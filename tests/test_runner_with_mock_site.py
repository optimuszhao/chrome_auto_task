from __future__ import annotations

import asyncio
import subprocess
import sys
import time
from pathlib import Path

import pytest
import yaml

from app.database import BASE_DIR
from app.models import Run
from app.schemas import FlowCreate
from app.services.flow_service import create_flow
from app.services.run_service import create_run
from app.runner.playwright_runner import run_flow_async


def wait_for_server(url: str) -> None:
    import urllib.request

    for _ in range(50):
        try:
            urllib.request.urlopen(url, timeout=1)
            return
        except Exception:
            time.sleep(0.2)
    raise RuntimeError("server did not start")


@pytest.mark.e2e
def test_runner_success_with_mock_site(db):
    proc = subprocess.Popen([sys.executable, "-m", "uvicorn", "app.main:app", "--port", "8010"], cwd=BASE_DIR)
    try:
        wait_for_server("http://127.0.0.1:8010/mock-site")
        yaml_content = Path(BASE_DIR / "flows/examples/mock_login_and_submit.yaml").read_text()
        data = yaml.safe_load(yaml_content)
        data["steps"][0]["url"] = "http://127.0.0.1:8010/mock-site"
        yaml_content = yaml.safe_dump(data, allow_unicode=True, sort_keys=False)
        flow = create_flow(db, FlowCreate(yaml_content=yaml_content))
        run = create_run(db, flow.id)
        asyncio.run(run_flow_async(flow.id, run.id))
        db.refresh(run)
        run = db.get(Run, run.id)
        assert run.status == "SUCCESS"
        assert len(run.step_logs) == len(data["steps"])
        assert (BASE_DIR / "logs/mock-before-submit.png").exists()
    finally:
        proc.terminate()
        proc.wait(timeout=10)


@pytest.mark.e2e
def test_runner_failed_saves_screenshot(db):
    proc = subprocess.Popen([sys.executable, "-m", "uvicorn", "app.main:app", "--port", "8011"], cwd=BASE_DIR)
    try:
        wait_for_server("http://127.0.0.1:8011/mock-site")
        yaml_content = """
name: fail case
browser:
  headless: true
steps:
  - action: goto
    url: http://127.0.0.1:8011/mock-site
  - action: assert_text
    text: 永远不会出现
    timeout: 500
"""
        flow = create_flow(db, FlowCreate(yaml_content=yaml_content))
        run = create_run(db, flow.id)
        asyncio.run(run_flow_async(flow.id, run.id))
        db.refresh(run)
        run = db.get(Run, run.id)
        assert run.status == "FAILED"
        assert run.step_logs[-1].screenshot_path
        assert (BASE_DIR / run.step_logs[-1].screenshot_path).exists()
    finally:
        proc.terminate()
        proc.wait(timeout=10)
