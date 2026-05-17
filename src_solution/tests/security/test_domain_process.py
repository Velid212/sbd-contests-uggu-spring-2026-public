"""Тесты безопасности для недоверенных доменов"""
from __future__ import annotations

import pytest

from src_solution.abu.other.domain_process import DomainProcess


@pytest.mark.security
def test_domain_process_request_response() -> None:
    response = DomainProcess().request("suggest_regime", {"depth_m": 5.0, "torque_nm": 1000.0})
    assert response.ok is True
    assert response.value[0] > 0


@pytest.mark.security
def test_domain_process_unknown_operation() -> None:
    response = DomainProcess().request("write_state", {})
    assert response.ok is False
