from __future__ import annotations

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app.runner.validators import FlowValidationError, validate_flow_yaml
from app.schemas import FlowCreate, FlowUpdate
from app.services.flow_service import create_flow, delete_flow, format_yaml, update_flow
from app.services.run_service import start_run

router = APIRouter(prefix="/api/flows", tags=["flows"])


@router.post("")
def api_create_flow(payload: FlowCreate, db: Session = Depends(get_db)):
    try:
        return create_flow(db, payload)
    except FlowValidationError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.put("/{flow_id}")
def api_update_flow(flow_id: int, payload: FlowUpdate, db: Session = Depends(get_db)):
    try:
        return update_flow(db, flow_id, payload)
    except (FlowValidationError, ValueError) as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.delete("/{flow_id}")
def api_delete_flow(flow_id: int, db: Session = Depends(get_db)):
    delete_flow(db, flow_id)
    return {"ok": True}


@router.post("/{flow_id}/validate")
def api_validate_flow(flow_id: int, payload: dict, db: Session = Depends(get_db)):
    yaml_content = payload.get("yaml_content")
    if yaml_content is None:
        flow = db.get(__import__("app.models", fromlist=["Flow"]).Flow, flow_id)
        yaml_content = flow.yaml_content if flow else ""
    try:
        data = validate_flow_yaml(yaml_content)
        return {"ok": True, "name": data["name"]}
    except FlowValidationError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.post("/{flow_id}/format")
def api_format_flow(flow_id: int, payload: dict):
    try:
        return {"yaml_content": format_yaml(payload.get("yaml_content", ""))}
    except FlowValidationError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.post("/{flow_id}/run")
def api_run_flow(flow_id: int, background_tasks: BackgroundTasks, db: Session = Depends(get_db)):
    try:
        run = start_run(db, flow_id, background_tasks)
        return {"run_id": run.id, "status": run.status}
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
