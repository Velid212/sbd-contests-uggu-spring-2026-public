"""Unit tests for trusted ABU modules."""

from __future__ import annotations

from src_solution.abu.tcb.pseudo_ai import anomaly_vibration, regime_suggest, risk_flag
from src_solution.abu.tcb.safety import enforce_depth_cap, enforce_rpm_cap, should_emergency_stop


def test_safety_caps_and_stop_rules() -> None:
    assert enforce_depth_cap(10.0, 20.0)
    assert not enforce_depth_cap(21.0, 20.0)
    assert enforce_rpm_cap(100.0, 200.0)
    assert not enforce_rpm_cap(250.0, 200.0)
    assert should_emergency_stop("high", [])
    assert should_emergency_stop("low", [0.0, 0.0, 1.0], vib_threshold=0.5)


def test_tcb_heuristics_are_deterministic() -> None:
    assert anomaly_vibration([]) == 1.0
    assert anomaly_vibration([1.0]) == 0.0
    assert anomaly_vibration([1.0, 1.0, 5.0]) >= 0.0
    low_rpm, low_feed = regime_suggest(0.0, 1000.0)
    deep_rpm, deep_feed = regime_suggest(20.0, 1000.0)
    assert deep_rpm >= low_rpm
    assert deep_feed >= low_feed
    assert risk_flag(0.9, 200.0, 100.0) == "high"
    assert risk_flag(0.7, 120.0, 10.0) == "medium"
    assert risk_flag(0.1, 120.0, 10.0) == "low"
