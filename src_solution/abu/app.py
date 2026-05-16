"""HTTP API of the cyberimmune ABU solution."""
from __future__ import annotations

import os
import uuid
from typing import Any

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field

from src_solution.abu.other.domain_process import default_domain
from src_solution.abu.tcb.event_log import EventLevel, default_log
from src_solution.abu.tcb.safety import (
    clamp_positive,
    enforce_depth_cap,
    enforce_rpm_cap,
    risk_flag,
    should_emergency_stop,
)
from src_solution.abu.tcb.sys.security_monitor import default_monitor

app = FastAPI(title="АБУ solution", version="0.2.0")


class MissionIn(BaseModel):
    """Drilling mission command."""

    target_depth_m: float = Field(gt=0, le=200)
    max_rpm: float = Field(default=300.0, gt=0)


class MissionState(BaseModel):
    """Trusted state of one active mission."""

    mission_id: str
    target_depth_m: float
    depth_m: float = 0.0
    rpm: float = 0.0
    torque_nm: float = 2000.0
    pressure: float = 120.0
    vibration_samples: list[float] = Field(default_factory=list)
    status: str = "running"


_mission: MissionState | None = None


def _call_other(operation: str, payload: dict[str, Any]) -> Any:
    default_monitor.require("tcb_controller", "other_ai" if operation != "smooth_vibration" else "other_numpy", operation, payload)
    response = default_domain.request(operation, payload)
    if not response.ok:
        default_log.record(EventLevel.ERROR, f"domain_failed operation={operation} error={response.error}")
        raise HTTPException(status_code=502, detail="isolated domain failed")
    return response.value


@app.get("/api/v1/health")
def health() -> dict[str, str]:
    """Health endpoint."""
    default_log.record(EventLevel.INFO, "health_check")
    return {"status": "ok", "service": "abu"}


@app.get("/api/v1/events/ring")
def events_ring() -> dict[str, list[str]]:
    """Current audit ring buffer."""
    return {"lines": default_log.ring_snapshot()}


@app.get("/api/v1/events/full")
def events_full_tail() -> dict[str, str]:
    """Tail of the full audit log."""
    return {"log": default_log.read_full_tail()}


@app.get("/api/v1/status")
def status() -> dict[str, Any]:
    """Current telemetry."""
    if _mission is None:
        return {"idle": True}
    m = _mission
    vibration_score = float(_call_other("anomaly_vibration", {"samples": m.vibration_samples})) if m.vibration_samples else 0.0
    risk = risk_flag(vibration_score, m.pressure, m.depth_m)
    return {
        "idle": False,
        "mission_id": m.mission_id,
        "depth_m": m.depth_m,
        "rpm": m.rpm,
        "torque_nm": m.torque_nm,
        "pressure": m.pressure,
        "vibration_score": vibration_score,
        "risk": risk,
        "mission_status": m.status,
    }


@app.post("/api/v1/missions")
def start_mission(body: MissionIn) -> dict[str, Any]:
    """Accept a new mission command after trusted validation."""
    global _mission
    mid = str(uuid.uuid4())
    _mission = MissionState(
        mission_id=mid,
        target_depth_m=body.target_depth_m,
        rpm=min(150.0, body.max_rpm),
    )
    default_log.record(EventLevel.INFO, f"mission_started mission_id={mid} target_depth_m={body.target_depth_m}")
    return {"accepted": True, "mission_id": mid}


@app.get("/api/v1/missions/current")
def current_mission() -> dict[str, Any]:
    """Return current mission or 404."""
    if _mission is None:
        raise HTTPException(status_code=404, detail="нет активной миссии")
    return _mission.model_dump()


@app.post("/api/v1/missions/tick")
def tick_step() -> dict[str, Any]:
    """Simulate one trusted control tick."""
    global _mission
    if _mission is None:
        raise HTTPException(status_code=400, detail="нет миссии")
    m = _mission
    if m.status != "running":
        return {"done": True, "status": m.status}
    m.depth_m = round(min(m.depth_m + 0.5, m.target_depth_m), 2)
    m.vibration_samples.append(0.1 + 0.05 * (m.depth_m % 3))
    smooth = float(_call_other("smooth_vibration", {"samples": m.vibration_samples}))
    default_log.record(EventLevel.INFO, f"tick depth={m.depth_m} smooth_vib={smooth:.4f}")
    m.torque_nm = 2000.0 + m.depth_m * 30.0
    m.pressure = 120.0 + m.depth_m * 0.4
    rpm_suggest, _feed = _call_other("suggest_regime", {"depth_m": m.depth_m, "torque_nm": m.torque_nm})
    env_cap = clamp_positive(os.environ.get("ABU_MAX_RPM", "300"), 300.0)
    m.rpm = min(float(rpm_suggest), env_cap)
    vibration_score = float(_call_other("anomaly_vibration", {"samples": m.vibration_samples}))
    risk = risk_flag(vibration_score, m.pressure, m.depth_m)
    if not enforce_depth_cap(m.depth_m, m.target_depth_m + 1e-6):
        m.status = "stopped_depth"
        default_log.record(EventLevel.WARNING, "mission_stopped_depth_cap")
    if not enforce_rpm_cap(m.rpm, env_cap):
        m.status = "stopped_rpm"
        default_log.record(EventLevel.ERROR, "mission_stopped_rpm_cap")
    if should_emergency_stop(risk, vibration_score):
        m.status = "emergency"
        default_log.record(EventLevel.CRITICAL, "emergency_stop_triggered")
    if m.depth_m >= m.target_depth_m and m.status == "running":
        m.status = "completed"
        default_log.record(EventLevel.INFO, "mission_completed_target_depth")
    return {"mission": m.model_dump(), "risk": risk}


class AISuggestIn(BaseModel):
    """Input for untrusted advisory AI."""

    depth_m: float = Field(ge=0)
    torque_nm: float = Field(ge=0)


@app.post("/api/v1/ai/suggest")
def ai_suggest(body: AISuggestIn) -> dict[str, float]:
    """Return advisory drilling mode from an isolated non-TCB process."""
    rpm, feed = _call_other("suggest_regime", {"depth_m": body.depth_m, "torque_nm": body.torque_nm})
    return {"suggested_rpm": float(rpm), "suggested_feed_mm_rev": float(feed)}
