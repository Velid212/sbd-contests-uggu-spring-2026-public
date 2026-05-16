"""Untrusted pseudo-AI heuristics kept outside the TCB."""
from __future__ import annotations


def anomaly_vibration(samples: list[float]) -> float:
    """Calculate a bounded anomaly score for the last vibration samples."""
    if not samples:
        return 1.0
    if len(samples) == 1:
        return 0.0
    window = [float(x) for x in samples[-5:]]
    mean = sum(window) / len(window)
    spread = max(abs(x - mean) for x in window) or 1e-9
    raw = abs(window[-1] - mean) / spread
    return max(0.0, min(1.0, raw))


def regime_suggest(depth_m: float, torque_nm: float) -> tuple[float, float]:
    """Return recommended RPM and feed. This is advisory, not trusted."""
    rpm = 120.0 + min(float(depth_m) * 2.0, 80.0)
    if float(torque_nm) > 5000.0:
        rpm *= 0.85
    feed = 0.2 + min(float(depth_m) * 0.01, 0.15)
    return round(rpm, 1), round(feed, 3)
