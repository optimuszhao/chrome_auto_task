from __future__ import annotations

from pathlib import Path
from typing import Any

from playwright.async_api import Page

from app.database import BASE_DIR, LOG_DIR


def resolve_project_path(path_value: str | None, fallback: str) -> Path:
    target = Path(path_value or fallback)
    if not target.is_absolute():
        target = BASE_DIR / target
    target = target.resolve()
    target.parent.mkdir(parents=True, exist_ok=True)
    return target


async def execute_action(page: Page, step: dict[str, Any], run_id: int, step_index: int) -> str | None:
    action = step["action"]
    timeout = int(step.get("timeout", 10000))
    if action == "goto":
        await page.goto(str(step["url"]), wait_until="domcontentloaded", timeout=timeout)
    elif action == "click":
        await page.locator(str(step["selector"])).click(timeout=timeout)
    elif action == "fill":
        await page.locator(str(step["selector"])).fill(str(step["value"]), timeout=timeout)
    elif action == "wait":
        await page.locator(str(step["selector"])).wait_for(state="visible", timeout=timeout)
    elif action == "sleep":
        await page.wait_for_timeout(int(float(step["seconds"]) * 1000))
    elif action == "screenshot":
        path = resolve_project_path(step.get("path"), f"logs/run-{run_id}-step-{step_index}.png")
        await page.screenshot(path=str(path), full_page=True)
        return str(path.relative_to(BASE_DIR))
    elif action == "assert_text":
        await page.get_by_text(str(step["text"])).first.wait_for(timeout=timeout)
    elif action == "assert_visible":
        await page.locator(str(step["selector"])).wait_for(state="visible", timeout=timeout)
    elif action == "select":
        await page.locator(str(step["selector"])).select_option(str(step["value"]), timeout=timeout)
    elif action == "upload":
        await page.locator(str(step["selector"])).set_input_files(str(resolve_project_path(str(step["file_path"]), "")), timeout=timeout)
    elif action == "download":
        path = resolve_project_path(step.get("save_as"), f"logs/downloads/run-{run_id}-step-{step_index}.bin")
        async with page.expect_download(timeout=timeout) as download_info:
            await page.locator(str(step["selector"])).click(timeout=timeout)
        download = await download_info.value
        await download.save_as(str(path))
        return str(path.relative_to(BASE_DIR))
    return None


async def failure_screenshot(page: Page, run_id: int, step_index: int | str) -> str:
    path = LOG_DIR / f"run-{run_id}-failed-{step_index}.png"
    await page.screenshot(path=str(path), full_page=True)
    return str(path.relative_to(BASE_DIR))
