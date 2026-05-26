from __future__ import annotations

import pandas as pd

from .db import get_db
from .models import TrainingLog

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
            notes_col = ex_group.get("exercise_notes")
            exercises.append({
                "name": ex_title,
                "notes": notes_col.dropna().iloc[0] if notes_col is not None and notes_col.notna().any() else "",
                "sets": sets,
            })

        desc_col = group.get("description")
        workouts.append({
            "title": title if pd.notna(title) else "Workout",
            "start_time": start,
            "end_time": group["end_time"].iloc[0] if "end_time" in group and pd.notna(group["end_time"].iloc[0]) else None,
            "description": desc_col.dropna().iloc[0] if desc_col is not None and desc_col.notna().any() else "",
            "exercises": exercises,
        })
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
            db.add(TrainingLog(
                user_id=user_id, program_id=program_id, date=w["start_time"],
                block_type=None, exercises=exercises_json, notes=w.get("description", ""),
            ))
            count += 1
    return count
