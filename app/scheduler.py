from __future__ import annotations

from datetime import datetime

from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger
from apscheduler.triggers.date import DateTrigger
from apscheduler.triggers.interval import IntervalTrigger
from sqlalchemy.orm import Session

from app.database import SessionLocal
from app.models import Schedule
from app.services.run_service import create_run
from app.runner.playwright_runner import run_flow_background

scheduler = BackgroundScheduler(timezone="Asia/Shanghai")


def _job_id(schedule_id: int) -> str:
    return f"schedule-{schedule_id}"


def run_scheduled_flow(flow_id: int) -> None:
    db = SessionLocal()
    try:
        run = create_run(db, flow_id, trigger_type="schedule")
        run_flow_background(flow_id, run.id)
    finally:
        db.close()


def build_trigger(schedule: Schedule):
    if schedule.schedule_type == "interval":
        return IntervalTrigger(seconds=schedule.interval_seconds or 60)
    if schedule.schedule_type == "date":
        return DateTrigger(run_date=schedule.run_at or datetime.utcnow())
    if schedule.schedule_type == "cron":
        fields = (schedule.cron_expr or "* * * * *").split()
        if len(fields) != 5:
            raise ValueError("cron 表达式需要 5 段")
        minute, hour, day, month, day_of_week = fields
        return CronTrigger(minute=minute, hour=hour, day=day, month=month, day_of_week=day_of_week)
    raise ValueError("不支持的调度类型")


def sync_schedule_job(db: Session, schedule: Schedule) -> None:
    scheduler.remove_job(_job_id(schedule.id)) if scheduler.get_job(_job_id(schedule.id)) else None
    if not schedule.enabled:
        schedule.next_run_time = None
        db.add(schedule)
        db.commit()
        return
    trigger = build_trigger(schedule)
    job = scheduler.add_job(
        run_scheduled_flow,
        trigger=trigger,
        args=[schedule.flow_id],
        id=_job_id(schedule.id),
        replace_existing=True,
        max_instances=1,
        coalesce=True,
    )
    schedule.next_run_time = job.next_run_time.replace(tzinfo=None) if job.next_run_time else None
    db.add(schedule)
    db.commit()


def remove_schedule_job(schedule_id: int) -> None:
    if scheduler.get_job(_job_id(schedule_id)):
        scheduler.remove_job(_job_id(schedule_id))


def load_enabled_schedules() -> None:
    db = SessionLocal()
    try:
        for schedule in db.query(Schedule).filter(Schedule.enabled.is_(True)).all():
            sync_schedule_job(db, schedule)
    finally:
        db.close()


def start_scheduler() -> None:
    if not scheduler.running:
        scheduler.start()
    load_enabled_schedules()


def shutdown_scheduler() -> None:
    if scheduler.running:
        scheduler.shutdown(wait=False)
