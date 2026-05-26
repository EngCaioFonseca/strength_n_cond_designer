from __future__ import annotations

import pandas as pd
from sqlalchemy.orm import joinedload

from .db import get_db
from .models import TrainingLog, TrainingProgram


def get_user_programs(user_id: int) -> list[dict]:
    with get_db() as db:
        programs = (
            db.query(TrainingProgram)
            .filter(TrainingProgram.user_id == user_id)
            .order_by(TrainingProgram.created_at.desc())
            .all()
        )
        return [
            {
                "id": p.id,
                "name": p.name,
                "blocks": p.blocks,
                "training_days": p.training_days,
                "created_at": p.created_at,
            }
            for p in programs
        ]


def get_user_logs_raw(user_id: int, limit: int | None = None) -> list[dict]:
    with get_db() as db:
        q = (
            db.query(TrainingLog)
            .filter(TrainingLog.user_id == user_id)
            .order_by(TrainingLog.date.desc())
        )
        if limit:
            q = q.limit(limit)
        logs = q.all()
        return [
            {
                "id": log.id,
                "date": log.date,
                "block_type": log.block_type,
                "exercises": log.exercises or [],
                "notes": log.notes,
            }
            for log in logs
        ]


def logs_to_dataframe(user_id: int) -> pd.DataFrame:
    logs = get_user_logs_raw(user_id)
    if not logs:
        return pd.DataFrame()

    rows = []
    for log in logs:
        for ex in log["exercises"]:
            rows.append({
                "date": log["date"],
                "block_type": log["block_type"],
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
