from __future__ import annotations

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


def generate_weekly_schedule(training_days: int) -> pd.DataFrame:
    if training_days not in WEEKLY_SCHEDULES:
        raise ValueError(f"training_days must be one of {list(WEEKLY_SCHEDULES.keys())}")
    schedule = WEEKLY_SCHEDULES[training_days]
    rows = [{"Day": day, "Training": DAY_INTENSITIES[day]} for day in schedule]
    return pd.DataFrame(rows)


def compute_residual_effects(blocks: list[str], optimized: bool = False):
    total_weeks = sum(TRAINING_BLOCKS[b]["duration_weeks"] for b in blocks) + 1
    max_residual_weeks = max(RESIDUAL_EFFECTS.values()) // 7
    timeline = list(range(total_weeks + max_residual_weeks))
    effects_data = {ability: [] for ability in RESIDUAL_EFFECTS}

    for week in timeline:
        week_effects = {ability: 0.0 for ability in RESIDUAL_EFFECTS}
        current_position = 0

        for block_idx, block in enumerate(blocks):
            block_duration = TRAINING_BLOCKS[block]["duration_weeks"]
            block_end_week = current_position + block_duration
            ability = BLOCK_TO_ABILITY[block]

            if week >= current_position:
                days_since_block = (week - block_end_week) * 7

                if week < block_end_week:
                    week_effects[ability] = 100.0
                    if optimized and block_idx > 0:
                        for prev_block in blocks[:block_idx]:
                            prev_ability = BLOCK_TO_ABILITY[prev_block]
                            mini_effect = MINI_BLOCK_EFFECT[prev_ability] * 100
                            week_effects[prev_ability] = max(week_effects[prev_ability], mini_effect)

                elif days_since_block < RESIDUAL_EFFECTS[ability]:
                    base_residual = 100 * (1 - days_since_block / RESIDUAL_EFFECTS[ability])
                    if optimized and block_idx < len(blocks) - 1:
                        base_residual += base_residual * MINI_BLOCK_EFFECT[ability]
                    week_effects[ability] = max(base_residual, week_effects[ability])

            current_position += block_duration

        if week == total_weeks - 1:
            for ability in RESIDUAL_EFFECTS:
                week_effects[ability] = 100.0

        for ability in RESIDUAL_EFFECTS:
            effects_data[ability].append(week_effects[ability])

    return timeline, effects_data, total_weeks
