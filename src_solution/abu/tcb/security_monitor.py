"""Default-deny security monitor for domain IPC requests/responses."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Any

from src_solution.abu.tcb.event_log import EventLevel, EventLog, default_log


class Domain(str, Enum):
    """Execution domains separated by trust level."""

    TCB_CONTROLLER = "tcb_controller"
    OTHER_AI = "other_ai"
    OTHER_NUMPY = "other_numpy"
    HTTP_ADAPTER = "http_adapter"
    EVENT_LOG = "event_log"


@dataclass(frozen=True)
class Request:
    """IPC request inspected by the monitor."""

    source: Domain
    target: Domain
    operation: str
    payload: dict[str, Any]


@dataclass(frozen=True)
class Response:
    """IPC response returned after monitor decision."""

    allowed: bool
    reason: str


@dataclass(frozen=True)
class PolicyRule:
    """One allow-list rule. Absence of a match means deny."""

    source: Domain
    target: Domain
    operations: tuple[str, ...]


DEFAULT_POLICIES: tuple[PolicyRule, ...] = (
    PolicyRule(Domain.HTTP_ADAPTER, Domain.TCB_CONTROLLER, ("start_mission", "tick", "status")),
    PolicyRule(Domain.TCB_CONTROLLER, Domain.EVENT_LOG, ("record", "read")),
    PolicyRule(Domain.TCB_CONTROLLER, Domain.OTHER_AI, ("suggest_regime",)),
    PolicyRule(Domain.TCB_CONTROLLER, Domain.OTHER_NUMPY, ("smooth_vibration",)),
)


class SecurityMonitor:
    """Mediates all cross-domain calls with explicit policies."""

    def __init__(
        self,
        policies: tuple[PolicyRule, ...] = DEFAULT_POLICIES,
        event_log: EventLog = default_log,
    ) -> None:
        self._policies = policies
        self._event_log = event_log

    def authorize(self, request: Request) -> Response:
        """Return allow/deny decision and write a security event."""
        for rule in self._policies:
            if (
                request.source == rule.source
                and request.target == rule.target
                and request.operation in rule.operations
            ):
                self._event_log.record(
                    EventLevel.INFO,
                    "ipc_allowed "
                    f"source={request.source.value} target={request.target.value} "
                    f"operation={request.operation}",
                )
                return Response(True, "policy allow")
        self._event_log.record(
            EventLevel.WARNING,
            "ipc_denied "
            f"source={request.source.value} target={request.target.value} "
            f"operation={request.operation}",
        )
        return Response(False, "default deny")

    def require(self, request: Request) -> None:
        """Raise PermissionError for denied IPC request."""
        response = self.authorize(request)
        if not response.allowed:
            raise PermissionError(response.reason)


security_monitor = SecurityMonitor()
