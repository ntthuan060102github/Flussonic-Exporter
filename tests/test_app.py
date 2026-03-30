"""Flask routes: healthz / readyz content negotiation."""

from __future__ import annotations

import json

from flussonic_exporter import health
from flussonic_exporter.app import create_app
from prometheus_client import CollectorRegistry


def test_readyz_plain_not_ready():
    with health._lock:
        health._state["last_error"] = "test err"
    app = create_app(CollectorRegistry(), "srv-a")
    with app.test_client() as c:
        r = c.get("/readyz")
        assert r.status_code == 503
        assert r.data == b"not ready\n"


def test_readyz_json_ready():
    with health._lock:
        health._state["ready"] = True
        health._state["last_success_ts"] = 12345.5
        health._state["last_error"] = None
    app = create_app(CollectorRegistry(), "srv-a")
    with app.test_client() as c:
        r = c.get("/readyz?format=json")
        assert r.status_code == 200
        data = json.loads(r.data)
        assert data["status"] == "ready"
        assert data["server_id"] == "srv-a"
        assert data["last_success_timestamp"] == 12345.5


def test_readyz_json_not_ready():
    with health._lock:
        health._state["last_error"] = "connection refused"
    app = create_app(CollectorRegistry(), "srv-b")
    with app.test_client() as c:
        r = c.get("/readyz?format=json")
        assert r.status_code == 503
        data = json.loads(r.data)
        assert data["status"] == "not_ready"
        assert data["last_error"] == "connection refused"


def test_healthz_json():
    app = create_app(CollectorRegistry(), "x")
    with app.test_client() as c:
        r = c.get("/healthz?format=json")
        assert r.status_code == 200
        assert json.loads(r.data)["status"] == "ok"
