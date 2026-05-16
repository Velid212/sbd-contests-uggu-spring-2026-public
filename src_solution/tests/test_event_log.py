"""Tests for trusted event_log."""
from __future__ import annotations

from src_solution.abu.event_log import EventLevel, EventLog


def test_ring_maxlen(tmp_path) -> None:
    log = EventLog(tmp_path)
    for i in range(12):
        log.record(EventLevel.INFO, f"event-{i}")
    assert len(log.ring_snapshot()) == 10


def test_record_contains_hash(tmp_path) -> None:
    log = EventLog(tmp_path)
    digest = log.record(EventLevel.WARNING, "policy warning")
    snap = log.ring_snapshot()
    assert digest in snap[0]
    assert "WARNING" in snap[0]


def test_full_tail(tmp_path) -> None:
    log = EventLog(tmp_path)
    log.record(EventLevel.ERROR, "error1")
    log.record(EventLevel.CRITICAL, "error2")
    tail = log.read_full_tail()
    assert "error1" in tail
    assert "error2" in tail
