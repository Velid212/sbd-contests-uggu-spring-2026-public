"""Integration tests for the src_solution ABU API."""
from __future__ import annotations

import os

import pytest
from fastapi.testclient import TestClient

from src_solution.abu.app import app


@pytest.fixture()
def client() -> TestClient:
    return TestClient(app)


def test_health(client: TestClient) -> None:
    r = client.get("/api/v1/health")
    assert r.status_code == 200
    assert r.json()["status"] == "ok"


def test_mission_flow(client: TestClient) -> None:
    r = client.post("/api/v1/missions", json={"target_depth_m": 2.0, "max_rpm": 250.0})
    assert r.status_code == 200
    mission_id = r.json()["mission_id"]
    for _ in range(10):
        tick = client.post("/api/v1/missions/tick")
        assert tick.status_code == 200
        if tick.json().get("mission", {}).get("status") == "completed":
            break
    st = client.get("/api/v1/status")
    assert st.json()["mission_id"] == mission_id


def test_ai_suggest(client: TestClient) -> None:
    r = client.post("/api/v1/ai/suggest", json={"depth_m": 5.0, "torque_nm": 3000.0})
    assert r.status_code == 200
    assert "suggested_rpm" in r.json()


def test_tick_without_mission(client: TestClient) -> None:
    for route in app.router.routes:
        if getattr(route, "path", "") == "/api/v1/missions/tick":
            route.endpoint.__globals__["_mission"] = None
            break
    r = client.post("/api/v1/missions/tick")
    assert r.status_code == 400


def test_rpm_env_cap(client: TestClient) -> None:
    os.environ["ABU_MAX_RPM"] = "100"
    try:
        client.post("/api/v1/missions", json={"target_depth_m": 1.0})
        tick = client.post("/api/v1/missions/tick")
        assert tick.json()["mission"]["rpm"] <= 100
    finally:
        os.environ.pop("ABU_MAX_RPM", None)
