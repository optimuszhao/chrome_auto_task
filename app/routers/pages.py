from __future__ import annotations

from datetime import date

from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import FileResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.database import AUTH_DIR, BASE_DIR, LOG_DIR, get_db
from app.models import Flow, Run, Schedule
from app.services.run_service import get_run

templates = Jinja2Templates(directory=str(BASE_DIR / "app" / "templates"))
router = APIRouter(tags=["pages"])


@router.get("/")
def dashboard(request: Request, db: Session = Depends(get_db)):
    today = date.today()
    runs_today = db.query(Run).filter(func.date(Run.created_at) == today.isoformat()).count()
    return templates.TemplateResponse(
        "index.html",
        {
            "request": request,
            "flow_count": db.query(Flow).count(),
            "runs_today": runs_today,
            "success_count": db.query(Run).filter(Run.status == "SUCCESS").count(),
            "failed_count": db.query(Run).filter(Run.status == "FAILED").count(),
            "running": db.query(Run).filter(Run.status.in_(["RUNNING", "WAITING_CONFIRM"])).all(),
            "recent_runs": db.query(Run).order_by(Run.created_at.desc()).limit(10).all(),
        },
    )


@router.get("/flows")
def flow_list(request: Request, db: Session = Depends(get_db)):
    flows = db.query(Flow).order_by(Flow.updated_at.desc()).all()
    recent = {run.flow_id: run for run in db.query(Run).order_by(Run.created_at.desc()).all()}
    return templates.TemplateResponse("flow_list.html", {"request": request, "flows": flows, "recent": recent})


@router.get("/flows/new")
def flow_new(request: Request):
    return templates.TemplateResponse("flow_editor.html", {"request": request, "flow": None, "auth_files": auth_files()})


@router.get("/flows/{flow_id}/edit")
def flow_edit(flow_id: int, request: Request, db: Session = Depends(get_db)):
    flow = db.get(Flow, flow_id)
    if not flow:
        raise HTTPException(status_code=404, detail="任务不存在")
    return templates.TemplateResponse("flow_editor.html", {"request": request, "flow": flow, "auth_files": auth_files()})


@router.get("/runs/{run_id}")
def run_detail(run_id: int, request: Request, db: Session = Depends(get_db)):
    run = get_run(db, run_id)
    if not run:
        raise HTTPException(status_code=404, detail="执行记录不存在")
    return templates.TemplateResponse("run_detail.html", {"request": request, "run": run})


@router.get("/schedules")
def schedule_list(request: Request, db: Session = Depends(get_db)):
    return templates.TemplateResponse(
        "schedule_list.html",
        {"request": request, "schedules": db.query(Schedule).all(), "flows": db.query(Flow).all()},
    )


@router.get("/tutorial")
def tutorial(request: Request):
    return templates.TemplateResponse("tutorial.html", {"request": request})


@router.get("/mock-site")
def mock_site(request: Request):
    return templates.TemplateResponse("mock_site.html", {"request": request})


@router.get("/files/{path:path}")
def serve_file(path: str):
    target = (BASE_DIR / path).resolve()
    if not str(target).startswith(str(BASE_DIR.resolve())) or not target.exists():
        raise HTTPException(status_code=404, detail="文件不存在")
    return FileResponse(target)


def auth_files() -> list[str]:
    return [item.name for item in AUTH_DIR.glob("*.json")]
