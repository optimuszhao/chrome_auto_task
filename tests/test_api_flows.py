from __future__ import annotations

from fastapi.testclient import TestClient

from app.main import app


def test_pages_return_200():
    with TestClient(app) as client:
        assert client.get("/flows").status_code == 200
        assert client.get("/tutorial").status_code == 200
        assert client.get("/mock-site").status_code == 200


def test_create_and_validate_flow(valid_yaml):
    with TestClient(app) as client:
        res = client.post("/api/flows", json={"yaml_content": valid_yaml})
        assert res.status_code == 200
        flow_id = res.json()["id"]
        res = client.post(f"/api/flows/{flow_id}/validate", json={"yaml_content": valid_yaml})
        assert res.status_code == 200


def test_validate_invalid_yaml_returns_400(valid_yaml):
    with TestClient(app) as client:
        res = client.post("/api/flows", json={"yaml_content": valid_yaml})
        flow_id = res.json()["id"]
        res = client.post(f"/api/flows/{flow_id}/validate", json={"yaml_content": "name: x\nsteps: []"})
        assert res.status_code == 400
