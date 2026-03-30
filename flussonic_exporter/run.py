"""CLI entry: validate config, logging, start collector + HTTP server."""

from __future__ import annotations

import logging
import sys

from prometheus_client import CollectorRegistry

from flussonic_exporter.app import create_app
from flussonic_exporter.collector import Collector
from flussonic_exporter.config import ConfigError, load_settings
from flussonic_exporter.logging_config import setup_logging
from flussonic_exporter.scheduler import start_collector_thread

logger = logging.getLogger(__name__)


def main() -> None:
    try:
        settings = load_settings()
    except ConfigError as e:
        sys.stderr.write(f"Configuration error: {e}\n")
        raise SystemExit(1) from e

    setup_logging(settings.log_level)
    registry = CollectorRegistry()
    collector = Collector(settings, registry)
    start_collector_thread(collector)

    app = create_app(registry, settings.server_id)
    logger.info(
        "Exporter listening on 0.0.0.0:%s (metrics /metrics, health /healthz, ready /readyz)",
        settings.exporter_port,
    )
    app.run(host="0.0.0.0", port=settings.exporter_port, threaded=True)


if __name__ == "__main__":
    main()
