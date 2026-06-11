from __future__ import annotations

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

from app.database import BASE_DIR, init_db
from app.routers import auth_state, flows, pages, runs, schedules
from app.scheduler import shutdown_scheduler, start_scheduler


@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    start_scheduler()
    yield
    shutdown_scheduler()


app = FastAPI(title="内网浏览器自动化编排平台", lifespan=lifespan)
app.mount("/static", StaticFiles(directory=str(BASE_DIR / "app" / "static")), name="static")

app.include_router(pages.router)
app.include_router(flows.router)
app.include_router(runs.router)
app.include_router(schedules.router)
app.include_router(auth_state.router)
