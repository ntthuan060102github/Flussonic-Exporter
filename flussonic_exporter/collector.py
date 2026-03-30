"""Background collection loop: fetch → parse → metrics."""

from __future__ import annotations

import logging
import time

from prometheus_client import CollectorRegistry

from flussonic_exporter import health
from flussonic_exporter.client import FlussonicClient
from flussonic_exporter.config import Settings
from flussonic_exporter.exporter_self import ExporterSelfMetrics
from flussonic_exporter.metrics import FlussonicMetrics
from flussonic_exporter.parser import parse_streams_payload

logger = logging.getLogger(__name__)


class Collector:
    """Runs the fetch/parse/update cycle for one Flussonic target."""

    def __init__(self, settings: Settings, registry: CollectorRegistry) -> None:
        self._settings = settings
        self._metrics = FlussonicMetrics(registry)
        self._self_metrics = ExporterSelfMetrics(registry, settings.server_id)
        self._client = FlussonicClient(
            url=settings.streams_url,
            username=settings.flussonic_username,
            password=settings.flussonic_password,
            timeout=settings.timeout,
            verify_ssl=settings.verify_ssl,
        )

    @property
    def metrics(self) -> FlussonicMetrics:
        return self._metrics

    def run_once(self) -> None:
        """Single cycle; raises on unrecoverable fetch errors after retries."""
        try:
            data = self._client.fetch_streams_json()
        except Exception as e:
            health.mark_error(str(e))
            logger.error(
                "Failed to fetch streams for server_id=%s url=%s: %s",
                self._settings.server_id,
                self._settings.streams_url,
                e,
                exc_info=True,
            )
            raise
        streams = parse_streams_payload(self._settings.server_id, data)
        self._metrics.update(streams)
        self._self_metrics.record_fetch_success()
        health.mark_success()
        logger.info(
            "Updated metrics for server_id=%s streams=%d",
            self._settings.server_id,
            len(streams),
        )

    def run_forever(self) -> None:
        """Background loop; never returns; logs errors and continues."""
        sid = self._settings.server_id
        url = self._settings.streams_url
        interval = self._settings.fetch_interval
        logger.info("Starting collector for server_id=%s url=%s interval=%ss", sid, url, interval)
        while True:
            try:
                self.run_once()
            except Exception as e:
                health.mark_error(str(e))
                logger.error(
                    "Collector cycle failed for server_id=%s url=%s: %s",
                    sid,
                    url,
                    e,
                    exc_info=True,
                )
            time.sleep(interval)
