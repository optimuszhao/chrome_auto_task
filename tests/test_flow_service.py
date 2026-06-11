from __future__ import annotations

import pytest

from app.runner.validators import FlowValidationError
from app.schemas import FlowCreate, FlowUpdate
from app.services.flow_service import create_flow, delete_flow, list_flows, update_flow


def test_create_update_delete_list_flow(db, valid_yaml):
    flow = create_flow(db, FlowCreate(yaml_content=valid_yaml))
    assert flow.id
    assert len(list_flows(db)) == 1

    updated_yaml = valid_yaml.replace("Mock 登录", "Mock 更新")
    flow = update_flow(db, flow.id, FlowUpdate(yaml_content=updated_yaml, enabled=False))
    assert flow.name == "Mock 更新"
    assert flow.enabled is False

    delete_flow(db, flow.id)
    assert list_flows(db) == []


def test_create_invalid_yaml_returns_error(db):
    with pytest.raises(FlowValidationError):
        create_flow(db, FlowCreate(yaml_content="name: x\nsteps: []"))
