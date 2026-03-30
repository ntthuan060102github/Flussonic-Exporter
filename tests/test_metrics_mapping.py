import json
from pathlib import Path

from flussonic_exporter.metrics import FlussonicMetrics
from flussonic_exporter.parser import parse_streams_payload
from prometheus_client import CollectorRegistry, generate_latest

FIXTURE = Path(__file__).parent / "fixtures" / "flussonic_streams_response.json"


def test_stale_stream_removed_from_text():
    data = json.loads(FIXTURE.read_text())
    registry = CollectorRegistry()
    m = FlussonicMetrics(registry)
    streams = parse_streams_payload("srv1", data)
    m.update(streams)
    text1 = generate_latest(registry).decode()
    assert 'stream_name="demo"' in text1
    assert "flussonic_stream_uptime_milliseconds" in text1

    m.update([])
    text2 = generate_latest(registry).decode()
    assert 'stream_name="demo"' not in text2
