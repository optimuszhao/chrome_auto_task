from __future__ import annotations

import yaml
from sqlalchemy.orm import Session

from app.models import Flow
from app.runner.validators import validate_flow_yaml
from app.schemas import FlowCreate, FlowUpdate


def list_flows(db: Session) -> list[Flow]:
    return db.query(Flow).order_by(Flow.updated_at.desc()).all()


def create_flow(db: Session, payload: FlowCreate) -> Flow:
    data = validate_flow_yaml(payload.yaml_content)
    flow = Flow(
        name=payload.name or data["name"],
        description=payload.description if payload.description is not None else data.get("description", ""),
        yaml_content=payload.yaml_content,
        enabled=payload.enabled,
    )
    db.add(flow)
    db.commit()
    db.refresh(flow)
    return flow


def update_flow(db: Session, flow_id: int, payload: FlowUpdate) -> Flow:
    flow = db.get(Flow, flow_id)
    if not flow:
        raise ValueError("任务不存在")
    data = validate_flow_yaml(payload.yaml_content)
    flow.name = payload.name or data["name"]
    flow.description = payload.description if payload.description is not None else data.get("description", "")
    flow.yaml_content = payload.yaml_content
    flow.enabled = payload.enabled
    db.add(flow)
    db.commit()
    db.refresh(flow)
    return flow


def delete_flow(db: Session, flow_id: int) -> None:
    flow = db.get(Flow, flow_id)
    if flow:
        db.delete(flow)
        db.commit()


def format_yaml(yaml_content: str) -> str:
    data = validate_flow_yaml(yaml_content)
    return yaml.safe_dump(data, allow_unicode=True, sort_keys=False)
