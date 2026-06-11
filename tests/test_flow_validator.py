from __future__ import annotations

import pytest

from app.runner.validators import FlowValidationError, mask_sensitive, validate_flow_yaml


def assert_invalid(yaml_content: str):
    with pytest.raises(FlowValidationError):
        validate_flow_yaml(yaml_content)


def test_valid_yaml_passes(valid_yaml):
    data = validate_flow_yaml(valid_yaml)
    assert data["name"] == "Mock 登录"


def test_missing_name_fails(valid_yaml):
    assert_invalid(valid_yaml.replace("name: Mock 登录", "description: only"))


def test_empty_steps_fails(valid_yaml):
    assert_invalid(valid_yaml.replace("steps:\n  - action: goto", "steps: []\n#"))


def test_unknown_action_fails():
    assert_invalid("name: x\nsteps:\n  - action: hover\n")


def test_click_missing_selector_fails():
    assert_invalid("name: x\nsteps:\n  - action: click\n")


def test_fill_missing_value_fails():
    assert_invalid("name: x\nsteps:\n  - action: fill\n    selector: '#a'\n")


def test_goto_missing_url_fails():
    assert_invalid("name: x\nsteps:\n  - action: goto\n")


def test_illegal_path_fails():
    assert_invalid("name: x\nsteps:\n  - action: screenshot\n    path: ../../secret.txt\n")


def test_mask_sensitive():
    data = mask_sensitive({"password": "abc", "nested": {"token_value": "t", "name": "ok"}})
    assert data["password"] == "***"
    assert data["nested"]["token_value"] == "***"
    assert data["nested"]["name"] == "ok"
