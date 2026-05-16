"""Small trusted deterministic heuristics used to validate untrusted suggestions."""

from __future__ import annotations

from typing import Literal

RiskLevel = Literal["low", "medium", "high"]


def anomaly_vibration(samples: list[float]) -> float:
    """Return normalized latest-sample deviation in the range [0, 1]."""
    if not samples:
        return 1.0
    if len(samples) == 1:
        return 0.0
    window = samples[-5:]
    mean = sum(window) / len(window)
    spread = max(abs(x - mean) for x in window) or 1e-9
    return max(0.0, min(1.0, abs(window[-1] - mean) / spread))


def regime_suggest(depth_m: float, torque_nm: float) -> tuple[float, float]:
    """Deterministic safe baseline for RPM/feed suggestions."""
    rpm = 120.0 + min(max(depth_m, 0.0) * 2.0, 80.0)
    if torque_nm > 5000:
        rpm *= 0.85
    feed = 0.2 + min(max(depth_m, 0.0) * 0.01, 0.15)
    return round(rpm, 1), round(feed, 3)


def risk_flag(vibration: float, pressure: float, depth_m: float) -> RiskLevel:
    """Classify risk using transparent thresholds."""
    if vibration >= 0.85 and pressure >= 180.0 and depth_m >= 80.0:
        return "high"
    if vibration >= 0.6 or pressure >= 160.0:
        return "medium"
    return "low"
