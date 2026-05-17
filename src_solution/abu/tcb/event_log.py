from __future__ import annotations

import hashlib
import threading
from collections import deque
from datetime import datetime, timezone
from enum import Enum
from pathlib import Path


class EventLevel(str, Enum):

    INFO = "INFO"
    WARNING = "WARNING"
    ERROR = "ERROR"
    CRITICAL = "CRITICAL"


_RING_SIZE = 10


class EventLog:
    def __init__(self, log_dir: Path | None = None) -> None:
        self._dir = log_dir or Path.cwd() / "var" / "abu_solution_logs"
        self._full_path = self._dir / "abu_events_full.log"
        self._ring_path = self._dir / "abu_events_ring.txt"
        self._ring: deque[str] = deque(maxlen=_RING_SIZE)
        self._lock = threading.Lock()
        self._last_hash = "0" * 64
        try:
            self._dir.mkdir(parents=True, exist_ok=True)
        except OSError:
            pass

    @property
    def last_hash(self) -> str:
        """Current hash-chain head."""
        with self._lock:
            return self._last_hash

    def record(self, level: EventLevel, message: str) -> str:
        """Append an event and return the new hash-chain head."""
        clean = " ".join(str(message).split())[:500]
        ts = datetime.now(timezone.utc).isoformat()
        material = f"{self._last_hash}|{ts}|{level.value}|{clean}".encode("utf-8")
        digest = hashlib.sha256(material).hexdigest()
        line = f"{ts}\t{level.value}\t{clean}\thash={digest}\n"
        with self._lock:
            self._last_hash = digest
            self._ring.append(line.strip())
            try:
                with self._full_path.open("a", encoding="utf-8") as fh:
                    fh.write(line)
                self._ring_path.write_text(
                    "".join(f"{x}\n" for x in self._ring),
                    encoding="utf-8",
                )
            except OSError:
                pass
        return digest

    def ring_snapshot(self) -> list[str]:
        with self._lock:
            return list(self._ring)

    def read_full_tail(self, max_lines: int = 500) -> str:
        if not self._full_path.is_file():
            return ""
        lines = self._full_path.read_text(encoding="utf-8").splitlines()
        return "\n".join(lines[-max_lines:])


default_log = EventLog()
