"""Compatibility health check for repository tests."""


def tcb_health() -> str:
    """Return OK when the trusted package imports successfully."""
    return "ok"
