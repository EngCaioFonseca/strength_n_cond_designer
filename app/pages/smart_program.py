import streamlit as st

from ..queries import logs_to_dataframe
from ..classifiers import add_classification_columns
from ..periodization import (
    TRAINING_BLOCKS, BLOCK_TO_ABILITY, RESIDUAL_EFFECTS, MINI_BLOCK_EFFECT,
    GOAL_PRIORITIES, program_duration,
    weekly_block_profile, current_residual_status,
    compute_residual_effects, recommend_program,
)
from ..charts import (
    training_history_chart, current_residuals_chart,
    residual_effects_plot, current_vs_peak_chart,
)


def render():
    st.title("Smart Program Recommendation")
    st.markdown(
        "Analyzes your training history, shows where your residual effects stand today, "
        "and recommends an optimal block sequence to reach your goal."
    )

    df = logs_to_dataframe(st.session_state.user_id)
    if df.empty:
        st.warning("No training data found. Import from Hevy or log sessions first.")
        return

    df = add_classification_columns(df)

    # 1. Training history
    st.markdown("---")
    st.header("1. Your Training History")
    weekly = weekly_block_profile(df)

    col1, col2, col3 = st.columns(3)
    col1.metric("Weeks of Data", len(weekly))
    col2.metric("Total Sessions", df["date"].nunique())
    col3.metric("Exercises Tracked", df["exercise"].nunique())

    st.plotly_chart(training_history_chart(weekly), use_container_width=True)

    recent = weekly.tail(4)
    if not recent.empty:
        dominant = recent["dominant"].value_counts()
        st.markdown(f"**Recent focus (last 4 weeks):** {dominant.index[0]} ({dominant.iloc[0]} of {len(recent)} weeks)")

    # 2. Current residual effects
    st.markdown("---")
    st.header("2. Current Residual Effects")
    status = current_residual_status(df)
    st.plotly_chart(current_residuals_chart(status), use_container_width=True)

    cols = st.columns(4)
    for i, (ability, info) in enumerate(status.items()):
        with cols[i]:
            st.caption(f"**{ability}**")
            if info["days_since"] is not None:
                st.write(f"{info['retention']:.0f}% retained")
                st.write(f"{info['days_since']}d since last block")
            else:
                st.write("No data")

    # 3. Goal & recommendation
    st.markdown("---")
    st.header("3. Your Goal")
    col_goal, col_weeks = st.columns(2)
    with col_goal:
        goal = st.selectbox("What are you training for?", list(GOAL_PRIORITIES.keys()))
    with col_weeks:
        weeks_available = st.slider("Weeks available", 4, 24, 12)

    recommended = recommend_program(goal, weeks_available)

    st.subheader("Recommended Block Sequence")
    block_cols = st.columns(len(recommended) + 1)
    for i, block in enumerate(recommended):
        with block_cols[i]:
            lo, hi = TRAINING_BLOCKS[block]["intensity_range"]
            st.markdown(f"**Block {i+1}: {block}**")
            st.write(f"{TRAINING_BLOCKS[block]['duration_weeks']} weeks @ {lo}-{hi}% 1RM")
    with block_cols[-1]:
        st.markdown("**Peak Week**")
        st.write("1 week — all qualities")

    st.write(f"**Total program duration:** {program_duration(recommended) + 1} weeks (including peak)")

    # 4. Projected effects
    st.markdown("---")
    st.header("4. Projected Training Effects")
    initial = {a: status[a]["retention"] for a in status}
    timeline, effects, tw = compute_residual_effects(recommended, optimized=True, initial_retention=initial)
    st.plotly_chart(residual_effects_plot(recommended, optimized=True, initial_retention=initial), use_container_width=True)

    # 5. Before vs after
    st.markdown("---")
    st.header("5. Current vs. Peak Comparison")
    st.plotly_chart(current_vs_peak_chart(status, effects, tw), use_container_width=True)

    # 6. Implementation
    st.markdown("---")
    st.header("6. Implementation Guidelines")
    for i, block in enumerate(recommended):
        ability = BLOCK_TO_ABILITY[block]
        st.markdown(f"**Block {i+1}: {block}** ({TRAINING_BLOCKS[block]['duration_weeks']} weeks)")
        lo, hi = TRAINING_BLOCKS[block]["intensity_range"]
        st.write(f"- Intensity zone: {lo}-{hi}% 1RM")
        st.write(f"- Residual effect lasts {RESIDUAL_EFFECTS[ability]} days after block ends")
        if i > 0:
            prev_ability = BLOCK_TO_ABILITY[recommended[i - 1]]
            st.write(f"- Include {recommended[i-1]} mini-blocks (1-2 sessions/week) to maintain {MINI_BLOCK_EFFECT[prev_ability]*100:.0f}% of {prev_ability}")
        st.write("")

    st.markdown("**Peak Week:** Reduce volume by 40-60%, maintain intensity. Integrate all training qualities at competition-level specificity.")
