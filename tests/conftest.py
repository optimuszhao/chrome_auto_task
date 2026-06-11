from __future__ import annotations

import pytest

from app.database import init_db, SessionLocal
from app.models import Flow, Run, RunStepLog, Schedule


@pytest.fixture(autouse=True)
def clean_db():
    init_db()
    db = SessionLocal()
    try:
        db.query(RunStepLog).delete()
        db.query(Run).delete()
        db.query(Schedule).delete()
        db.query(Flow).delete()
        db.commit()
    finally:
        db.close()
    yield
    db = SessionLocal()
    try:
        db.query(RunStepLog).delete()
        db.query(Run).delete()
        db.query(Schedule).delete()
        db.query(Flow).delete()
        db.commit()
    finally:
        db.close()


@pytest.fixture
def db():
    session = SessionLocal()
    try:
        yield session
    finally:
        session.close()


@pytest.fixture
def valid_yaml():
    return """
name: Mock 登录
description: 测试
browser:
  headless: true
variables:
  username: admin
  password: "123456"
steps:
  - action: goto
    url: http://127.0.0.1:8000/mock-site
  - action: fill
    selector: "#username"
    value: "${username}"
  - action: click
    selector: "#loginBtn"
"""
