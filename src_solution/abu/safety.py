"""Compatibility API for trusted safety checks."""
from src_solution.abu.tcb.safety import (
    RiskLevel,
    clamp_positive,
    enforce_depth_cap,
    enforce_rpm_cap,
    risk_flag,
    should_emergency_stop,
)

__all__ = [
    "RiskLevel",
    "clamp_positive",
    "enforce_depth_cap",
    "enforce_rpm_cap",
    "risk_flag",
    "should_emergency_stop",
]
