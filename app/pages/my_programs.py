import streamlit as st

from ..periodization import TRAINING_BLOCKS, program_duration
from ..queries import get_user_programs
from ..db import get_db


def render():
    st.title("My Programs")
    programs = get_user_programs(st.session_state.user_id)

    if not programs:
        st.info("No saved programs yet. Build one in the Program Builder!")
        return

    for prog in programs:
        with st.expander(f"{prog.name} ({prog.created_at.strftime('%Y-%m-%d')})"):
            valid_blocks = [b for b in prog.blocks if b in TRAINING_BLOCKS]
            st.write(f"**Blocks:** {', '.join(prog.blocks)}")
            st.write(f"**Training days/week:** {prog.training_days}")
            st.write(f"**Duration:** {program_duration(valid_blocks)} weeks")

            if st.button("Delete", key=f"del_{prog.id}"):
                with get_db() as db:
                    obj = db.merge(prog)
                    db.delete(obj)
                st.rerun()
