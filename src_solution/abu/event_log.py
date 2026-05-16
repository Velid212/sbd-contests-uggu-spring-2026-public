"""Compatibility re-export for tests and API modules."""
from src_solution.abu.tcb.event_log import EventLevel, EventLog, default_log

__all__ = ["EventLevel", "EventLog", "default_log"]
