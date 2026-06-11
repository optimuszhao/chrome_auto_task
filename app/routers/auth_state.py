from __future__ import annotations

from fastapi import APIRouter

from app.database import AUTH_DIR

router = APIRouter(prefix="/api/auth-state", tags=["auth-state"])


@router.get("")
def list_auth_state():
    return {"files": [item.name for item in AUTH_DIR.glob("*.json")]}
