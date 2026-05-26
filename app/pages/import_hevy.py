import pandas as pd
import streamlit as st

from ..hevy_import import parse_hevy_csv, group_workouts, save_workouts_to_db
from ..queries import get_user_programs


def render():
    st.title("Import from Hevy")
    st.markdown("Export your data from Hevy: **Profile > Settings > Export Data**. Upload the workout CSV file below.")

    programs = get_user_programs(st.session_state.user_id)
    program_options = {"None (standalone)": None}
    program_options.update({p.name: p.id for p in programs})

    uploaded = st.file_uploader("Upload Hevy CSV", type=["csv"])
    target_program = st.selectbox("Link to program (optional)", list(program_options.keys()))

    if uploaded is None:
        return

    try:
        df = parse_hevy_csv(uploaded)
    except Exception as e:
        st.error(f"Failed to parse CSV: {e}")
        return

    workouts = group_workouts(df)
    st.success(f"Parsed **{len(workouts)} workouts** with **{len(df)} total sets**.")

    st.subheader("Preview")
    for w in workouts[:5]:
        date_str = w["start_time"].strftime("%Y-%m-%d %H:%M") if pd.notna(w["start_time"]) else "unknown date"
        with st.expander(f"{w['title']} — {date_str}"):
            for ex in w["exercises"]:
                sets_str = ", ".join(
                    f"{s['reps']}r @ {s['weight_kg']}kg" + (f" RPE {s['rpe']}" if s.get("rpe") else "")
                    for s in ex["sets"]
                )
                st.write(f"**{ex['name']}**: {sets_str}")
    if len(workouts) > 5:
        st.caption(f"...and {len(workouts) - 5} more workouts.")

    if st.button("Import All"):
        count = save_workouts_to_db(st.session_state.user_id, workouts, program_options[target_program])
        st.success(f"Imported {count} workouts to your training log!")
        st.rerun()
