"""Trusted safety invariants for drilling missions."""
from __future__ import annotations

from typing import Literal

RiskLevel = Literal["low", "medium", "high"]


def clamp_positive(value: float, fallback: float) -> float:
    """Return value when it is a positive number, otherwise fallback."""
    try:
        number = float(value)
    except (TypeError, ValueError):
        return fallback
    return number if number > 0 else fallback


def enforce_depth_cap(depth_m: float, max_depth_m: float) -> bool:
    """Allow motion only while depth is within the target cap."""
    return float(depth_m) <= float(max_depth_m)


def enforce_rpm_cap(rpm: float, max_rpm: float) -> bool:
    """Allow rotation only while RPM is within the configured cap."""
    return float(rpm) <= float(max_rpm)


def risk_flag(vibration: float, pressure: float, depth_m: float) -> RiskLevel:
    """Trusted risk classifier with explicit thresholds."""
    score = 0
    if vibration > 0.75:
        score += 2
    if pressure > 180.0:
        score += 2
    if depth_m > 95.0:
        score += 1
    if score >= 3:
        return "high"
    if score >= 1:
        return "medium"
    return "low"


def should_emergency_stop(
    risk_level: str,
    vibration_values,
    vib_threshold: float = 0.9,
) -> bool:
    if risk_level.lower() == "high":
        return True

    if isinstance(vibration_values, (int, float)):
        return float(vibration_values) >= vib_threshold

    return any(float(v) >= vib_threshold for v in vibration_values)
