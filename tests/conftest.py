"""Shared pytest fixtures."""

from __future__ import annotations

import pytest
from flussonic_exporter import health


@pytest.fixture(autouse=True)
def reset_health_state():
    with health._lock:
        health._state["ready"] = False
        health._state["last_success_ts"] = None
        health._state["last_error"] = None
    yield
    with health._lock:
        health._state["ready"] = False
        health._state["last_success_ts"] = None
        health._state["last_error"] = None
