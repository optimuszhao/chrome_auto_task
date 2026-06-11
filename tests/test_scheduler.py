from __future__ import annotations

from datetime import datetime, timedelta

from app.models import Schedule
from app.scheduler import load_enabled_schedules, scheduler, sync_schedule_job
from app.schemas import FlowCreate
from app.services.flow_service import create_flow


def test_create_interval_schedule(db, valid_yaml):
    flow = create_flow(db, FlowCreate(yaml_content=valid_yaml))
    schedule = Schedule(flow_id=flow.id, name="每分钟", schedule_type="interval", interval_seconds=60, enabled=True)
    db.add(schedule)
    db.commit()
    db.refresh(schedule)
    if not scheduler.running:
        scheduler.start()
    sync_schedule_job(db, schedule)
    assert scheduler.get_job(f"schedule-{schedule.id}")


def test_create_cron_schedule(db, valid_yaml):
    flow = create_flow(db, FlowCreate(yaml_content=valid_yaml))
    schedule = Schedule(flow_id=flow.id, name="cron", schedule_type="cron", cron_expr="*/5 * * * *", enabled=True)
    db.add(schedule)
    db.commit()
    db.refresh(schedule)
    if not scheduler.running:
        scheduler.start()
    sync_schedule_job(db, schedule)
    assert scheduler.get_job(f"schedule-{schedule.id}")


def test_disable_and_delete_schedule(db, valid_yaml):
    flow = create_flow(db, FlowCreate(yaml_content=valid_yaml))
    schedule = Schedule(flow_id=flow.id, name="once", schedule_type="date", run_at=datetime.utcnow() + timedelta(minutes=5), enabled=True)
    db.add(schedule)
    db.commit()
    db.refresh(schedule)
    if not scheduler.running:
        scheduler.start()
    sync_schedule_job(db, schedule)
    schedule.enabled = False
    sync_schedule_job(db, schedule)
    assert schedule.enabled is False
    assert scheduler.get_job(f"schedule-{schedule.id}") is None


def test_load_enabled_schedules(db, valid_yaml):
    flow = create_flow(db, FlowCreate(yaml_content=valid_yaml))
    db.add(Schedule(flow_id=flow.id, name="loaded", schedule_type="interval", interval_seconds=120, enabled=True))
    db.commit()
    if not scheduler.running:
        scheduler.start()
    load_enabled_schedules()
    assert len(scheduler.get_jobs()) >= 1
