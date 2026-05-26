import streamlit as st

from .db import init_db
from .auth import is_logged_in, logout
from .pages.auth import render_auth_page
from .pages import (
    program_builder,
    my_programs,
    training_log,
    import_hevy,
    analytics,
    smart_program,
)

st.set_page_config(page_title="S&C Program Builder", layout="wide")
init_db()

PAGES = {
    "Smart Program": smart_program.render,
    "Program Builder": program_builder.render,
    "My Programs": my_programs.render,
    "Training Log": training_log.render,
    "Import from Hevy": import_hevy.render,
    "Analytics": analytics.render,
}


def main():
    if not is_logged_in():
        render_auth_page()
        return

    st.sidebar.markdown(f"**Logged in as** {st.session_state.user_name}")
    if st.sidebar.button("Logout"):
        logout()
        st.rerun()

    st.sidebar.markdown("---")
    nav = st.sidebar.radio("Navigation", list(PAGES.keys()))
    PAGES[nav]()


if __name__ == "__main__":
    main()
