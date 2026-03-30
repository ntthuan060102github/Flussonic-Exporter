"""Flask application factory."""

from __future__ import annotations

import json

from flask import Flask, Response, request
from prometheus_client import CollectorRegistry, generate_latest

from flussonic_exporter import health


def _wants_json() -> bool:
    if request.args.get("format") == "json":
        return True
    accept = (request.headers.get("Accept") or "").lower()
    return accept.startswith("application/json")


def create_app(registry: CollectorRegistry, server_id: str) -> Flask:
    app = Flask(__name__)

    @app.route("/metrics")
    def metrics() -> Response:
        return Response(generate_latest(registry), mimetype="text/plain; charset=utf-8")

    @app.route("/healthz")
    def healthz() -> Response:
        if _wants_json():
            return Response(
                json.dumps({"status": "ok"}),
                mimetype="application/json",
            )
        return Response("ok\n", mimetype="text/plain; charset=utf-8")

    @app.route("/readyz")
    def readyz() -> Response:
        snap = health.snapshot()
        if _wants_json():
            if health.is_ready():
                body = {
                    "status": "ready",
                    "server_id": server_id,
                    "last_success_timestamp": snap.get("last_success_ts"),
                }
                return Response(json.dumps(body), mimetype="application/json")
            body = {
                "status": "not_ready",
                "server_id": server_id,
                "detail": "no successful Flussonic fetch yet",
                "last_error": snap.get("last_error"),
            }
            return Response(json.dumps(body), status=503, mimetype="application/json")
        if health.is_ready():
            return Response("ready\n", mimetype="text/plain; charset=utf-8")
        return Response(
            "not ready\n",
            status=503,
            mimetype="text/plain; charset=utf-8",
        )

    return app
