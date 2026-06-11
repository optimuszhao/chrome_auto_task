from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import Schedule
from app.scheduler import remove_schedule_job, sync_schedule_job
from app.schemas import ScheduleCreate, ScheduleUpdate

router = APIRouter(prefix="/api/schedules", tags=["schedules"])


def _save_schedule(db: Session, schedule: Schedule, payload: ScheduleCreate | ScheduleUpdate) -> Schedule:
    schedule.flow_id = payload.flow_id
    schedule.name = payload.name
    schedule.schedule_type = payload.schedule_type
    schedule.cron_expr = payload.cron_expr
    schedule.interval_seconds = payload.interval_seconds
    schedule.run_at = payload.run_at
    schedule.enabled = payload.enabled
    db.add(schedule)
    db.commit()
    db.refresh(schedule)
    sync_schedule_job(db, schedule)
    db.refresh(schedule)
    return schedule


@router.post("")
def api_create_schedule(payload: ScheduleCreate, db: Session = Depends(get_db)):
    try:
        return _save_schedule(db, Schedule(), payload)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.put("/{schedule_id}")
def api_update_schedule(schedule_id: int, payload: ScheduleUpdate, db: Session = Depends(get_db)):
    schedule = db.get(Schedule, schedule_id)
    if not schedule:
        raise HTTPException(status_code=404, detail="计划不存在")
    try:
        return _save_schedule(db, schedule, payload)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.delete("/{schedule_id}")
def api_delete_schedule(schedule_id: int, db: Session = Depends(get_db)):
    schedule = db.get(Schedule, schedule_id)
    if schedule:
        db.delete(schedule)
        db.commit()
    remove_schedule_job(schedule_id)
    return {"ok": True}


@router.post("/{schedule_id}/enable")
def api_enable_schedule(schedule_id: int, db: Session = Depends(get_db)):
    schedule = db.get(Schedule, schedule_id)
    if not schedule:
        raise HTTPException(status_code=404, detail="计划不存在")
    schedule.enabled = True
    sync_schedule_job(db, schedule)
    return {"ok": True}


@router.post("/{schedule_id}/disable")
def api_disable_schedule(schedule_id: int, db: Session = Depends(get_db)):
    schedule = db.get(Schedule, schedule_id)
    if not schedule:
        raise HTTPException(status_code=404, detail="计划不存在")
    schedule.enabled = False
    sync_schedule_job(db, schedule)
    return {"ok": True}
