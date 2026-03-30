"""Process readiness and last-fetch state for probes."""

from __future__ import annotations

import threading
import time
from typing import Any

_lock = threading.Lock()
_state: dict[str, Any] = {
    "ready": False,
    "last_success_ts": None,
    "last_error": None,
}


def mark_success() -> None:
    with _lock:
        _state["ready"] = True
        _state["last_success_ts"] = time.time()
        _state["last_error"] = None


def mark_error(message: str) -> None:
    with _lock:
        _state["last_error"] = message


def snapshot() -> dict[str, Any]:
    with _lock:
        return dict(_state)


def is_ready() -> bool:
    with _lock:
        return bool(_state["ready"])
