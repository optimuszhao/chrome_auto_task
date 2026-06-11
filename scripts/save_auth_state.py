from __future__ import annotations

import asyncio
import sys
from pathlib import Path

from playwright.async_api import async_playwright

ROOT = Path(__file__).resolve().parent.parent
AUTH_DIR = ROOT / "playwright" / ".auth"


async def main() -> None:
    if len(sys.argv) < 3:
        print("Usage: python scripts/save_auth_state.py <login_url> <name.json>")
        raise SystemExit(1)
    login_url = sys.argv[1]
    name = sys.argv[2]
    if not name.endswith(".json"):
        name = f"{name}.json"
    AUTH_DIR.mkdir(parents=True, exist_ok=True)
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False)
        context = await browser.new_context()
        page = await context.new_page()
        await page.goto(login_url)
        input("请在浏览器完成登录，然后回车保存登录态...")
        await context.storage_state(path=str(AUTH_DIR / name))
        await browser.close()
    print(f"saved: playwright/.auth/{name}")


if __name__ == "__main__":
    asyncio.run(main())
