import bcrypt
import streamlit as st
from sqlalchemy import func

from .config import MAX_USERS
from .db import get_db
from .models import User


def hash_password(password: str) -> str:
    return bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()


def verify_password(password: str, hashed: str) -> bool:
    return bcrypt.checkpw(password.encode(), hashed.encode())


def create_user(email: str, password: str, name: str) -> tuple[User | None, str]:
    with get_db() as db:
        user_count = db.query(func.count(User.id)).scalar()
        if user_count >= MAX_USERS:
            return None, f"User limit reached ({MAX_USERS}). Registration is closed."

        existing = db.query(User).filter(User.email == email).first()
        if existing:
            return None, "An account with this email already exists."

        user = User(email=email, password_hash=hash_password(password), name=name)
        db.add(user)
        db.flush()
        return user, ""


def authenticate_user(email: str, password: str) -> tuple[User | None, str]:
    with get_db() as db:
        user = db.query(User).filter(User.email == email).first()
        if not user or not verify_password(password, user.password_hash):
            return None, "Invalid email or password."
        st.session_state.user_id = user.id
        st.session_state.user_name = user.name
        st.session_state.user_email = user.email
        return user, ""


def logout():
    for key in ["user_id", "user_name", "user_email"]:
        st.session_state.pop(key, None)


def is_logged_in() -> bool:
    return "user_id" in st.session_state


def render_login_page():
    st.title("Login")
    with st.form("login_form"):
        email = st.text_input("Email")
        password = st.text_input("Password", type="password")
        submitted = st.form_submit_button("Login")

    if submitted:
        if not email or not password:
            st.error("Please fill in all fields.")
            return
        user, err = authenticate_user(email, password)
        if err:
            st.error(err)
        else:
            st.rerun()


def render_register_page():
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
        if password != password_confirm:
            st.error("Passwords do not match.")
            return
        if len(password) < 8:
            st.error("Password must be at least 8 characters.")
            return
        user, err = create_user(email, password, name)
        if err:
            st.error(err)
        else:
            st.success("Account created! You can now log in.")


def render_auth_page():
    tab_login, tab_register = st.tabs(["Login", "Register"])
    with tab_login:
        render_login_page()
    with tab_register:
        render_register_page()
