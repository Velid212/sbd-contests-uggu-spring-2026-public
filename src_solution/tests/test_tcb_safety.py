"""Tests for trusted safety checks."""
from __future__ import annotations

from src_solution.abu.tcb.safety import (
    clamp_positive,
    enforce_depth_cap,
    enforce_rpm_cap,
    risk_flag,
    should_emergency_stop,
)


def test_depth_and_rpm_caps() -> None:
    assert enforce_depth_cap(10.0, 20.0) is True
    assert enforce_depth_cap(21.0, 20.0) is False
    assert enforce_rpm_cap(100.0, 200.0) is True
    assert enforce_rpm_cap(300.0, 200.0) is False


def test_risk_flag_and_stop() -> None:
    assert risk_flag(0.1, 100.0, 10.0) == "low"
    assert risk_flag(0.8, 100.0, 10.0) == "medium"
    assert risk_flag(0.9, 200.0, 100.0) == "high"
    assert should_emergency_stop("high", 0.1) is True
    assert should_emergency_stop("low", 0.95) is True


def test_clamp_positive() -> None:
    assert clamp_positive("bad", 10.0) == 10.0
    assert clamp_positive(-1.0, 10.0) == 10.0
    assert clamp_positive(5.0, 10.0) == 5.0
