from __future__ import annotations

import argon2
import streamlit as st
from sqlalchemy import func

from .config import MAX_USERS
from .db import get_db
from .models import User

_hasher = argon2.PasswordHasher(time_cost=3, memory_cost=65536, parallelism=4)


def hash_password(password: str) -> str:
    return _hasher.hash(password)


def verify_password(password: str, hashed: str) -> bool:
    try:
        return _hasher.verify(hashed, password)
    except argon2.exceptions.VerifyMismatchError:
        return False


def normalize_email(email: str) -> str:
    return email.strip().lower()


def create_user(email: str, password: str, name: str) -> tuple[User | None, str]:
    email = normalize_email(email)
    with get_db() as db:
        if db.query(func.count(User.id)).scalar() >= MAX_USERS:
            return None, f"User limit reached ({MAX_USERS}). Registration is closed."
        if db.query(User).filter(User.email == email).first():
            return None, "An account with this email already exists."
        user = User(email=email, password_hash=hash_password(password), name=name.strip())
        db.add(user)
        db.flush()
        return user, ""


def authenticate_user(email: str, password: str) -> tuple[User | None, str]:
    email = normalize_email(email)
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
