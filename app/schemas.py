from __future__ import annotations

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict


class FlowCreate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = ""
    yaml_content: str
    enabled: bool = True


class FlowUpdate(FlowCreate):
    pass


class FlowOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    description: str
    yaml_content: str
    enabled: bool
    created_at: datetime
    updated_at: datetime


class ScheduleCreate(BaseModel):
    flow_id: int
    name: str
    schedule_type: str
    cron_expr: Optional[str] = None
    interval_seconds: Optional[int] = None
    run_at: Optional[datetime] = None
    enabled: bool = True


class ScheduleUpdate(ScheduleCreate):
    pass
