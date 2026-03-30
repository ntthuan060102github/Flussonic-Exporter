import json
from pathlib import Path

from flussonic_exporter.parser import PLAY_HTTP_RE, parse_streams_payload

FIXTURE = Path(__file__).parent / "fixtures" / "flussonic_streams_response.json"


def test_play_http_regex():
    m = PLAY_HTTP_RE.match("play_hls_http_200")
    assert m is not None
    assert m.group("protocol") == "hls"
    assert m.group("resource") is None
    assert m.group("status") == "200"


def test_parse_fixture():
    data = json.loads(FIXTURE.read_text())
    streams = parse_streams_payload("srv1", data)
    assert len(streams) == 1
    s = streams[0]
    assert s.server_id == "srv1"
    assert s.stream_name == "demo"
    assert s.input_bits == 1024 * 8
    assert s.error_by_type["errors_lost_packets"] == 1.0
    assert any(p == "hls" and st == "200" for p, _r, st, v in s.play_http)
    assert s.transcoder_hw == "nvenc"


def test_parse_empty_streams():
    assert parse_streams_payload("x", {}) == []
    assert parse_streams_payload("x", {"streams": None}) == []
