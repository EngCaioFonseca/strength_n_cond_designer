import streamlit as st

from ..auth import authenticate_user, create_user


def render_login():
    st.title("Login")
    with st.form("login_form"):
        email = st.text_input("Email")
        password = st.text_input("Password", type="password")
        submitted = st.form_submit_button("Login")

    if submitted:
        if not email or not password:
            st.error("Please fill in all fields.")
            return
        _, err = authenticate_user(email, password)
        if err:
            st.error(err)
        else:
            st.rerun()


def render_register():
    st.title("Create Account")
    with st.form("register_form"):
        name = st.text_input("Name")
        email = st.text_input("Email")
        password = st.text_input("Password", type="password")
        password_confirm = st.text_input("Confirm Password", type="password")
        submitted = st.form_submit_button("Register")

    if submitted:
        if not all([name, email, password, password_confirm]):
            st.error("Please fill in all fields.")
            return
        if "@" not in email or "." not in email.split("@")[-1]:
            st.error("Please enter a valid email address.")
            return
        if password != password_confirm:
            st.error("Passwords do not match.")
            return
        if len(password) < 8:
            st.error("Password must be at least 8 characters.")
            return
        _, err = create_user(email, password, name)
        if err:
            st.error(err)
        else:
            st.success("Account created! You can now log in.")


def render_auth_page():
    tab_login, tab_register = st.tabs(["Login", "Register"])
    with tab_login:
        render_login()
    with tab_register:
        render_register()
