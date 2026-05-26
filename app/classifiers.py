from __future__ import annotations

import pandas as pd

POWER_KEYWORDS = ["clean", "snatch", "jerk", "jump squat", "box jump", "med ball", "medicine ball", "plyo"]
SPEED_KEYWORDS = ["sprint", "dash", "agility", "band-resisted", "prowler"]

MUSCLE_GROUP_KEYWORDS: dict[str, list[str]] = {
    "Legs": ["squat", "leg press", "lunge", "leg ext"],
    "Chest": ["bench", "chest", "push up", "fly", "pec"],
    "Back": ["row", "pull", "lat", "back"],
    "Shoulders": ["shoulder", "press", "ohp", "lateral raise", "delt"],
    "Biceps": ["curl", "bicep"],
    "Triceps": ["tricep", "pushdown", "skull"],
    "Posterior Chain": ["deadlift", "rdl", "hip thrust", "glute"],
    "Olympic Lifts": ["clean", "snatch", "jerk"],
    "Cardio": ["run", "sprint", "cardio", "bike"],
    "Core": ["ab", "crunch", "plank", "core"],
}


def classify_block_type(exercise: str, reps: int, weight_kg: float, e1rm: float | None) -> str:
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
    if reps >= 6:
        return "Hypertrophy"

    return "Strength"


def classify_muscle_group(exercise: str) -> str:
    name = exercise.lower()
    for group, keywords in MUSCLE_GROUP_KEYWORDS.items():
        if any(k in name for k in keywords):
            return group
    return "Other"


def estimate_e1rm(weight_kg: float, reps: int) -> float:
    if weight_kg <= 0 or reps <= 0:
        return 0.0
    return weight_kg * (1 + reps / 30)


def add_classification_columns(df: pd.DataFrame) -> pd.DataFrame:
    if df.empty:
        return df

    df = df.copy()
    e1rm_lookup = {}
    for ex, grp in df[df["weight_kg"] > 0].groupby("exercise"):
        best = grp.loc[grp["weight_kg"].idxmax()]
        e1rm_lookup[ex] = estimate_e1rm(best["weight_kg"], max(best["reps"], 1))

    df["e1rm"] = df["exercise"].map(e1rm_lookup)
    df["block_type_classified"] = df.apply(
        lambda r: classify_block_type(r["exercise"], r["reps"], r["weight_kg"], r.get("e1rm")),
        axis=1,
    )
    df["muscle_group"] = df["exercise"].apply(classify_muscle_group)
    df["week_start"] = df["date"].dt.to_period("W").apply(lambda p: p.start_time)
    return df
