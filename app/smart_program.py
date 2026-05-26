from __future__ import annotations

from datetime import datetime, timedelta, timezone
from itertools import permutations

import pandas as pd
import plotly.graph_objects as go
import streamlit as st

from .db import get_db
from .models import TrainingLog
from .training import (
    TRAINING_BLOCKS,
    RESIDUAL_EFFECTS,
    BLOCK_TO_ABILITY,
    MINI_BLOCK_EFFECT,
)

# ---------------------------------------------------------------------------
# 1. Load & classify historical training
# ---------------------------------------------------------------------------

POWER_KEYWORDS = ["clean", "snatch", "jerk", "jump squat", "box jump", "med ball", "medicine ball", "plyo"]
SPEED_KEYWORDS = ["sprint", "dash", "agility", "band-resisted", "prowler"]


def _classify_set(exercise: str, reps: int, weight_kg: float, e1rm: float | None) -> str:
    name = exercise.lower()

    if any(k in name for k in SPEED_KEYWORDS):
        return "Speed"
    if any(k in name for k in POWER_KEYWORDS):
        return "Power"

    if e1rm and e1rm > 0 and weight_kg > 0:
        intensity_pct = (weight_kg / e1rm) * 100
        if intensity_pct >= 80 and reps <= 5:
            return "Strength"
        if 60 <= intensity_pct < 80 and reps <= 5:
            return "Power"
        if intensity_pct >= 85:
            return "Speed"

    if reps <= 5 and weight_kg > 0:
        return "Strength"
    if 6 <= reps <= 12:
        return "Hypertrophy"
    if reps > 12:
        return "Hypertrophy"

    return "Strength"


def load_and_classify(user_id: int) -> pd.DataFrame:
    with get_db() as db:
        logs = (
            db.query(TrainingLog)
            .filter(TrainingLog.user_id == user_id)
            .order_by(TrainingLog.date.asc())
            .all()
        )
    if not logs:
        return pd.DataFrame()

    rows = []
    for log in logs:
        for ex in (log.exercises or []):
            reps = ex.get("reps", 0) or 0
            weight = ex.get("weight", 0) or 0
            rows.append({
                "date": log.date,
                "exercise": ex.get("name", "Unknown"),
                "reps": reps,
                "weight_kg": weight,
                "sets": ex.get("sets", 1),
                "rpe": ex.get("rpe"),
            })

    df = pd.DataFrame(rows)
    if df.empty:
        return df

    df["date"] = pd.to_datetime(df["date"])
    df["volume"] = df["sets"] * df["reps"] * df["weight_kg"]

    e1rm_lookup = {}
    for ex, grp in df[df["weight_kg"] > 0].groupby("exercise"):
        best = grp.loc[grp["weight_kg"].idxmax()]
        reps = max(best["reps"], 1)
        e1rm_lookup[ex] = best["weight_kg"] * (1 + reps / 30)

    df["e1rm"] = df["exercise"].map(e1rm_lookup)
    df["block_type"] = df.apply(
        lambda r: _classify_set(r["exercise"], r["reps"], r["weight_kg"], r.get("e1rm")), axis=1
    )
    df["week_start"] = df["date"].dt.to_period("W").apply(lambda p: p.start_time)
    return df


def weekly_block_profile(df: pd.DataFrame) -> pd.DataFrame:
    if df.empty:
        return pd.DataFrame()
    weekly = df.groupby(["week_start", "block_type"])["volume"].sum().unstack(fill_value=0)
    for bt in ["Strength", "Power", "Speed", "Hypertrophy"]:
        if bt not in weekly.columns:
            weekly[bt] = 0
    weekly["dominant"] = weekly[["Strength", "Power", "Speed", "Hypertrophy"]].idxmax(axis=1)
    weekly = weekly.reset_index().sort_values("week_start")
    return weekly


# ---------------------------------------------------------------------------
# 2. Current residual effects from real data
# ---------------------------------------------------------------------------

def current_residual_status(df: pd.DataFrame) -> dict[str, dict]:
    today = datetime.now(timezone.utc)
    status = {}
    weekly = weekly_block_profile(df)
    if weekly.empty:
        for ability in RESIDUAL_EFFECTS:
            status[ability] = {"retention": 0.0, "days_since": None, "last_trained": None}
        return status

    for block_type, ability in BLOCK_TO_ABILITY.items():
        block_weeks = weekly[weekly["dominant"] == block_type]
        if block_weeks.empty:
            status[ability] = {"retention": 0.0, "days_since": None, "last_trained": None}
            continue
        last_week = pd.Timestamp(block_weeks["week_start"].max())
        days_since = (today - last_week.to_pydatetime().replace(tzinfo=timezone.utc)).days
        residual_days = RESIDUAL_EFFECTS[ability]
        retention = max(0.0, 100 * (1 - days_since / residual_days)) if days_since < residual_days else 0.0
        status[ability] = {
            "retention": round(retention, 1),
            "days_since": days_since,
            "last_trained": last_week.strftime("%Y-%m-%d"),
        }
    return status


# ---------------------------------------------------------------------------
# 3. Recommend optimal block sequence
# ---------------------------------------------------------------------------

GOAL_PRIORITIES = {
    "Strength Peak": ["Hypertrophy", "Strength", "Power", "Speed"],
    "Power Peak": ["Hypertrophy", "Strength", "Power", "Speed"],
    "Speed Peak": ["Hypertrophy", "Strength", "Power", "Speed"],
    "Hypertrophy Focus": ["Strength", "Power", "Hypertrophy"],
    "General Fitness": ["Hypertrophy", "Strength", "Power"],
    "Competition Prep": ["Hypertrophy", "Strength", "Power", "Speed"],
}


def _score_sequence(blocks: list[str], goal: str, weeks_available: int) -> float:
    total_weeks = sum(TRAINING_BLOCKS[b]["duration_weeks"] for b in blocks)
    if total_weeks > weeks_available:
        return -1.0

    priority = GOAL_PRIORITIES[goal]
    target_ability = BLOCK_TO_ABILITY[priority[-1]]

    score = 0.0
    current_week = 0
    for block_idx, block in enumerate(blocks):
        block_duration = TRAINING_BLOCKS[block]["duration_weeks"]
        block_end = current_week + block_duration
        ability = BLOCK_TO_ABILITY[block]

        if ability == target_ability:
            recency_bonus = (current_week + 1) / total_weeks
            score += 30 * recency_bonus

        for prev_idx in range(block_idx):
            prev_ability = BLOCK_TO_ABILITY[blocks[prev_idx]]
            prev_end = sum(TRAINING_BLOCKS[blocks[j]]["duration_weeks"] for j in range(prev_idx + 1))
            days_gap = (current_week - prev_end) * 7
            residual = RESIDUAL_EFFECTS[prev_ability]
            if days_gap < residual:
                retention = 100 * (1 - days_gap / residual)
                score += retention * 0.2

        current_week = block_end

    final_week = total_weeks
    for ability_name, residual_days in RESIDUAL_EFFECTS.items():
        block_for_ability = [b for b, a in BLOCK_TO_ABILITY.items() if a == ability_name]
        if not block_for_ability:
            continue
        bt = block_for_ability[0]
        if bt in blocks:
            last_idx = len(blocks) - 1 - blocks[::-1].index(bt)
            end_of_block = sum(TRAINING_BLOCKS[blocks[j]]["duration_weeks"] for j in range(last_idx + 1))
            days_to_end = (final_week - end_of_block) * 7
            if days_to_end < residual_days:
                retention = 100 * (1 - days_to_end / residual_days)
                weight = 2.0 if ability_name == target_ability else 0.5
                score += retention * weight

    return score


def recommend_program(goal: str, weeks_available: int) -> list[str]:
    priority = GOAL_PRIORITIES[goal]

    best_seq = None
    best_score = -1.0

    for length in range(len(priority), 0, -1):
        for perm in permutations(priority[:length]):
            seq = list(perm)
            total = sum(TRAINING_BLOCKS[b]["duration_weeks"] for b in seq)
            if total > weeks_available:
                continue
            s = _score_sequence(seq, goal, weeks_available)
            if s > best_score:
                best_score = s
                best_seq = seq

    return best_seq or [priority[-1]]


# ---------------------------------------------------------------------------
# 4. Project future residual effects
# ---------------------------------------------------------------------------

def project_future_effects(blocks: list[str], current_status: dict[str, dict]) -> tuple[list[int], dict[str, list[float]], int]:
    total_weeks = sum(TRAINING_BLOCKS[b]["duration_weeks"] for b in blocks) + 1
    max_residual_weeks = max(RESIDUAL_EFFECTS.values()) // 7
    timeline = list(range(total_weeks + max_residual_weeks))
    effects = {ability: [] for ability in RESIDUAL_EFFECTS}

    for week in timeline:
        week_effects = {}
        for ability in RESIDUAL_EFFECTS:
            if week == 0 and current_status.get(ability):
                week_effects[ability] = current_status[ability]["retention"]
            else:
                week_effects[ability] = 0.0

        current_pos = 0
        for block_idx, block in enumerate(blocks):
            duration = TRAINING_BLOCKS[block]["duration_weeks"]
            block_end = current_pos + duration
            ability = BLOCK_TO_ABILITY[block]

            if week >= current_pos:
                days_since = (week - block_end) * 7

                if week < block_end:
                    week_effects[ability] = 100.0
                    if block_idx > 0:
                        for prev_block in blocks[:block_idx]:
                            prev_ability = BLOCK_TO_ABILITY[prev_block]
                            mini_effect = MINI_BLOCK_EFFECT[prev_ability] * 100
                            week_effects[prev_ability] = max(week_effects[prev_ability], mini_effect)

                elif days_since < RESIDUAL_EFFECTS[ability]:
                    base = 100 * (1 - days_since / RESIDUAL_EFFECTS[ability])
                    if block_idx < len(blocks) - 1:
                        base += base * MINI_BLOCK_EFFECT[ability]
                    week_effects[ability] = max(base, week_effects[ability])

            current_pos += duration

        if week == total_weeks - 1:
            for ability in RESIDUAL_EFFECTS:
                week_effects[ability] = 100.0

        for ability in RESIDUAL_EFFECTS:
            effects[ability].append(max(week_effects[ability], 0.0))

    return timeline, effects, total_weeks


# ---------------------------------------------------------------------------
# 5. Visualizations
# ---------------------------------------------------------------------------

ABILITY_COLORS = {
    "Maximal Strength": "rgb(31, 119, 180)",
    "Power": "rgb(255, 127, 14)",
    "Speed": "rgb(44, 160, 44)",
    "Hypertrophy": "rgb(214, 39, 40)",
}

BLOCK_TYPE_COLORS = {
    "Strength": "rgb(31, 119, 180)",
    "Power": "rgb(255, 127, 14)",
    "Speed": "rgb(44, 160, 44)",
    "Hypertrophy": "rgb(214, 39, 40)",
}


def plot_training_history(weekly: pd.DataFrame) -> go.Figure:
    fig = go.Figure()
    for bt in ["Strength", "Power", "Speed", "Hypertrophy"]:
        if bt in weekly.columns:
            fig.add_trace(go.Bar(
                x=weekly["week_start"], y=weekly[bt],
                name=bt, marker_color=BLOCK_TYPE_COLORS[bt],
            ))
    fig.update_layout(
        title="Training Volume by Block Type (Weekly)",
        xaxis_title="Week", yaxis_title="Volume (sets x reps x kg)",
        barmode="stack", hovermode="x unified",
    )
    return fig


def plot_current_residuals(status: dict[str, dict]) -> go.Figure:
    abilities = list(status.keys())
    retentions = [status[a]["retention"] for a in abilities]
    colors = [ABILITY_COLORS[a] for a in abilities]

    fig = go.Figure(go.Bar(
        x=abilities, y=retentions,
        marker_color=colors,
        text=[f"{r:.0f}%" for r in retentions],
        textposition="outside",
    ))
    fig.update_layout(
        title="Current Residual Training Effects",
        yaxis_title="Retention (%)", yaxis_range=[0, 110],
        showlegend=False,
    )
    return fig


def plot_projected_effects(timeline: list[int], effects: dict[str, list[float]], total_weeks: int, blocks: list[str]) -> go.Figure:
    fig = go.Figure()
    for ability in RESIDUAL_EFFECTS:
        fig.add_trace(go.Scatter(
            x=timeline, y=effects[ability],
            name=ability, line=dict(color=ABILITY_COLORS[ability]),
            hovertemplate="Week %{x}<br>" + f"{ability}: %{{y:.1f}}%<br><extra></extra>",
        ))

    current_week = 0
    for i, block in enumerate(blocks):
        duration = TRAINING_BLOCKS[block]["duration_weeks"]
        fig.add_vrect(
            x0=current_week, x1=current_week + duration,
            fillcolor=BLOCK_TYPE_COLORS[block], opacity=0.1,
            layer="below", line_width=0,
            annotation_text=block, annotation_position="top left",
        )
        current_week += duration

    fig.add_vrect(
        x0=total_weeks - 1, x1=total_weeks,
        fillcolor="rgba(255, 255, 0, 0.3)", layer="below", line_width=0,
        annotation_text="Peak Week", annotation_position="top left",
    )
    fig.update_layout(
        title="Projected Residual Effects — Recommended Program",
        xaxis_title="Weeks from Now", yaxis_title="Effect Retention (%)",
        hovermode="x unified", yaxis_range=[0, 110], showlegend=True,
    )
    return fig


def plot_comparison(
    current_status: dict[str, dict],
    projected_effects: dict[str, list[float]],
    total_weeks: int,
) -> go.Figure:
    abilities = list(RESIDUAL_EFFECTS.keys())
    now = [current_status[a]["retention"] for a in abilities]
    at_peak = [projected_effects[a][total_weeks - 1] if total_weeks - 1 < len(projected_effects[a]) else 0 for a in abilities]

    fig = go.Figure()
    fig.add_trace(go.Bar(name="Now", x=abilities, y=now, marker_color="rgba(100,100,100,0.5)"))
    fig.add_trace(go.Bar(name="At Peak", x=abilities, y=at_peak, marker_color="rgb(255, 215, 0)"))
    fig.update_layout(
        title="Current vs. Projected Peak Performance",
        yaxis_title="Retention (%)", yaxis_range=[0, 110],
        barmode="group",
    )
    return fig


# ---------------------------------------------------------------------------
# 6. Streamlit page
# ---------------------------------------------------------------------------

def render_smart_program_page():
    st.title("Smart Program Recommendation")
    st.markdown(
        "Analyzes your training history, shows where your residual effects stand today, "
        "and recommends an optimal block sequence to reach your goal."
    )

    df = load_and_classify(st.session_state.user_id)
    if df.empty:
        st.warning("No training data found. Import from Hevy or log sessions first.")
        return

    # --- Section 1: Training history ---
    st.markdown("---")
    st.header("1. Your Training History")
    weekly = weekly_block_profile(df)

    col1, col2, col3 = st.columns(3)
    col1.metric("Weeks of Data", len(weekly))
    col2.metric("Total Sessions", df["date"].nunique())
    col3.metric("Exercises Tracked", df["exercise"].nunique())

    st.plotly_chart(plot_training_history(weekly), use_container_width=True)

    recent = weekly.tail(4)
    if not recent.empty:
        dominant_counts = recent["dominant"].value_counts()
        st.markdown(f"**Recent focus (last 4 weeks):** {dominant_counts.index[0]} "
                    f"({dominant_counts.iloc[0]} of {len(recent)} weeks)")

    # --- Section 2: Current residual effects ---
    st.markdown("---")
    st.header("2. Current Residual Effects")
    status = current_residual_status(df)
    st.plotly_chart(plot_current_residuals(status), use_container_width=True)

    cols = st.columns(4)
    for i, (ability, info) in enumerate(status.items()):
        with cols[i]:
            if info["days_since"] is not None:
                st.caption(f"**{ability}**")
                st.write(f"{info['retention']:.0f}% retained")
                st.write(f"{info['days_since']}d since last block")
            else:
                st.caption(f"**{ability}**")
                st.write("No data")

    # --- Section 3: Goal & recommendation ---
    st.markdown("---")
    st.header("3. Your Goal")

    col_goal, col_weeks = st.columns(2)
    with col_goal:
        goal = st.selectbox("What are you training for?", list(GOAL_PRIORITIES.keys()))
    with col_weeks:
        weeks_available = st.slider("Weeks available", 4, 24, 12)

    recommended = recommend_program(goal, weeks_available)
    total_duration = sum(TRAINING_BLOCKS[b]["duration_weeks"] for b in recommended)

    st.subheader("Recommended Block Sequence")
    block_cols = st.columns(len(recommended) + 1)
    for i, block in enumerate(recommended):
        with block_cols[i]:
            dur = TRAINING_BLOCKS[block]["duration_weeks"]
            lo, hi = TRAINING_BLOCKS[block]["intensity_range"]
            st.markdown(f"**Block {i+1}: {block}**")
            st.write(f"{dur} weeks @ {lo}-{hi}% 1RM")
    with block_cols[-1]:
        st.markdown("**Peak Week**")
        st.write("1 week — all qualities")

    st.write(f"**Total program duration:** {total_duration + 1} weeks (including peak)")

    # --- Section 4: Projected effects ---
    st.markdown("---")
    st.header("4. Projected Training Effects")
    timeline, effects, tw = project_future_effects(recommended, status)
    st.plotly_chart(plot_projected_effects(timeline, effects, tw, recommended), use_container_width=True)

    # --- Section 5: Before vs after ---
    st.markdown("---")
    st.header("5. Current vs. Peak Comparison")
    st.plotly_chart(plot_comparison(status, effects, tw), use_container_width=True)

    # --- Section 6: Implementation notes ---
    st.markdown("---")
    st.header("6. Implementation Guidelines")
    for i, block in enumerate(recommended):
        ability = BLOCK_TO_ABILITY[block]
        residual = RESIDUAL_EFFECTS[ability]
        st.markdown(f"**Block {i+1}: {block}** ({TRAINING_BLOCKS[block]['duration_weeks']} weeks)")
        st.write(f"- Intensity zone: {TRAINING_BLOCKS[block]['intensity_range'][0]}-{TRAINING_BLOCKS[block]['intensity_range'][1]}% 1RM")
        st.write(f"- Residual effect lasts {residual} days after block ends")
        if i > 0:
            prev = recommended[i-1]
            prev_ability = BLOCK_TO_ABILITY[prev]
            maint = MINI_BLOCK_EFFECT[prev_ability] * 100
            st.write(f"- Include {prev} mini-blocks (1-2 sessions/week) to maintain {maint:.0f}% of {prev_ability}")
        st.write("")

    st.markdown(
        "**Peak Week:** Reduce volume by 40-60%, maintain intensity. "
        "Integrate all training qualities at competition-level specificity."
    )
