from __future__ import annotations

from datetime import datetime, timezone
from itertools import permutations

import pandas as pd

TRAINING_BLOCKS = {
    "Strength": {"duration_weeks": 4, "intensity_range": (75, 90)},
    "Power": {"duration_weeks": 3, "intensity_range": (60, 80)},
    "Speed": {"duration_weeks": 2, "intensity_range": (85, 100)},
    "Hypertrophy": {"duration_weeks": 5, "intensity_range": (65, 75)},
}

RESIDUAL_EFFECTS = {
    "Maximal Strength": 30,
    "Power": 18,
    "Speed": 5,
    "Hypertrophy": 15,
}

BLOCK_TO_ABILITY = {
    "Strength": "Maximal Strength",
    "Power": "Power",
    "Speed": "Speed",
    "Hypertrophy": "Hypertrophy",
}

MINI_BLOCK_EFFECT = {
    "Maximal Strength": 0.8,
    "Power": 0.75,
    "Speed": 0.7,
    "Hypertrophy": 0.75,
}

EXERCISES = {
    "Strength": ["Back Squat", "Sport Squat", "Bench Press", "DB Shoulder Press", "Rows"],
    "Power": ["Clean", "Snatch", "Jump Squats", "Medicine Ball Throws", "Plyometrics"],
    "Speed": ["Sprint Variations", "Plyometrics", "Medicine Ball Throws", "Band-Resisted Movements"],
    "Hypertrophy": ["Compound Movements", "Isolation Exercises", "Accessory Work"],
}

BLOCK_FOCUS = {
    "Strength": ["Force production", "Progressive overload", "Neural adaptations"],
    "Power": ["Rate of force development", "Technical mastery", "Explosive strength"],
    "Speed": ["Maximum velocity", "Neural efficiency", "Minimal resistance"],
    "Hypertrophy": ["Muscle development", "Volume accumulation", "Metabolic stress"],
}

WEEKLY_SCHEDULES = {
    3: ["Monday", "Wednesday", "Friday"],
    4: ["Monday", "Tuesday", "Thursday", "Friday"],
    5: ["Monday", "Tuesday", "Wednesday", "Friday", "Saturday"],
    6: ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday"],
}

DAY_INTENSITIES = {
    "Monday": "High Intensity",
    "Tuesday": "Medium-High Intensity",
    "Wednesday": "Medium Intensity",
    "Thursday": "Medium-High Intensity",
    "Friday": "High Volume",
    "Saturday": "Medium Intensity",
}

GOAL_PRIORITIES = {
    "Strength Peak": ["Hypertrophy", "Strength", "Power", "Speed"],
    "Power Peak": ["Hypertrophy", "Strength", "Power", "Speed"],
    "Speed Peak": ["Hypertrophy", "Strength", "Power", "Speed"],
    "Hypertrophy Focus": ["Strength", "Power", "Hypertrophy"],
    "General Fitness": ["Hypertrophy", "Strength", "Power"],
    "Competition Prep": ["Hypertrophy", "Strength", "Power", "Speed"],
}


def program_duration(blocks: list[str]) -> int:
    return sum(TRAINING_BLOCKS[b]["duration_weeks"] for b in blocks)


def generate_weekly_schedule(training_days: int) -> pd.DataFrame:
    if training_days not in WEEKLY_SCHEDULES:
        raise ValueError(f"training_days must be one of {list(WEEKLY_SCHEDULES.keys())}")
    schedule = WEEKLY_SCHEDULES[training_days]
    rows = [{"Day": day, "Training": DAY_INTENSITIES[day]} for day in schedule]
    return pd.DataFrame(rows)


# ---------------------------------------------------------------------------
# Residual effects engine (single implementation, replaces 2 prior copies)
# ---------------------------------------------------------------------------

def compute_residual_effects(
    blocks: list[str],
    optimized: bool = False,
    initial_retention: dict[str, float] | None = None,
) -> tuple[list[int], dict[str, list[float]], int]:
    total_weeks = program_duration(blocks) + 1
    max_residual_weeks = max(RESIDUAL_EFFECTS.values()) // 7
    timeline = list(range(total_weeks + max_residual_weeks))
    effects = {ability: [] for ability in RESIDUAL_EFFECTS}

    for week in timeline:
        week_effects = {ability: 0.0 for ability in RESIDUAL_EFFECTS}

        if week == 0 and initial_retention:
            for ability in RESIDUAL_EFFECTS:
                week_effects[ability] = initial_retention.get(ability, 0.0)

        current_pos = 0
        for block_idx, block in enumerate(blocks):
            duration = TRAINING_BLOCKS[block]["duration_weeks"]
            block_end = current_pos + duration
            ability = BLOCK_TO_ABILITY[block]

            if week >= current_pos:
                days_since = (week - block_end) * 7

                if week < block_end:
                    week_effects[ability] = 100.0
                    if optimized and block_idx > 0:
                        for prev_block in blocks[:block_idx]:
                            prev_ability = BLOCK_TO_ABILITY[prev_block]
                            mini_effect = MINI_BLOCK_EFFECT[prev_ability] * 100
                            week_effects[prev_ability] = max(week_effects[prev_ability], mini_effect)

                elif days_since < RESIDUAL_EFFECTS[ability]:
                    base = 100 * (1 - days_since / RESIDUAL_EFFECTS[ability])
                    if optimized and block_idx < len(blocks) - 1:
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
# Weekly block profiling from classified data
# ---------------------------------------------------------------------------

def weekly_block_profile(df: pd.DataFrame) -> pd.DataFrame:
    if df.empty:
        return pd.DataFrame()
    col = "block_type_classified" if "block_type_classified" in df.columns else "block_type"
    weekly = df.groupby(["week_start", col])["volume"].sum().unstack(fill_value=0)
    for bt in ["Strength", "Power", "Speed", "Hypertrophy"]:
        if bt not in weekly.columns:
            weekly[bt] = 0
    weekly["dominant"] = weekly[["Strength", "Power", "Speed", "Hypertrophy"]].idxmax(axis=1)
    return weekly.reset_index().sort_values("week_start")


def current_residual_status(df: pd.DataFrame) -> dict[str, dict]:
    today = datetime.now(timezone.utc)
    weekly = weekly_block_profile(df)
    status = {}

    for block_type, ability in BLOCK_TO_ABILITY.items():
        if weekly.empty:
            status[ability] = {"retention": 0.0, "days_since": None, "last_trained": None}
            continue
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
# Program recommendation engine
# ---------------------------------------------------------------------------

def _score_sequence(blocks: list[str], goal: str, weeks_available: int) -> float:
    total = program_duration(blocks)
    if total > weeks_available:
        return -1.0

    priority = GOAL_PRIORITIES[goal]
    target_ability = BLOCK_TO_ABILITY[priority[-1]]

    score = 0.0
    current_week = 0
    for block_idx, block in enumerate(blocks):
        duration = TRAINING_BLOCKS[block]["duration_weeks"]
        ability = BLOCK_TO_ABILITY[block]

        if ability == target_ability:
            score += 30 * ((current_week + 1) / total)

        for prev_idx in range(block_idx):
            prev_ability = BLOCK_TO_ABILITY[blocks[prev_idx]]
            prev_end = program_duration(blocks[: prev_idx + 1])
            days_gap = (current_week - prev_end) * 7
            residual = RESIDUAL_EFFECTS[prev_ability]
            if days_gap < residual:
                score += 100 * (1 - days_gap / residual) * 0.2

        current_week += duration

    for ability_name, residual_days in RESIDUAL_EFFECTS.items():
        bt = next((b for b, a in BLOCK_TO_ABILITY.items() if a == ability_name), None)
        if bt and bt in blocks:
            last_idx = len(blocks) - 1 - blocks[::-1].index(bt)
            end_of_block = program_duration(blocks[: last_idx + 1])
            days_to_end = (total - end_of_block) * 7
            if days_to_end < residual_days:
                weight = 2.0 if ability_name == target_ability else 0.5
                score += 100 * (1 - days_to_end / residual_days) * weight

    return score


def recommend_program(goal: str, weeks_available: int) -> list[str]:
    priority = GOAL_PRIORITIES[goal]
    best_seq, best_score = None, -1.0

    for length in range(len(priority), 0, -1):
        for perm in permutations(priority[:length]):
            seq = list(perm)
            if program_duration(seq) > weeks_available:
                continue
            s = _score_sequence(seq, goal, weeks_available)
            if s > best_score:
                best_score = s
                best_seq = seq

    return best_seq or [priority[-1]]
