from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app.services.run_service import get_run, mark_cancel, mark_continue

router = APIRouter(prefix="/api/runs", tags=["runs"])


def serialize_run(run):
    return {
        "id": run.id,
        "flow_id": run.flow_id,
        "flow_name": run.flow.name if run.flow else "",
        "status": run.status,
        "trigger_type": run.trigger_type,
        "current_step_index": run.current_step_index,
        "started_at": run.started_at,
        "ended_at": run.ended_at,
        "duration_ms": run.duration_ms,
        "error_message": run.error_message,
        "steps": [
            {
                "step_index": item.step_index,
                "action": item.action,
                "description": item.description,
                "status": item.status,
                "started_at": item.started_at,
                "ended_at": item.ended_at,
                "duration_ms": item.duration_ms,
                "input_snapshot": item.input_snapshot,
                "screenshot_path": item.screenshot_path,
                "error_message": item.error_message,
            }
            for item in run.step_logs
        ],
    }


@router.get("/{run_id}")
def api_get_run(run_id: int, db: Session = Depends(get_db)):
    run = get_run(db, run_id)
    if not run:
        raise HTTPException(status_code=404, detail="执行记录不存在")
    return serialize_run(run)


@router.post("/{run_id}/continue")
def api_continue_run(run_id: int, db: Session = Depends(get_db)):
    try:
        return {"ok": True, "status": mark_continue(db, run_id).status}
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@router.post("/{run_id}/cancel")
def api_cancel_run(run_id: int, db: Session = Depends(get_db)):
    try:
        return {"ok": True, "status": mark_cancel(db, run_id).status}
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
