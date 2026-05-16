"""Security-oriented API tests for ABU solution."""

from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from src_solution.abu.app import app


@pytest.mark.security
def test_solution_mission_flow_records_security_events() -> None:
    client = TestClient(app)
    started = client.post("/api/v1/missions", json={"target_depth_m": 1.0, "max_rpm": 200.0})
    assert started.status_code == 200
    tick = client.post("/api/v1/missions/tick")
    assert tick.status_code == 200
    ring = client.get("/api/v1/events/ring")
    assert any("ipc_allowed" in line or "mission" in line for line in ring.json()["lines"])


@pytest.mark.security
def test_solution_health_status_and_ai_suggest() -> None:
    client = TestClient(app)
    assert client.get("/api/v1/health").json()["status"] == "ok"
    status = client.get("/api/v1/status")
    assert status.status_code == 200
    suggest = client.post("/api/v1/ai/suggest", json={"depth_m": 5.0, "torque_nm": 3000.0})
    assert suggest.status_code == 200
    assert suggest.json()["suggested_rpm"] > 0
