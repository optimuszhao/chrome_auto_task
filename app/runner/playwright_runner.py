from __future__ import annotations

import asyncio
from datetime import datetime
from time import perf_counter
from typing import Any

from playwright.async_api import async_playwright
from sqlalchemy.orm import Session

from app.database import AUTH_DIR, BASE_DIR, SessionLocal
from app.models import Flow, Run
from app.runner.actions import execute_action, failure_screenshot
from app.runner.validators import substitute_variables, validate_flow_yaml
from app.services.log_service import create_step_log, finish_step_log

flow_locks: dict[int, asyncio.Lock] = {}
confirm_events: dict[int, asyncio.Event] = {}
cancelled_runs: set[int] = set()


def _lock_for(flow_id: int) -> asyncio.Lock:
    if flow_id not in flow_locks:
        flow_locks[flow_id] = asyncio.Lock()
    return flow_locks[flow_id]


def continue_run(run_id: int) -> None:
    event = confirm_events.get(run_id)
    if event:
        event.set()


def cancel_run(run_id: int) -> None:
    cancelled_runs.add(run_id)
    event = confirm_events.get(run_id)
    if event:
        event.set()


def _materialize_step(step: dict[str, Any], variables: dict[str, Any]) -> dict[str, Any]:
    return {key: substitute_variables(value, variables) for key, value in step.items()}


async def run_flow_async(flow_id: int, run_id: int, start_step: int = 0) -> None:
    db = SessionLocal()
    try:
        flow = db.get(Flow, flow_id)
        run = db.get(Run, run_id)
        if not flow or not run:
            return
        config = validate_flow_yaml(flow.yaml_content)
        variables = config.get("variables", {}) or {}
        browser_config = config.get("browser", {}) or {}

        lock = _lock_for(flow_id)
        async with lock:
            run.status = "RUNNING"
            run.started_at = run.started_at or datetime.utcnow()
            db.add(run)
            db.commit()
            started = perf_counter()

            async with async_playwright() as p:
                launch_options = {
                    "headless": bool(browser_config.get("headless", True)),
                    "slow_mo": int(browser_config.get("slow_mo", 0) or 0),
                }
                browser = await p.chromium.launch(**launch_options)
                storage_state = browser_config.get("storage_state")
                context_options: dict[str, Any] = {"accept_downloads": True}
                if storage_state:
                    state_path = AUTH_DIR / str(storage_state)
                    if not state_path.exists():
                        state_path = (BASE_DIR / str(storage_state)).resolve()
                    context_options["storage_state"] = str(state_path)
                context = await browser.new_context(**context_options)
                page = await context.new_page()

                try:
                    steps = config["steps"]
                    index = start_step
                    while index < len(steps):
                        if run_id in cancelled_runs:
                            run.status = "CANCELLED"
                            break
                        raw_step = steps[index]
                        step = _materialize_step(raw_step, variables)
                        run.current_step_index = index
                        db.add(run)
                        db.commit()

                        if step["action"] == "manual_confirm":
                            run.status = "WAITING_CONFIRM"
                            db.add(run)
                            db.commit()
                            event = asyncio.Event()
                            confirm_events[run_id] = event
                            await event.wait()
                            confirm_events.pop(run_id, None)
                            if run_id in cancelled_runs:
                                run.status = "CANCELLED"
                                break
                            run.status = "RUNNING"
                            index += 1
                            db.add(run)
                            db.commit()
                            continue

                        log, step_started = create_step_log(db, run_id, index, step)
                        try:
                            screenshot_path = await execute_action(page, step, run_id, index)
                            finish_step_log(db, log, step_started, "SUCCESS", screenshot_path=screenshot_path)
                        except Exception as exc:
                            shot = await failure_screenshot(page, run_id, index)
                            finish_step_log(db, log, step_started, "FAILED", screenshot_path=shot, error=str(exc))
                            run.status = "FAILED"
                            run.error_message = str(exc)
                            break
                        index += 1
                    if run.status == "RUNNING":
                        run.status = "SUCCESS"
                finally:
                    await context.close()
                    await browser.close()
                    run.ended_at = datetime.utcnow()
                    run.duration_ms = int((perf_counter() - started) * 1000)
                    db.add(run)
                    db.commit()
                    cancelled_runs.discard(run_id)
    except Exception as exc:
        run = db.get(Run, run_id)
        if run:
            run.status = "FAILED"
            run.error_message = str(exc)
            run.ended_at = datetime.utcnow()
            db.add(run)
            db.commit()
    finally:
        db.close()


def run_flow_background(flow_id: int, run_id: int) -> None:
    asyncio.run(run_flow_async(flow_id, run_id))
