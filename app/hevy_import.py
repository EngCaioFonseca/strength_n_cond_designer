from __future__ import annotations

import io
from datetime import datetime

import pandas as pd
import streamlit as st

from .db import get_db
from .models import TrainingLog, TrainingProgram

HEVY_COLUMNS = [
    "title", "start_time", "end_time", "description",
    "exercise_title", "superset_id", "exercise_notes",
    "set_index", "set_type", "weight_lbs", "reps",
    "distance_miles", "duration_seconds", "rpe",
]

LBS_TO_KG = 0.453592
MILES_TO_KM = 1.60934


def parse_hevy_csv(file) -> pd.DataFrame:
    df = pd.read_csv(file, encoding="utf-8")
    df.columns = df.columns.str.strip().str.lower()

    missing = [c for c in ["exercise_title", "start_time"] if c not in df.columns]
    if missing:
        raise ValueError(f"Missing required columns: {missing}")

    if "weight_lbs" in df.columns:
        df["weight_kg"] = pd.to_numeric(df["weight_lbs"], errors="coerce") * LBS_TO_KG
    elif "weight_kg" not in df.columns:
        df["weight_kg"] = 0.0

    if "distance_miles" in df.columns:
        df["distance_km"] = pd.to_numeric(df["distance_miles"], errors="coerce") * MILES_TO_KM
    elif "distance_km" not in df.columns:
        df["distance_km"] = 0.0

    df["reps"] = pd.to_numeric(df.get("reps"), errors="coerce").fillna(0).astype(int)
    df["set_index"] = pd.to_numeric(df.get("set_index"), errors="coerce").fillna(1).astype(int)
    df["rpe"] = pd.to_numeric(df.get("rpe"), errors="coerce")
    df["duration_seconds"] = pd.to_numeric(df.get("duration_seconds"), errors="coerce").fillna(0)

    for col in ["start_time", "end_time"]:
        if col in df.columns:
            df[col] = pd.to_datetime(df[col], errors="coerce")

    df["title"] = df.get("title", "Workout").fillna("Workout")
    df["exercise_title"] = df["exercise_title"].fillna("Unknown Exercise")
    df["set_type"] = df.get("set_type", "normal").fillna("normal")

    return df


def group_workouts(df: pd.DataFrame) -> list[dict]:
    workouts = []
    for (title, start), group in df.groupby(["title", "start_time"], sort=False):
        exercises = []
        for ex_title, ex_group in group.groupby("exercise_title", sort=False):
            sets = []
            for _, row in ex_group.iterrows():
                s = {
                    "set_index": int(row["set_index"]),
                    "set_type": row.get("set_type", "normal"),
                    "weight_kg": round(row.get("weight_kg", 0) or 0, 1),
                    "reps": int(row.get("reps", 0) or 0),
                }
                if pd.notna(row.get("rpe")):
                    s["rpe"] = float(row["rpe"])
                if row.get("duration_seconds", 0) > 0:
                    s["duration_seconds"] = float(row["duration_seconds"])
                if row.get("distance_km", 0) > 0:
                    s["distance_km"] = round(float(row["distance_km"]), 2)
                sets.append(s)

            exercises.append({
                "name": ex_title,
                "notes": ex_group["exercise_notes"].dropna().iloc[0] if "exercise_notes" in ex_group and ex_group["exercise_notes"].notna().any() else "",
                "sets": sets,
            })

        workout = {
            "title": title if pd.notna(title) else "Workout",
            "start_time": start,
            "end_time": group["end_time"].iloc[0] if "end_time" in group and pd.notna(group["end_time"].iloc[0]) else None,
            "description": group["description"].dropna().iloc[0] if "description" in group and group["description"].notna().any() else "",
            "exercises": exercises,
        }
        workouts.append(workout)

    return workouts


def save_workouts_to_db(user_id: int, workouts: list[dict], program_id: int | None = None) -> int:
    count = 0
    with get_db() as db:
        for w in workouts:
            exercises_json = []
            for ex in w["exercises"]:
                for s in ex["sets"]:
                    exercises_json.append({
                        "name": ex["name"],
                        "sets": 1,
                        "reps": s["reps"],
                        "weight": s["weight_kg"],
                        "rpe": s.get("rpe"),
                        "set_type": s.get("set_type", "normal"),
                        "duration_seconds": s.get("duration_seconds"),
                        "distance_km": s.get("distance_km"),
                    })

            log = TrainingLog(
                user_id=user_id,
                program_id=program_id,
                date=w["start_time"],
                block_type=None,
                exercises=exercises_json,
                notes=w.get("description", ""),
            )
            db.add(log)
            count += 1
    return count


def render_import_page():
    st.title("Import from Hevy")
    st.markdown(
        "Export your data from Hevy: **Profile > Settings > Export Data**. "
        "Upload the workout CSV file below."
    )

    with get_db() as db:
        programs = (
            db.query(TrainingProgram)
            .filter(TrainingProgram.user_id == st.session_state.user_id)
            .all()
        )
    program_options = {"None (standalone)": None}
    program_options.update({p.name: p.id for p in programs})

    uploaded = st.file_uploader("Upload Hevy CSV", type=["csv"])
    target_program = st.selectbox("Link to program (optional)", list(program_options.keys()))

    if uploaded is not None:
        try:
            df = parse_hevy_csv(uploaded)
        except Exception as e:
            st.error(f"Failed to parse CSV: {e}")
            return

        workouts = group_workouts(df)
        st.success(f"Parsed **{len(workouts)} workouts** with **{len(df)} total sets**.")

        # Preview
        st.subheader("Preview")
        for w in workouts[:5]:
            with st.expander(f"{w['title']} — {w['start_time'].strftime('%Y-%m-%d %H:%M') if pd.notna(w['start_time']) else 'unknown date'}"):
                for ex in w["exercises"]:
                    sets_str = ", ".join(
                        f"{s['reps']}r @ {s['weight_kg']}kg" + (f" RPE {s['rpe']}" if s.get('rpe') else "")
                        for s in ex["sets"]
                    )
                    st.write(f"**{ex['name']}**: {sets_str}")
        if len(workouts) > 5:
            st.caption(f"...and {len(workouts) - 5} more workouts.")

        if st.button("Import All"):
            program_id = program_options[target_program]
            count = save_workouts_to_db(st.session_state.user_id, workouts, program_id)
            st.success(f"Imported {count} workouts to your training log!")
            st.rerun()
