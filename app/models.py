from __future__ import annotations

from datetime import datetime
from typing import Optional

from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


def now_utc() -> datetime:
    return datetime.utcnow()


class Flow(Base):
    __tablename__ = "flows"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    name: Mapped[str] = mapped_column(String(200), nullable=False, index=True)
    description: Mapped[str] = mapped_column(Text, default="")
    yaml_content: Mapped[str] = mapped_column(Text, nullable=False)
    enabled: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=now_utc)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=now_utc, onupdate=now_utc)

    runs: Mapped[list["Run"]] = relationship(back_populates="flow", cascade="all, delete-orphan")
    schedules: Mapped[list["Schedule"]] = relationship(back_populates="flow", cascade="all, delete-orphan")


class Run(Base):
    __tablename__ = "runs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    flow_id: Mapped[int] = mapped_column(ForeignKey("flows.id"), nullable=False, index=True)
    status: Mapped[str] = mapped_column(String(40), default="PENDING", index=True)
    trigger_type: Mapped[str] = mapped_column(String(40), default="manual")
    current_step_index: Mapped[int] = mapped_column(Integer, default=0)
    started_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    ended_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    duration_ms: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    error_message: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=now_utc)

    flow: Mapped["Flow"] = relationship(back_populates="runs")
    step_logs: Mapped[list["RunStepLog"]] = relationship(back_populates="run", cascade="all, delete-orphan", order_by="RunStepLog.step_index")


class RunStepLog(Base):
    __tablename__ = "run_step_logs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    run_id: Mapped[int] = mapped_column(ForeignKey("runs.id"), nullable=False, index=True)
    step_index: Mapped[int] = mapped_column(Integer, nullable=False)
    action: Mapped[str] = mapped_column(String(80), nullable=False)
    description: Mapped[str] = mapped_column(Text, default="")
    status: Mapped[str] = mapped_column(String(40), default="PENDING")
    started_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    ended_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    duration_ms: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    input_snapshot: Mapped[str] = mapped_column(Text, default="")
    screenshot_path: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    error_message: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    run: Mapped["Run"] = relationship(back_populates="step_logs")


class Schedule(Base):
    __tablename__ = "schedules"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    flow_id: Mapped[int] = mapped_column(ForeignKey("flows.id"), nullable=False, index=True)
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    schedule_type: Mapped[str] = mapped_column(String(40), nullable=False)
    cron_expr: Mapped[Optional[str]] = mapped_column(String(200), nullable=True)
    interval_seconds: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    run_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    enabled: Mapped[bool] = mapped_column(Boolean, default=True)
    next_run_time: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=now_utc)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=now_utc, onupdate=now_utc)

    flow: Mapped["Flow"] = relationship(back_populates="schedules")
