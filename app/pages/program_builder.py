import streamlit as st

from ..db import get_db
from ..models import TrainingProgram
from ..periodization import (
    TRAINING_BLOCKS, EXERCISES, BLOCK_FOCUS,
    program_duration, generate_weekly_schedule,
)
from ..charts import intensity_plot, residual_effects_plot, program_gantt, schedule_heatmap


def render():
    st.sidebar.title("Program Builder")
    blocks = st.sidebar.multiselect(
        "Select Training Blocks",
        options=list(TRAINING_BLOCKS.keys()),
        default=list(TRAINING_BLOCKS.keys()),
    )
    training_days = st.sidebar.slider("Training Days per Week", 3, 6, 4)

    if not blocks:
        st.info("Select at least one training block from the sidebar.")
        return

    st.sidebar.markdown("---")
    program_name = st.sidebar.text_input("Program Name", placeholder="e.g. Off-Season Strength")
    if st.sidebar.button("Save Program") and program_name:
        with get_db() as db:
            db.add(TrainingProgram(
                user_id=st.session_state.user_id, name=program_name,
                blocks=blocks, training_days=training_days,
            ))
        st.sidebar.success(f"Saved '{program_name}'")

    st.title("Program Analysis")
    st.write(f"**Program Duration:** {program_duration(blocks)} weeks")

    st.markdown("---")
    st.header("1. Intensity Profile")
    st.plotly_chart(intensity_plot(blocks), use_container_width=True)

    st.markdown("---")
    st.header("2. Residual Effects")
    st.plotly_chart(residual_effects_plot(blocks, optimized=False), use_container_width=True)

    st.markdown("---")
    st.header("3. Optimized Effects (with Mini-Blocks)")
    st.plotly_chart(residual_effects_plot(blocks, optimized=True), use_container_width=True)

    st.markdown("---")
    st.header("4. Block Analysis")
    for i, block in enumerate(blocks):
        st.subheader(f"Block {i + 1}: {block}")
        col1, col2 = st.columns(2)
        with col1:
            st.markdown("**Basic Information**")
            st.write(f"Duration: {TRAINING_BLOCKS[block]['duration_weeks']} weeks")
            lo, hi = TRAINING_BLOCKS[block]["intensity_range"]
            st.write(f"Intensity: {lo}-{hi}%")
            st.markdown("**Main Exercises**")
            for ex in EXERCISES[block]:
                st.write(f"- {ex}")
        with col2:
            st.markdown("**Block Focus**")
            for point in BLOCK_FOCUS[block]:
                st.write(f"- {point}")
        st.markdown("---")

    st.header("5. Weekly Schedule")
    st.plotly_chart(schedule_heatmap(generate_weekly_schedule(training_days)), use_container_width=True)
    col1, col2 = st.columns(2)
    with col1:
        st.markdown("**Training Guidelines**")
        st.write("- High Intensity: Technical focus")
        st.write("- Medium Intensity: Volume focus")
        st.write("- High Volume: Accumulation")
    with col2:
        st.markdown("**Recovery Focus**")
        st.write("- 24-48h between high intensity")
        st.write("- Active recovery on off days")
        st.write("- Sleep and nutrition priority")

    st.markdown("---")
    st.header("6. Program Timeline")
    st.plotly_chart(program_gantt(blocks), use_container_width=True)
