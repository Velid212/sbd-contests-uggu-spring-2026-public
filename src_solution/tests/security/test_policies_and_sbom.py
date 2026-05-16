"""Security tests for policies and SBOM split."""
from __future__ import annotations

import json
from pathlib import Path

import pytest

from src_solution.abu.tcb.sys.security_monitor import DEFAULT_POLICIES



def _find_file(*candidates: str) -> Path:
    here = Path(__file__).resolve()
    for parent in here.parents:
        for rel in candidates:
            p = parent / rel
            if p.is_file():
                return p
    raise FileNotFoundError(candidates)


@pytest.mark.security
def test_ipc_policies_have_small_tcb_interface() -> None:
    policies = json.loads(_find_file("src_solution/abu/tcb/sys/ipc_policies.json", "abu/tcb/sys/ipc_policies.json").read_text(encoding="utf-8"))
    assert len(policies["allows"]) == 2
    assert DEFAULT_POLICIES["tcb_controller->other_numpy"] == {"smooth_vibration"}
    assert {entry["from"] for entry in policies["allows"]} == {"tcb_controller"}


@pytest.mark.security
def test_numpy_is_not_in_tcb_sbom() -> None:
    tcb = json.loads(_find_file("src_solution/sbom/SBOM_TCB.cdx.json", "../sbom/SBOM_TCB.cdx.json").read_text(encoding="utf-8"))
    other = json.loads(_find_file("src_solution/sbom/SBOM_OTHER.cdx.json", "../sbom/SBOM_OTHER.cdx.json").read_text(encoding="utf-8"))
    assert "numpy" not in json.dumps(tcb).lower()
    assert "numpy" in json.dumps(other).lower()
