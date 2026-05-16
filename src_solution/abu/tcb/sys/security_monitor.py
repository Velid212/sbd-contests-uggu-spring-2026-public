"""Reference monitor for trusted/untrusted domain messages."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from src_solution.abu.tcb.event_log import EventLevel, EventLog, default_log


@dataclass(frozen=True)
class PolicyDecision:
    """Result of a policy check."""

    allowed: bool
    reason: str


class SecurityMonitor:
    """Validate request/response traffic at the TCB boundary."""

    def __init__(self, policies: dict[str, set[str]], log: EventLog | None = None) -> None:
        self._policies = policies
        self._log = log or default_log

    def check(self, source: str, target: str, operation: str, payload: dict[str, Any]) -> PolicyDecision:
        """Authorize a cross-domain request using static policy and payload guards."""
        edge = f"{source}->{target}"
        allowed_ops = self._policies.get(edge, set())
        if operation not in allowed_ops:
            self._log.record(EventLevel.WARNING, f"deny edge={edge} operation={operation}")
            return PolicyDecision(False, "operation is not allowed by IPC policy")
        if operation == "suggest_regime" and float(payload.get("depth_m", 0.0)) > 200.0:
            self._log.record(EventLevel.WARNING, "deny suggest_regime depth out of range")
            return PolicyDecision(False, "depth is out of range")
        if operation == "smooth_vibration" and len(payload.get("samples", [])) > 100:
            self._log.record(EventLevel.WARNING, "deny smooth_vibration too many samples")
            return PolicyDecision(False, "too many samples")
        self._log.record(EventLevel.INFO, f"allow edge={edge} operation={operation}")
        return PolicyDecision(True, "allowed")

    def require(self, source: str, target: str, operation: str, payload: dict[str, Any]) -> None:
        """Raise PermissionError when a request is denied."""
        decision = self.check(source, target, operation, payload)
        if not decision.allowed:
            raise PermissionError(decision.reason)


DEFAULT_POLICIES: dict[str, set[str]] = {
    "tcb_controller->other_ai": {"suggest_regime", "anomaly_vibration"},
    "tcb_controller->other_numpy": {"smooth_vibration"},
}


default_monitor = SecurityMonitor(DEFAULT_POLICIES)
