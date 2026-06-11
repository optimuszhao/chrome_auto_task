from __future__ import annotations

from datetime import datetime
from time import perf_counter

from sqlalchemy.orm import Session

from app.models import RunStepLog
from app.runner.validators import safe_json


def create_step_log(db: Session, run_id: int, step_index: int, step: dict) -> tuple[RunStepLog, float]:
    started = perf_counter()
    log = RunStepLog(
        run_id=run_id,
        step_index=step_index,
        action=step.get("action", ""),
        description=step.get("description", ""),
        status="RUNNING",
        started_at=datetime.utcnow(),
        input_snapshot=safe_json(step),
    )
    db.add(log)
    db.commit()
    db.refresh(log)
    return log, started


def finish_step_log(db: Session, log: RunStepLog, started: float, status: str, screenshot_path: str | None = None, error: str | None = None) -> None:
    log.status = status
    log.ended_at = datetime.utcnow()
    log.duration_ms = int((perf_counter() - started) * 1000)
    log.screenshot_path = screenshot_path or log.screenshot_path
    log.error_message = error
    db.add(log)
    db.commit()
