from __future__ import annotations

import pandas as pd
import plotly.graph_objects as go

from .periodization import TRAINING_BLOCKS, RESIDUAL_EFFECTS, compute_residual_effects

ABILITY_COLORS = {
    "Maximal Strength": "rgb(31, 119, 180)",
    "Power": "rgb(255, 127, 14)",
    "Speed": "rgb(44, 160, 44)",
    "Hypertrophy": "rgb(214, 39, 40)",
}

BLOCK_COLORS = {
    "Strength": "rgb(31, 119, 180)",
    "Power": "rgb(255, 127, 14)",
    "Speed": "rgb(44, 160, 44)",
    "Hypertrophy": "rgb(214, 39, 40)",
    "Mini-Block": "rgba(180, 180, 180, 0.7)",
    "Peak": "rgb(255, 215, 0)",
}


# ---------------------------------------------------------------------------
# Program builder charts
# ---------------------------------------------------------------------------

def intensity_plot(blocks: list[str]) -> go.Figure:
    weeks, lo_vals, hi_vals = [], [], []
    current_week = 0
    for block in blocks:
        data = TRAINING_BLOCKS[block]
        for w in range(data["duration_weeks"]):
            weeks.append(current_week + w)
            lo_vals.append(data["intensity_range"][0])
            hi_vals.append(data["intensity_range"][1])
        current_week += data["duration_weeks"]

    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=weeks + weeks[::-1], y=hi_vals + lo_vals[::-1],
        fill="toself", fillcolor="rgba(0,100,80,0.2)",
        line=dict(color="rgba(255,255,255,0)"), showlegend=False, name="Intensity Range",
    ))
    fig.add_trace(go.Scatter(x=weeks, y=hi_vals, line=dict(color="rgb(0,100,80)"), name="Max Intensity"))
    fig.add_trace(go.Scatter(x=weeks, y=lo_vals, line=dict(color="rgb(0,100,80)", dash="dash"), name="Min Intensity"))
    fig.update_layout(title="Program Intensity Profile", xaxis_title="Week", yaxis_title="Intensity (%1RM)", hovermode="x unified")
    return fig


def residual_effects_plot(blocks: list[str], optimized: bool = False, initial_retention: dict[str, float] | None = None) -> go.Figure:
    timeline, effects, total_weeks = compute_residual_effects(blocks, optimized=optimized, initial_retention=initial_retention)

    fig = go.Figure()
    for ability in RESIDUAL_EFFECTS:
        fig.add_trace(go.Scatter(
            x=timeline, y=effects[ability], name=ability,
            line=dict(color=ABILITY_COLORS[ability]),
            hovertemplate="Week %{x}<br>" + f"{ability}: %{{y:.1f}}%<br><extra></extra>",
        ))

    current_week = 0
    for i, block in enumerate(blocks):
        duration = TRAINING_BLOCKS[block]["duration_weeks"]
        if initial_retention:
            fig.add_vrect(
                x0=current_week, x1=current_week + duration,
                fillcolor=BLOCK_COLORS[block], opacity=0.1, layer="below", line_width=0,
                annotation_text=block, annotation_position="top left",
            )
        elif i > 0:
            fig.add_vline(x=current_week, line_dash="dash", line_color="gray", opacity=0.5)
        current_week += duration

    fig.add_vrect(
        x0=total_weeks - 1, x1=total_weeks,
        fillcolor="rgba(255, 255, 0, 0.3)", layer="below", line_width=0,
        annotation_text="Peak Week", annotation_position="top left",
    )

    title = "Projected Residual Effects" if initial_retention else (
        "Optimized Residual Training Effects (with Mini-Blocks)" if optimized else "Residual Training Effects"
    )
    fig.update_layout(title=title, xaxis_title="Weeks", yaxis_title="Effect Retention (%)", hovermode="x unified", yaxis_range=[0, 110])
    return fig


def program_gantt(blocks: list[str]) -> go.Figure:
    tasks = []
    current_week = 0
    for i, block in enumerate(blocks):
        duration = TRAINING_BLOCKS[block]["duration_weeks"]
        tasks.append({"Task": f"{block} Block", "Start": current_week, "Duration": duration, "Color": BLOCK_COLORS[block], "Type": "Main"})
        if i > 0:
            prev = blocks[i - 1]
            for mw in range(current_week, current_week + duration, 2):
                tasks.append({"Task": f"{prev} Mini-Block", "Start": mw, "Duration": 1, "Color": BLOCK_COLORS["Mini-Block"], "Type": "Mini"})
        current_week += duration
    tasks.append({"Task": "Peak Week", "Start": current_week, "Duration": 1, "Color": BLOCK_COLORS["Peak"], "Type": "Peak"})

    fig = go.Figure()
    for t in tasks:
        fig.add_trace(go.Bar(
            name=t["Task"], x=[t["Duration"]], y=[t["Task"]], orientation="h",
            marker=dict(color=t["Color"]), base=t["Start"], showlegend=t["Type"] == "Main",
            hovertemplate="Block: %{y}<br>Start Week: %{base}<br>Duration: %{x} week(s)<br><extra></extra>",
        ))
    fig.update_layout(title="Training Program Timeline", xaxis_title="Weeks", yaxis=dict(title="", autorange="reversed"),
                      barmode="overlay", height=400, legend_title="Training Blocks", hovermode="closest")
    return fig


def schedule_heatmap(schedule_df: pd.DataFrame) -> go.Figure:
    intensity_map = {"High Intensity": 3, "Medium-High Intensity": 2, "Medium Intensity": 1, "High Volume": 2.5}
    vals = [[intensity_map[t] for t in schedule_df["Training"]]]
    fig = go.Figure(data=go.Heatmap(
        z=vals, x=schedule_df["Day"].tolist(), y=["Training"], colorscale="Viridis", showscale=False,
        text=[schedule_df["Training"].tolist()], texttemplate="%{text}", textfont={"size": 12, "color": "white"},
    ))
    fig.update_layout(title="Weekly Training Schedule Intensity", xaxis_title="Day of Week", yaxis_title="", height=200)
    return fig


# ---------------------------------------------------------------------------
# Analytics charts
# ---------------------------------------------------------------------------

def volume_over_time(df: pd.DataFrame) -> go.Figure:
    col = "year_week" if "year_week" in df.columns else "week_start"
    weekly = df.groupby(col)["volume"].sum().reset_index()
    fig = go.Figure(go.Bar(x=weekly[col], y=weekly["volume"], name="Volume", marker_color="rgb(31, 119, 180)"))
    fig.update_layout(title="Weekly Training Volume", xaxis_title="Week", yaxis_title="Volume (sets x reps x kg)", hovermode="x unified")
    return fig


def session_frequency(df: pd.DataFrame) -> go.Figure:
    daily = df.groupby(df["date"].dt.date).size().reset_index(name="count")
    daily["date"] = pd.to_datetime(daily["date"])
    weekday_order = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
    freq = daily["date"].dt.day_name().value_counts().reindex(weekday_order, fill_value=0)
    fig = go.Figure(go.Bar(x=freq.index, y=freq.values, marker_color="rgb(44, 160, 44)"))
    fig.update_layout(title="Training Frequency by Day of Week", xaxis_title="Day", yaxis_title="Sessions")
    return fig


def volume_by_muscle_group(df: pd.DataFrame) -> go.Figure:
    if "muscle_group" not in df.columns:
        return go.Figure()
    grouped = df.groupby("muscle_group")["volume"].sum().sort_values(ascending=True)
    fig = go.Figure(go.Bar(x=grouped.values, y=grouped.index, orientation="h", marker_color="rgb(214, 39, 40)"))
    fig.update_layout(title="Total Volume by Muscle Group", xaxis_title="Volume (sets x reps x kg)", yaxis_title="")
    return fig


def exercise_progression(df: pd.DataFrame, exercise: str) -> go.Figure:
    ex_df = df[df["exercise"] == exercise]
    daily = ex_df.groupby("date").agg(max_weight=("weight_kg", "max"), total_volume=("volume", "sum")).reset_index()

    fig = go.Figure()
    fig.add_trace(go.Scatter(x=daily["date"], y=daily["max_weight"], mode="lines+markers", name="Max Weight (kg)", line=dict(color="rgb(31, 119, 180)")))
    fig.add_trace(go.Bar(x=daily["date"], y=daily["total_volume"], name="Session Volume", marker_color="rgba(255, 127, 14, 0.4)", yaxis="y2"))
    fig.update_layout(
        title=f"{exercise} — Progression", xaxis_title="Date",
        yaxis=dict(title="Weight (kg)"), yaxis2=dict(title="Volume", overlaying="y", side="right"),
        hovermode="x unified", legend=dict(x=0, y=1.15, orientation="h"),
    )
    return fig


def e1rm_progression(df: pd.DataFrame, exercise: str) -> go.Figure:
    ex_df = df[(df["exercise"] == exercise) & (df["weight_kg"] > 0) & (df["reps"] > 0)].copy()
    ex_df["e1rm"] = ex_df["weight_kg"] * (1 + ex_df["reps"] / 30)
    daily = ex_df.groupby("date")["e1rm"].max().reset_index()

    fig = go.Figure(go.Scatter(x=daily["date"], y=daily["e1rm"], mode="lines+markers", name="Estimated 1RM", line=dict(color="rgb(148, 103, 189)", width=2)))
    fig.update_layout(title=f"{exercise} — Estimated 1RM (Epley)", xaxis_title="Date", yaxis_title="Estimated 1RM (kg)", hovermode="x unified")
    return fig


# ---------------------------------------------------------------------------
# Smart program charts
# ---------------------------------------------------------------------------

def training_history_chart(weekly: pd.DataFrame) -> go.Figure:
    fig = go.Figure()
    for bt in ["Strength", "Power", "Speed", "Hypertrophy"]:
        if bt in weekly.columns:
            fig.add_trace(go.Bar(x=weekly["week_start"], y=weekly[bt], name=bt, marker_color=BLOCK_COLORS[bt]))
    fig.update_layout(title="Training Volume by Block Type (Weekly)", xaxis_title="Week", yaxis_title="Volume", barmode="stack", hovermode="x unified")
    return fig


def current_residuals_chart(status: dict[str, dict]) -> go.Figure:
    abilities = list(status.keys())
    retentions = [status[a]["retention"] for a in abilities]
    fig = go.Figure(go.Bar(
        x=abilities, y=retentions, marker_color=[ABILITY_COLORS[a] for a in abilities],
        text=[f"{r:.0f}%" for r in retentions], textposition="outside",
    ))
    fig.update_layout(title="Current Residual Training Effects", yaxis_title="Retention (%)", yaxis_range=[0, 110], showlegend=False)
    return fig


def current_vs_peak_chart(current_status: dict[str, dict], projected: dict[str, list[float]], total_weeks: int) -> go.Figure:
    abilities = list(RESIDUAL_EFFECTS.keys())
    now = [current_status[a]["retention"] for a in abilities]
    peak_idx = total_weeks - 1
    at_peak = [projected[a][peak_idx] if peak_idx < len(projected[a]) else 0 for a in abilities]
    fig = go.Figure()
    fig.add_trace(go.Bar(name="Now", x=abilities, y=now, marker_color="rgba(100,100,100,0.5)"))
    fig.add_trace(go.Bar(name="At Peak", x=abilities, y=at_peak, marker_color="rgb(255, 215, 0)"))
    fig.update_layout(title="Current vs. Projected Peak Performance", yaxis_title="Retention (%)", yaxis_range=[0, 110], barmode="group")
    return fig
