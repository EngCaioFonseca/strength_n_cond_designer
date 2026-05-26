from __future__ import annotations

import pandas as pd

from .db import get_db
from .models import TrainingLog, TrainingProgram


def get_user_programs(user_id: int) -> list[TrainingProgram]:
    with get_db() as db:
        return (
            db.query(TrainingProgram)
            .filter(TrainingProgram.user_id == user_id)
            .order_by(TrainingProgram.created_at.desc())
            .all()
        )


def get_user_logs(user_id: int, limit: int | None = None) -> list[TrainingLog]:
    with get_db() as db:
        q = (
            db.query(TrainingLog)
            .filter(TrainingLog.user_id == user_id)
            .order_by(TrainingLog.date.desc())
        )
        if limit:
            q = q.limit(limit)
        return q.all()


def logs_to_dataframe(user_id: int) -> pd.DataFrame:
    logs = get_user_logs(user_id)
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
                "reps": ex.get("reps", 0) or 0,
                "weight_kg": ex.get("weight", 0) or 0,
                "rpe": ex.get("rpe"),
                "set_type": ex.get("set_type", "normal"),
                "duration_seconds": ex.get("duration_seconds"),
                "distance_km": ex.get("distance_km"),
            })

    df = pd.DataFrame(rows)
    df["date"] = pd.to_datetime(df["date"])
    df["volume"] = df["sets"] * df["reps"] * df["weight_kg"]
    return df
