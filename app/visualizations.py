from __future__ import annotations

import plotly.graph_objects as go

from .training import (
    TRAINING_BLOCKS,
    RESIDUAL_EFFECTS,
    compute_residual_effects,
)

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


def create_intensity_plot(blocks: list[str]) -> go.Figure:
    weeks, intensities_min, intensities_max = [], [], []
    current_week = 0

    for block in blocks:
        data = TRAINING_BLOCKS[block]
        for w in range(data["duration_weeks"]):
            weeks.append(current_week + w)
            intensities_min.append(data["intensity_range"][0])
            intensities_max.append(data["intensity_range"][1])
        current_week += data["duration_weeks"]

    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=weeks + weeks[::-1],
        y=intensities_max + intensities_min[::-1],
        fill="toself",
        fillcolor="rgba(0,100,80,0.2)",
        line=dict(color="rgba(255,255,255,0)"),
        showlegend=False,
        name="Intensity Range",
    ))
    fig.add_trace(go.Scatter(
        x=weeks, y=intensities_max,
        line=dict(color="rgb(0,100,80)"),
        name="Max Intensity",
    ))
    fig.add_trace(go.Scatter(
        x=weeks, y=intensities_min,
        line=dict(color="rgb(0,100,80)", dash="dash"),
        name="Min Intensity",
    ))
    fig.update_layout(
        title="Program Intensity Profile",
        xaxis_title="Week",
        yaxis_title="Intensity (%1RM)",
        hovermode="x unified",
        showlegend=True,
    )
    return fig


def create_residual_effects_plot(blocks: list[str], optimized: bool = False) -> go.Figure:
    timeline, effects_data, total_weeks = compute_residual_effects(blocks, optimized=optimized)

    fig = go.Figure()
    for ability in RESIDUAL_EFFECTS:
        fig.add_trace(go.Scatter(
            x=timeline,
            y=effects_data[ability],
            name=ability,
            line=dict(color=ABILITY_COLORS[ability]),
            hovertemplate="Week %{x}<br>" + f"{ability}: %{{y:.1f}}%<br><extra></extra>",
        ))

    current_week = 0
    for i, block in enumerate(blocks):
        if i > 0:
            fig.add_vline(x=current_week, line_dash="dash", line_color="gray", opacity=0.5)
        current_week += TRAINING_BLOCKS[block]["duration_weeks"]

    fig.add_vrect(
        x0=total_weeks - 1, x1=total_weeks,
        fillcolor="rgba(255, 255, 0, 0.3)", layer="below", line_width=0,
        annotation_text="Peak Week", annotation_position="top left",
    )

    title = "Optimized Residual Training Effects (with Mini-Blocks)" if optimized else "Residual Training Effects"
    fig.update_layout(
        title=title,
        xaxis_title="Weeks",
        yaxis_title="Effect Retention (%)",
        hovermode="x unified",
        showlegend=True,
        yaxis_range=[0, 100],
    )
    return fig


def create_program_gantt(blocks: list[str]) -> go.Figure:
    tasks = []
    current_week = 0

    for i, block in enumerate(blocks):
        duration = TRAINING_BLOCKS[block]["duration_weeks"]
        tasks.append({
            "Task": f"{block} Block", "Start": current_week,
            "Duration": duration, "Color": BLOCK_COLORS[block], "Type": "Main",
        })
        if i > 0:
            prev_block = blocks[i - 1]
            for mini_week in range(current_week, current_week + duration, 2):
                tasks.append({
                    "Task": f"{prev_block} Mini-Block", "Start": mini_week,
                    "Duration": 1, "Color": BLOCK_COLORS["Mini-Block"], "Type": "Mini",
                })
        current_week += duration

    tasks.append({
        "Task": "Peak Week", "Start": current_week,
        "Duration": 1, "Color": BLOCK_COLORS["Peak"], "Type": "Peak",
    })

    fig = go.Figure()
    for task in tasks:
        fig.add_trace(go.Bar(
            name=task["Task"],
            x=[task["Duration"]],
            y=[task["Task"]],
            orientation="h",
            marker=dict(color=task["Color"]),
            base=task["Start"],
            showlegend=task["Type"] == "Main",
            hovertemplate=(
                "Block: %{y}<br>Start Week: %{base}<br>"
                "Duration: %{x} week(s)<br><extra></extra>"
            ),
        ))
    fig.update_layout(
        title="Training Program Timeline",
        xaxis_title="Weeks",
        yaxis=dict(title="", autorange="reversed"),
        barmode="overlay",
        height=400,
        showlegend=True,
        legend_title="Training Blocks",
        hovermode="closest",
    )
    return fig


def create_schedule_heatmap(schedule_df) -> go.Figure:
    intensity_map = {
        "High Intensity": 3,
        "Medium-High Intensity": 2,
        "Medium Intensity": 1,
        "High Volume": 2.5,
    }
    intensity_values = [[intensity_map[t] for t in schedule_df["Training"]]]

    fig = go.Figure(data=go.Heatmap(
        z=intensity_values,
        x=schedule_df["Day"].tolist(),
        y=["Training"],
        colorscale="Viridis",
        showscale=False,
        text=[schedule_df["Training"].tolist()],
        texttemplate="%{text}",
        textfont={"size": 12, "color": "white"},
    ))
    fig.update_layout(
        title="Weekly Training Schedule Intensity",
        xaxis_title="Day of Week",
        yaxis_title="",
        height=200,
    )
    return fig
