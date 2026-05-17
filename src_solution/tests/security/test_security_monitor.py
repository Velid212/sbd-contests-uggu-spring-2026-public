"""Тесты политик IPC"""
from __future__ import annotations

import pytest

from src_solution.abu.tcb.event_log import EventLog
from src_solution.abu.tcb.sys.security_monitor import DEFAULT_POLICIES, SecurityMonitor


@pytest.mark.security
def test_security_monitor_allows_declared_request(tmp_path) -> None:
    monitor = SecurityMonitor(DEFAULT_POLICIES, EventLog(tmp_path))
    decision = monitor.check(
        "tcb_controller",
        "other_ai",
        "suggest_regime",
        {"depth_m": 10.0, "torque_nm": 1000.0},
    )
    assert decision.allowed is True


@pytest.mark.security
def test_security_monitor_denies_unknown_operation(tmp_path) -> None:
    monitor = SecurityMonitor(DEFAULT_POLICIES, EventLog(tmp_path))
    decision = monitor.check("other_ai", "tcb_controller", "write_state", {})
    assert decision.allowed is False
    assert "not allowed" in decision.reason


@pytest.mark.security
def test_security_monitor_payload_guard(tmp_path) -> None:
    monitor = SecurityMonitor(DEFAULT_POLICIES, EventLog(tmp_path))
    decision = monitor.check(
        "tcb_controller",
        "other_ai",
        "suggest_regime",
        {"depth_m": 250.0, "torque_nm": 1000.0},
    )
    assert decision.allowed is False
