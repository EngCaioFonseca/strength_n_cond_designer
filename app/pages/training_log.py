from datetime import datetime, timezone

import streamlit as st

from ..db import get_db
from ..models import TrainingLog
from ..periodization import TRAINING_BLOCKS
from ..queries import get_user_programs, get_user_logs


def render():
    st.title("Training Log")

    programs = get_user_programs(st.session_state.user_id)
    program_options = {f"{p.name} ({p.id})": p.id for p in programs}

    st.header("Log a Session")
    with st.form("log_form"):
        col1, col2 = st.columns(2)
        with col1:
            log_date = st.date_input("Date", value=datetime.now(timezone.utc).date())
            block_type = st.selectbox("Block Type", list(TRAINING_BLOCKS.keys()))
        with col2:
            selected_program = st.selectbox("Program (optional)", options=["None"] + list(program_options.keys()))

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
                db.add(TrainingLog(
                    user_id=st.session_state.user_id, program_id=program_id,
                    date=datetime.combine(log_date, datetime.min.time()),
                    block_type=block_type, exercises=exercises, notes=notes,
                ))
            st.success("Training session logged!")

    st.markdown("---")
    st.header("Session History")
    logs = get_user_logs(st.session_state.user_id, limit=50)
    if not logs:
        st.info("No training sessions logged yet.")
        return

    for log in logs:
        label = f"{log.date.strftime('%Y-%m-%d')} - {log.block_type or 'General'}"
        with st.expander(label):
            for ex in (log.exercises or []):
                st.write(f"- **{ex['name']}**: {ex.get('sets', 1)}x{ex.get('reps', 0)} @ {ex.get('weight', 0)}kg")
            if log.notes:
                st.write(f"*{log.notes}*")
            if st.button("Delete", key=f"del_log_{log.id}"):
                with get_db() as db:
                    obj = db.merge(log)
                    db.delete(obj)
                st.rerun()
