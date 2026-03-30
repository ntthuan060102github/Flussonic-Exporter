"""Exporter self-metrics (build info, last success)."""

from __future__ import annotations

from flussonic_exporter.exporter_self import ExporterSelfMetrics
from prometheus_client import CollectorRegistry, generate_latest


def test_build_info_and_last_success_in_registry():
    reg = CollectorRegistry()
    sm = ExporterSelfMetrics(reg, "test-srv")
    sm.record_fetch_success()
    text = generate_latest(reg).decode()
    assert "flussonic_exporter_build_info" in text
    assert "flussonic_exporter_last_success_timestamp_seconds" in text
    assert 'server_id="test-srv"' in text
