"""Background thread for the collector loop."""

from __future__ import annotations

import logging
import threading

from flussonic_exporter.collector import Collector

logger = logging.getLogger(__name__)


def start_collector_thread(collector: Collector) -> threading.Thread:
    t = threading.Thread(target=collector.run_forever, name="flussonic-collector", daemon=True)
    t.start()
    logger.info("Collector thread started")
    return t
