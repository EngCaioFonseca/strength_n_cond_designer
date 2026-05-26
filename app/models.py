from datetime import datetime, timezone

from sqlalchemy import (
    Column, Integer, String, DateTime, ForeignKey, JSON, Text, CheckConstraint,
)
from sqlalchemy.orm import declarative_base, relationship

Base = declarative_base()


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True)
    email = Column(String(255), unique=True, nullable=False, index=True)
    password_hash = Column(String(255), nullable=False)
    name = Column(String(255), nullable=False)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    programs = relationship("TrainingProgram", back_populates="user", cascade="all, delete-orphan")
    logs = relationship("TrainingLog", back_populates="user", cascade="all, delete-orphan")


class TrainingProgram(Base):
    __tablename__ = "training_programs"

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    name = Column(String(255), nullable=False)
    blocks = Column(JSON, nullable=False)
    training_days = Column(Integer, nullable=False)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))

    __table_args__ = (
        CheckConstraint("training_days >= 3 AND training_days <= 6", name="ck_training_days_range"),
    )

    user = relationship("User", back_populates="programs")
    logs = relationship("TrainingLog", back_populates="program", cascade="all, delete-orphan")


class TrainingLog(Base):
    __tablename__ = "training_logs"

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    program_id = Column(Integer, ForeignKey("training_programs.id", ondelete="CASCADE"), nullable=True)
    date = Column(DateTime, nullable=False)
    block_type = Column(String(50))
    exercises = Column(JSON, nullable=False, default=list)
    notes = Column(Text)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    user = relationship("User", back_populates="logs")
    program = relationship("TrainingProgram", back_populates="logs")
