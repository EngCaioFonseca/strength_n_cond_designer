import streamlit as st
from datetime import datetime, timezone

from .db import init_db, get_db
from .auth import is_logged_in, logout, render_auth_page
from .models import TrainingProgram, TrainingLog
from .training import (
    TRAINING_BLOCKS,
    EXERCISES,
    BLOCK_FOCUS,
    generate_weekly_schedule,
)
from .visualizations import (
    create_intensity_plot,
    create_residual_effects_plot,
    create_program_gantt,
    create_schedule_heatmap,
)
from .hevy_import import render_import_page
from .analytics import render_analytics_page

st.set_page_config(page_title="S&C Program Builder", layout="wide")
init_db()


def render_program_builder():
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

    # Save program
    st.sidebar.markdown("---")
    program_name = st.sidebar.text_input("Program Name", placeholder="e.g. Off-Season Strength")
    if st.sidebar.button("Save Program") and program_name:
        with get_db() as db:
            program = TrainingProgram(
                user_id=st.session_state.user_id,
                name=program_name,
                blocks=blocks,
                training_days=training_days,
            )
            db.add(program)
        st.sidebar.success(f"Saved '{program_name}'")

    # Analysis
    st.title("Program Analysis")
    total_weeks = sum(TRAINING_BLOCKS[b]["duration_weeks"] for b in blocks)
    st.write(f"**Program Duration:** {total_weeks} weeks")

    st.markdown("---")
    st.header("1. Intensity Profile")
    st.plotly_chart(create_intensity_plot(blocks), use_container_width=True)

    st.markdown("---")
    st.header("2. Residual Effects")
    st.plotly_chart(create_residual_effects_plot(blocks, optimized=False), use_container_width=True)

    st.markdown("---")
    st.header("3. Optimized Effects (with Mini-Blocks)")
    st.plotly_chart(create_residual_effects_plot(blocks, optimized=True), use_container_width=True)

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
    schedule_df = generate_weekly_schedule(training_days)
    st.plotly_chart(create_schedule_heatmap(schedule_df), use_container_width=True)
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
    st.plotly_chart(create_program_gantt(blocks), use_container_width=True)

    st.markdown("---")
    st.markdown("### Implementation Guidelines")
    st.markdown(
        "1. Mini-blocks: 1-2 sessions per week\n"
        "2. Quality over quantity\n"
        "3. Adjust based on recovery\n"
        "4. Peak week: reduced volume, maintained intensity"
    )


def render_my_programs():
    st.title("My Programs")
    with get_db() as db:
        programs = (
            db.query(TrainingProgram)
            .filter(TrainingProgram.user_id == st.session_state.user_id)
            .order_by(TrainingProgram.created_at.desc())
            .all()
        )
        if not programs:
            st.info("No saved programs yet. Build one in the Program Builder!")
            return

        for prog in programs:
            with st.expander(f"{prog.name} ({prog.created_at.strftime('%Y-%m-%d')})"):
                st.write(f"**Blocks:** {', '.join(prog.blocks)}")
                st.write(f"**Training days/week:** {prog.training_days}")
                total = sum(TRAINING_BLOCKS[b]["duration_weeks"] for b in prog.blocks if b in TRAINING_BLOCKS)
                st.write(f"**Duration:** {total} weeks")

                col1, col2 = st.columns(2)
                with col1:
                    if st.button("View Analysis", key=f"view_{prog.id}"):
                        st.session_state.view_program_id = prog.id
                        st.session_state.nav = "Program Builder"
                        st.rerun()
                with col2:
                    if st.button("Delete", key=f"del_{prog.id}"):
                        db.delete(prog)
                        st.rerun()


def render_training_log():
    st.title("Training Log")

    with get_db() as db:
        programs = (
            db.query(TrainingProgram)
            .filter(TrainingProgram.user_id == st.session_state.user_id)
            .all()
        )
        program_options = {f"{p.name} ({p.id})": p.id for p in programs}

    # Log new session
    st.header("Log a Session")
    with st.form("log_form"):
        col1, col2 = st.columns(2)
        with col1:
            log_date = st.date_input("Date", value=datetime.now(timezone.utc).date())
            block_type = st.selectbox("Block Type", list(TRAINING_BLOCKS.keys()))
        with col2:
            selected_program = st.selectbox(
                "Program (optional)",
                options=["None"] + list(program_options.keys()),
            )

        st.markdown("**Exercises**")
        exercises = []
        for i in range(5):
            cols = st.columns([3, 1, 1, 1])
            with cols[0]:
                ex_name = st.text_input("Exercise", key=f"ex_name_{i}", placeholder="e.g. Back Squat")
            with cols[1]:
                sets = st.number_input("Sets", min_value=0, max_value=20, value=0, key=f"ex_sets_{i}")
            with cols[2]:
                reps = st.number_input("Reps", min_value=0, max_value=50, value=0, key=f"ex_reps_{i}")
            with cols[3]:
                weight = st.number_input("Weight (kg)", min_value=0.0, step=2.5, value=0.0, key=f"ex_weight_{i}")
            if ex_name:
                exercises.append({"name": ex_name, "sets": sets, "reps": reps, "weight": weight})

        notes = st.text_area("Notes")
        submitted = st.form_submit_button("Save Log Entry")

    if submitted:
        if not exercises:
            st.error("Add at least one exercise.")
        else:
            program_id = program_options.get(selected_program) if selected_program != "None" else None
            with get_db() as db:
                log = TrainingLog(
                    user_id=st.session_state.user_id,
                    program_id=program_id,
                    date=datetime.combine(log_date, datetime.min.time()),
                    block_type=block_type,
                    exercises=exercises,
                    notes=notes,
                )
                db.add(log)
            st.success("Training session logged!")

    # View log history
    st.markdown("---")
    st.header("Session History")
    with get_db() as db:
        logs = (
            db.query(TrainingLog)
            .filter(TrainingLog.user_id == st.session_state.user_id)
            .order_by(TrainingLog.date.desc())
            .limit(50)
            .all()
        )
        if not logs:
            st.info("No training sessions logged yet.")
            return

        for log in logs:
            label = f"{log.date.strftime('%Y-%m-%d')} - {log.block_type or 'General'}"
            with st.expander(label):
                if log.exercises:
                    for ex in log.exercises:
                        st.write(f"- **{ex['name']}**: {ex['sets']}x{ex['reps']} @ {ex['weight']}kg")
                if log.notes:
                    st.write(f"*{log.notes}*")
                if st.button("Delete", key=f"del_log_{log.id}"):
                    db.delete(log)
                    st.rerun()


def main():
    if not is_logged_in():
        render_auth_page()
        return

    # Sidebar navigation
    st.sidebar.markdown(f"**Logged in as** {st.session_state.user_name}")
    if st.sidebar.button("Logout"):
        logout()
        st.rerun()

    st.sidebar.markdown("---")
    nav = st.sidebar.radio(
        "Navigation",
        ["Program Builder", "My Programs", "Training Log", "Import from Hevy", "Analytics"],
    )

    if nav == "Program Builder":
        render_program_builder()
    elif nav == "My Programs":
        render_my_programs()
    elif nav == "Training Log":
        render_training_log()
    elif nav == "Import from Hevy":
        render_import_page()
    elif nav == "Analytics":
        render_analytics_page()


if __name__ == "__main__":
    main()
