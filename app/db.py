from contextlib import contextmanager

import streamlit as st
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session

from .config import DATABASE_URL


@st.cache_resource
def _get_engine():
    return create_engine(DATABASE_URL, pool_pre_ping=True)


def get_session_factory() -> sessionmaker:
    return sessionmaker(bind=_get_engine())


@contextmanager
def get_db() -> Session:
    factory = get_session_factory()
    session = factory()
    try:
        yield session
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()


def init_db():
    from .models import Base
    Base.metadata.create_all(_get_engine())
