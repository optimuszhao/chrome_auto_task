from __future__ import annotations

import asyncio
from datetime import datetime

from fastapi import BackgroundTasks
from sqlalchemy.orm import Session, selectinload

from app.models import Flow, Run
from app.runner.playwright_runner import cancel_run, continue_run, run_flow_async


def create_run(db: Session, flow_id: int, trigger_type: str = "manual") -> Run:
    flow = db.get(Flow, flow_id)
    if not flow:
        raise ValueError("任务不存在")
    run = Run(flow_id=flow_id, trigger_type=trigger_type, status="PENDING")
    db.add(run)
    db.commit()
    db.refresh(run)
    return run


def start_run(db: Session, flow_id: int, background_tasks: BackgroundTasks | None = None, trigger_type: str = "manual") -> Run:
    run = create_run(db, flow_id, trigger_type)
    if background_tasks:
        background_tasks.add_task(asyncio.run, run_flow_async(flow_id, run.id))
    else:
        asyncio.create_task(run_flow_async(flow_id, run.id))
    return run


def get_run(db: Session, run_id: int) -> Run | None:
    return db.query(Run).options(selectinload(Run.flow), selectinload(Run.step_logs)).filter(Run.id == run_id).first()


def mark_continue(db: Session, run_id: int) -> Run:
    run = db.get(Run, run_id)
    if not run:
        raise ValueError("执行记录不存在")
    run.status = "RUNNING"
    db.add(run)
    db.commit()
    continue_run(run_id)
    return run


def mark_cancel(db: Session, run_id: int) -> Run:
    run = db.get(Run, run_id)
    if not run:
        raise ValueError("执行记录不存在")
    run.status = "CANCELLED"
    run.ended_at = datetime.utcnow()
    db.add(run)
    db.commit()
    cancel_run(run_id)
    return run
