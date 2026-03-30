"""Prometheus metrics that describe the exporter process (not Flussonic streams)."""

from __future__ import annotations

import sys
import time

from prometheus_client import CollectorRegistry, Gauge, Info

from flussonic_exporter import __version__


class ExporterSelfMetrics:
    """Registers build info and last-success timestamp for operational visibility."""

    def __init__(self, registry: CollectorRegistry, server_id: str) -> None:
        self._server_id = server_id
        self._last_success = Gauge(
            "flussonic_exporter_last_success_timestamp_seconds",
            "Unix timestamp of the last successful Flussonic API fetch and metric update",
            ["server_id"],
            registry=registry,
        )
        self._build = Info(
            "flussonic_exporter_build",
            "Exporter build metadata",
            registry=registry,
        )
        self._build.info(
            {
                "version": __version__,
                "python": f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}",
            }
        )

    def record_fetch_success(self) -> None:
        self._last_success.labels(server_id=self._server_id).set(time.time())
