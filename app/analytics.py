from __future__ import annotations

import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
import streamlit as st

from .db import get_db
from .models import TrainingLog


def _load_user_logs(user_id: int) -> pd.DataFrame:
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
            rows.append({
                "date": log.date,
                "block_type": log.block_type,
                "exercise": ex.get("name", "Unknown"),
                "sets": ex.get("sets", 1),
                "reps": ex.get("reps", 0),
                "weight_kg": ex.get("weight", 0),
                "rpe": ex.get("rpe"),
                "set_type": ex.get("set_type", "normal"),
                "duration_seconds": ex.get("duration_seconds"),
                "distance_km": ex.get("distance_km"),
            })
    df = pd.DataFrame(rows)
    df["date"] = pd.to_datetime(df["date"])
    df["volume"] = df["sets"] * df["reps"] * df["weight_kg"]
    df["week"] = df["date"].dt.isocalendar().week.astype(int)
    df["year_week"] = df["date"].dt.strftime("%Y-W%U")
    return df


def _volume_over_time(df: pd.DataFrame) -> go.Figure:
    weekly = df.groupby("year_week", sort=True).agg(
        total_volume=("volume", "sum"),
        total_sets=("sets", "sum"),
        sessions=("date", "nunique"),
    ).reset_index()

    fig = go.Figure()
    fig.add_trace(go.Bar(
        x=weekly["year_week"], y=weekly["total_volume"],
        name="Total Volume (kg)",
        marker_color="rgb(31, 119, 180)",
    ))
    fig.update_layout(
        title="Weekly Training Volume",
        xaxis_title="Week",
        yaxis_title="Volume (sets x reps x kg)",
        hovermode="x unified",
    )
    return fig


def _exercise_progression(df: pd.DataFrame, exercise: str) -> go.Figure:
    ex_df = df[df["exercise"] == exercise].copy()
    daily_max = ex_df.groupby("date").agg(
        max_weight=("weight_kg", "max"),
        max_reps=("reps", "max"),
        total_volume=("volume", "sum"),
    ).reset_index()

    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=daily_max["date"], y=daily_max["max_weight"],
        mode="lines+markers",
        name="Max Weight (kg)",
        line=dict(color="rgb(31, 119, 180)"),
    ))
    fig.add_trace(go.Bar(
        x=daily_max["date"], y=daily_max["total_volume"],
        name="Session Volume",
        marker_color="rgba(255, 127, 14, 0.4)",
        yaxis="y2",
    ))
    fig.update_layout(
        title=f"{exercise} — Progression",
        xaxis_title="Date",
        yaxis=dict(title="Weight (kg)"),
        yaxis2=dict(title="Volume", overlaying="y", side="right"),
        hovermode="x unified",
        legend=dict(x=0, y=1.15, orientation="h"),
    )
    return fig


def _session_frequency(df: pd.DataFrame) -> go.Figure:
    daily = df.groupby(df["date"].dt.date).size().reset_index(name="exercises")
    daily.columns = ["date", "exercises"]
    daily["date"] = pd.to_datetime(daily["date"])
    daily["weekday"] = daily["date"].dt.day_name()

    weekday_order = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
    freq = daily["weekday"].value_counts().reindex(weekday_order, fill_value=0)

    fig = go.Figure(go.Bar(
        x=freq.index, y=freq.values,
        marker_color="rgb(44, 160, 44)",
    ))
    fig.update_layout(
        title="Training Frequency by Day of Week",
        xaxis_title="Day",
        yaxis_title="Number of Sessions",
    )
    return fig


def _muscle_group_estimate(exercise_name: str) -> str:
    name = exercise_name.lower()
    if any(k in name for k in ["squat", "leg press", "lunge", "leg ext"]):
        return "Legs"
    if any(k in name for k in ["bench", "chest", "push up", "fly", "pec"]):
        return "Chest"
    if any(k in name for k in ["row", "pull", "lat", "back"]):
        return "Back"
    if any(k in name for k in ["shoulder", "press", "ohp", "lateral raise", "delt"]):
        return "Shoulders"
    if any(k in name for k in ["curl", "bicep"]):
        return "Biceps"
    if any(k in name for k in ["tricep", "pushdown", "skull"]):
        return "Triceps"
    if any(k in name for k in ["deadlift", "rdl", "hip thrust", "glute"]):
        return "Posterior Chain"
    if any(k in name for k in ["clean", "snatch", "jerk"]):
        return "Olympic Lifts"
    if any(k in name for k in ["run", "sprint", "cardio", "bike", "row"]):
        return "Cardio"
    if any(k in name for k in ["ab", "crunch", "plank", "core"]):
        return "Core"
    return "Other"


def _volume_by_muscle_group(df: pd.DataFrame) -> go.Figure:
    df = df.copy()
    df["muscle_group"] = df["exercise"].apply(_muscle_group_estimate)
    grouped = df.groupby("muscle_group")["volume"].sum().sort_values(ascending=True)

    fig = go.Figure(go.Bar(
        x=grouped.values, y=grouped.index,
        orientation="h",
        marker_color="rgb(214, 39, 40)",
    ))
    fig.update_layout(
        title="Total Volume by Muscle Group",
        xaxis_title="Volume (sets x reps x kg)",
        yaxis_title="",
    )
    return fig


def _estimated_1rm_progression(df: pd.DataFrame, exercise: str) -> go.Figure:
    ex_df = df[(df["exercise"] == exercise) & (df["weight_kg"] > 0) & (df["reps"] > 0)].copy()
    # Epley formula
    ex_df["e1rm"] = ex_df["weight_kg"] * (1 + ex_df["reps"] / 30)
    daily_e1rm = ex_df.groupby("date")["e1rm"].max().reset_index()

    fig = go.Figure(go.Scatter(
        x=daily_e1rm["date"], y=daily_e1rm["e1rm"],
        mode="lines+markers",
        name="Estimated 1RM",
        line=dict(color="rgb(148, 103, 189)", width=2),
    ))
    fig.update_layout(
        title=f"{exercise} — Estimated 1RM (Epley)",
        xaxis_title="Date",
        yaxis_title="Estimated 1RM (kg)",
        hovermode="x unified",
    )
    return fig


def render_analytics_page():
    st.title("Training Analytics")

    df = _load_user_logs(st.session_state.user_id)
    if df.empty:
        st.info("No training data yet. Log sessions or import from Hevy to see analytics.")
        return

    # Summary metrics
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Total Sessions", df["date"].nunique())
    col2.metric("Total Exercises", df["exercise"].nunique())
    col3.metric("Total Volume (kg)", f"{df['volume'].sum():,.0f}")
    date_range = (df["date"].max() - df["date"].min()).days
    col4.metric("Date Range", f"{date_range} days")

    # Filters
    st.sidebar.markdown("---")
    st.sidebar.subheader("Analytics Filters")
    date_min = df["date"].min().date()
    date_max = df["date"].max().date()
    date_range_filter = st.sidebar.date_input(
        "Date range", value=(date_min, date_max), min_value=date_min, max_value=date_max,
    )
    if len(date_range_filter) == 2:
        start, end = date_range_filter
        df = df[(df["date"].dt.date >= start) & (df["date"].dt.date <= end)]

    # Volume over time
    st.markdown("---")
    st.header("1. Weekly Volume")
    st.plotly_chart(_volume_over_time(df), use_container_width=True)

    # Frequency
    st.markdown("---")
    st.header("2. Training Frequency")
    st.plotly_chart(_session_frequency(df), use_container_width=True)

    # Volume by muscle group
    st.markdown("---")
    st.header("3. Volume by Muscle Group")
    st.plotly_chart(_volume_by_muscle_group(df), use_container_width=True)

    # Per-exercise progression
    st.markdown("---")
    st.header("4. Exercise Progression")
    exercises = sorted(df["exercise"].unique())
    selected = st.selectbox("Select exercise", exercises)
    if selected:
        st.plotly_chart(_exercise_progression(df, selected), use_container_width=True)
        st.plotly_chart(_estimated_1rm_progression(df, selected), use_container_width=True)
