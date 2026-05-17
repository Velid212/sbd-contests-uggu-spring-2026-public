
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

def test_coverage_wrappers_and_domain_process() -> None:
    from src_solution.abu.event_log import EventLevel, EventLog
    from src_solution.abu.numpy_workflow import smooth_vibration_window
    from src_solution.abu.other.domain_process import DomainProcess

    log = EventLog()
    log.record(EventLevel.INFO, "coverage")
    assert log.ring_snapshot()

    assert isinstance(smooth_vibration_window([1.0, 2.0, 3.0]), float)

    result = DomainProcess().request("unknown", {})
    assert result.ok is False
    assert "unknown" in result.error


def test_coverage_extra_app_routes() -> None:
    from fastapi.testclient import TestClient
    from src_solution.abu.app import app

    client = TestClient(app)

    assert client.get("/api/v1/health").status_code == 200
    assert client.get("/api/v1/events/ring").status_code == 200
    assert client.get("/api/v1/events/full").status_code == 200
    assert client.get("/api/v1/status").status_code == 200

    r = client.post("/api/v1/ai/suggest", json={"depth_m": 10.0, "torque_nm": 2000.0})
    assert r.status_code == 200

def test_coverage_current_mission_and_completed_tick() -> None:
    from fastapi.testclient import TestClient
    from src_solution.abu.app import app

    client = TestClient(app)

    r = client.post("/api/v1/missions", json={"target_depth_m": 0.5, "max_rpm": 150.0})
    assert r.status_code == 200

    current = client.get("/api/v1/missions/current")
    assert current.status_code == 200

    tick1 = client.post("/api/v1/missions/tick")
    assert tick1.status_code == 200

    tick2 = client.post("/api/v1/missions/tick")
    assert tick2.status_code == 200
    assert tick2.json().get("done") is True


def test_coverage_call_other_failure(monkeypatch) -> None:
    from fastapi.testclient import TestClient
    from src_solution.abu import app as app_module
    from src_solution.abu.app import app
    from src_solution.abu.other.domain_process import DomainResponse

    class FailingDomain:
        def request(self, operation, payload):
            return DomainResponse(False, error="forced")

    monkeypatch.setattr(app_module, "default_domain", FailingDomain())

    client = TestClient(app)
    response = client.post("/api/v1/ai/suggest", json={"depth_m": 1.0, "torque_nm": 1.0})

    assert response.status_code == 502


def test_coverage_domain_worker_direct_branches() -> None:
    import multiprocessing as mp
    from src_solution.abu.other.domain_process import DomainResponse, _worker

    for operation, payload in [
        ("smooth_vibration", {"samples": [1.0, 2.0, 3.0]}),
        ("suggest_regime", {"depth_m": 1.0, "torque_nm": 100.0}),
        ("anomaly_vibration", {"samples": [0.1, 0.2, 0.3]}),
    ]:
        queue = mp.Queue()
        _worker(operation, payload, queue)
        result = queue.get(timeout=1.0)
        assert isinstance(result, DomainResponse)
        assert result.ok is True

def test_coverage_tick_emergency_branches(monkeypatch) -> None:
    from fastapi.testclient import TestClient
    from src_solution.abu import app as app_module
    from src_solution.abu.app import app
    from src_solution.abu.other.domain_process import DomainResponse

    class EmergencyDomain:
        def request(self, operation, payload):
            if operation == "smooth_vibration":
                return DomainResponse(True, 0.99)
            if operation == "suggest_regime":
                return DomainResponse(True, (999.0, 0.1))
            if operation == "anomaly_vibration":
                return DomainResponse(True, 0.99)
            return DomainResponse(False, error="unknown")

    monkeypatch.setattr(app_module, "default_domain", EmergencyDomain())
    monkeypatch.setenv("ABU_MAX_RPM", "100")

    client = TestClient(app)
    r = client.post("/api/v1/missions", json={"target_depth_m": 10.0, "max_rpm": 300.0})
    assert r.status_code == 200

    tick = client.post("/api/v1/missions/tick")
    assert tick.status_code == 200
    assert tick.json()["mission"]["status"] in {"emergency", "stopped_rpm"}