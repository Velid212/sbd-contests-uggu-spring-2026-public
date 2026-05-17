from __future__ import annotations

import multiprocessing as mp
from dataclasses import dataclass
from typing import Any

from src_solution.abu.other.numpy_workflow import smooth_vibration_window
from src_solution.abu.other.pseudo_ai import anomaly_vibration, regime_suggest


@dataclass(frozen=True)
class DomainResponse:
    ok: bool
    value: Any = None
    error: str = ""


def _worker(operation: str, payload: dict[str, Any], queue: mp.Queue) -> None:
    try:
        if operation == "smooth_vibration":
            queue.put(DomainResponse(True, smooth_vibration_window(payload.get("samples", []))))
        elif operation == "suggest_regime":
            queue.put(DomainResponse(True, regime_suggest(payload["depth_m"], payload["torque_nm"])))
        elif operation == "anomaly_vibration":
            queue.put(DomainResponse(True, anomaly_vibration(payload.get("samples", []))))
        else:
            queue.put(DomainResponse(False, error="unknown operation"))
    except Exception as exc:  # pragma: no cover - defensive boundary
        queue.put(DomainResponse(False, error=str(exc)))


class DomainProcess:
    def request(self, operation: str, payload: dict[str, Any], timeout: float = 3.0) -> DomainResponse:
        """Run request/response IPC through multiprocessing.Process."""
        ctx = mp.get_context("fork") if hasattr(mp, "get_context") else mp
        queue: mp.Queue = ctx.Queue()
        process = ctx.Process(target=_worker, args=(operation, payload, queue))
        process.start()
        process.join(timeout)
        if process.is_alive():
            process.terminate()
            process.join(1.0)
            return DomainResponse(False, error="domain timeout")
        if queue.empty():
            return DomainResponse(False, error="empty domain response")
        return queue.get()


default_domain = DomainProcess()
