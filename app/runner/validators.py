from __future__ import annotations

import json
import os
import re
from pathlib import Path
from typing import Any

import yaml

from app.database import BASE_DIR

SUPPORTED_ACTIONS = {
    "goto": ["url"],
    "click": ["selector"],
    "fill": ["selector", "value"],
    "wait": ["selector"],
    "sleep": ["seconds"],
    "screenshot": [],
    "assert_text": ["text"],
    "assert_visible": ["selector"],
    "select": ["selector", "value"],
    "upload": ["selector", "file_path"],
    "download": ["selector"],
    "manual_confirm": ["message"],
}
SENSITIVE_KEYS = ("password", "token", "secret", "cookie", "authorization")


class FlowValidationError(ValueError):
    pass


def parse_yaml(yaml_content: str) -> dict[str, Any]:
    try:
        data = yaml.safe_load(yaml_content)
    except yaml.YAMLError as exc:
        raise FlowValidationError(f"YAML 格式错误: {exc}") from exc
    if not isinstance(data, dict):
        raise FlowValidationError("YAML 顶层必须是对象")
    return data


def _safe_project_path(value: str) -> None:
    if not isinstance(value, str):
        raise FlowValidationError("path 必须是字符串")
    raw = Path(value)
    blocked_prefixes = ("/etc", "/var", "/System", "/Library", "/Users", "C:\\Windows")
    if raw.is_absolute() and not str(raw.resolve()).startswith(str(BASE_DIR.resolve())):
        raise FlowValidationError(f"路径必须位于项目目录内: {value}")
    resolved = (BASE_DIR / raw).resolve()
    if not str(resolved).startswith(str(BASE_DIR.resolve())):
        raise FlowValidationError(f"路径禁止跳出项目目录: {value}")
    if str(raw).startswith(blocked_prefixes):
        raise FlowValidationError(f"路径禁止读取系统敏感目录: {value}")


def validate_flow_yaml(yaml_content: str) -> dict[str, Any]:
    data = parse_yaml(yaml_content)
    if not data.get("name"):
        raise FlowValidationError("name 必填")
    steps = data.get("steps")
    if not isinstance(steps, list) or not steps:
        raise FlowValidationError("steps 必须是非空数组")
    browser = data.get("browser", {}) or {}
    if not isinstance(browser, dict):
        raise FlowValidationError("browser 必须是对象")
    variables = data.get("variables", {}) or {}
    if not isinstance(variables, dict):
        raise FlowValidationError("variables 必须是对象")

    for index, step in enumerate(steps):
        if not isinstance(step, dict):
            raise FlowValidationError(f"第 {index + 1} 步必须是对象")
        action = step.get("action")
        if not action:
            raise FlowValidationError(f"第 {index + 1} 步缺少 action")
        if action not in SUPPORTED_ACTIONS:
            raise FlowValidationError(f"不支持的 action: {action}")
        for field in SUPPORTED_ACTIONS[action]:
            if step.get(field) in (None, ""):
                raise FlowValidationError(f"{action} 缺少必填字段 {field}")
        for text_field in ("selector", "url", "path", "save_as", "file_path", "text", "value"):
            if text_field in step and step[text_field] is not None and not isinstance(step[text_field], (str, int, float, bool)):
                raise FlowValidationError(f"{text_field} 类型错误")
        if "timeout" in step and not isinstance(step["timeout"], (int, float)):
            raise FlowValidationError("timeout 必须是数字")
        if action == "sleep" and not isinstance(step.get("seconds"), (int, float)):
            raise FlowValidationError("sleep seconds 必须是数字")
        for path_field in ("path", "save_as", "file_path"):
            if step.get(path_field):
                _safe_project_path(str(step[path_field]))
    return data


def substitute_variables(value: Any, variables: dict[str, Any]) -> Any:
    if not isinstance(value, str):
        return value

    def replace(match: re.Match[str]) -> str:
        key = match.group(1)
        return str(os.environ.get(key, variables.get(key, "")))

    return re.sub(r"\$\{([A-Za-z_][A-Za-z0-9_]*)\}", replace, value)


def mask_sensitive(value: Any) -> Any:
    if isinstance(value, dict):
        masked: dict[str, Any] = {}
        for key, item in value.items():
            if any(s in key.lower() for s in SENSITIVE_KEYS):
                masked[key] = "***"
            else:
                masked[key] = mask_sensitive(item)
        return masked
    if isinstance(value, list):
        return [mask_sensitive(item) for item in value]
    return value


def safe_json(data: Any) -> str:
    return json.dumps(mask_sensitive(data), ensure_ascii=False, default=str)
