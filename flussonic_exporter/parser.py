"""Parse Flussonic API JSON into internal models."""

from __future__ import annotations

import re
from typing import Any

from flussonic_exporter.models import ParsedStream

PLAY_HTTP_RE = re.compile(
    r"^play_(?P<protocol>[^_]+(?:_[^_]+)?)(?:_(?P<resource>[^_]+))?_http_(?P<status>\d+)$"
)


def _normalize_stream_name(raw: str) -> str:
    return raw.replace("_stream", "") if raw else "unknown"


def parse_streams_payload(server_id: str, data: dict[str, Any]) -> list[ParsedStream]:
    """Parse API response body into a list of ParsedStream."""
    streams_raw = data.get("streams")
    if not isinstance(streams_raw, list):
        return []

    out: list[ParsedStream] = []
    for stream in streams_raw:
        if not isinstance(stream, dict):
            continue
        name = stream.get("name", "unknown")
        if not isinstance(name, str):
            name = "unknown"
        stream_name = _normalize_stream_name(name)
        stats = stream.get("stats", {})
        if not isinstance(stats, dict):
            stats = {}
        input_stats = stats.get("input", {})
        if not isinstance(input_stats, dict):
            input_stats = {}
        transcoder_stats = stats.get("transcoder", {})
        if not isinstance(transcoder_stats, dict):
            transcoder_stats = {}

        error_by_type = {
            "errors": float(input_stats.get("errors", 0)),
            "errors_lost_packets": float(input_stats.get("errors_lost_packets", 0)),
            "errors_decoder_reset": float(input_stats.get("errors_decoder_reset", 0)),
            "errors_broken_payload": float(input_stats.get("errors_broken_payload", 0)),
            "errors_dropped_frames": float(input_stats.get("errors_dropped_frames", 0)),
            "errors_desync": float(input_stats.get("errors_desync", 0)),
            "errors_ts_pat": float(input_stats.get("errors_ts_pat", 0)),
            "errors_ts_service_lost": float(input_stats.get("errors_ts_service_lost", 0)),
            "errors_ts_stuck_restarts": float(input_stats.get("errors_ts_stuck_restarts", 0)),
            "errors_ts_jump_restarts": float(input_stats.get("errors_ts_jump_restarts", 0)),
            "errors_404": float(input_stats.get("errors_404", 0)),
            "errors_403": float(input_stats.get("errors_403", 0)),
            "errors_500": float(input_stats.get("errors_500", 0)),
            "errors_crashed": float(input_stats.get("errors_crashed", 0)),
            "resync_count_drift": float(input_stats.get("resync_count_drift", 0)),
            "resync_count_jump": float(input_stats.get("resync_count_jump", 0)),
            "resync_count_normal": float(input_stats.get("resync_count_normal", 0)),
            "reorder_count": float(input_stats.get("reorder_count", 0)),
            "invalid_secondary_inputs": float(input_stats.get("invalid_secondary_inputs", 0)),
        }

        bytes_in = float(input_stats.get("bytes", 0))
        warnings = float(input_stats.get("invalid_secondary_inputs", 0))
        source_seconds = {
            "primary": float(input_stats.get("num_sec_on_primary_input", 0)),
            "secondary": float(input_stats.get("num_sec_on_secondary_input", 0)),
            "no_data": float(input_stats.get("num_sec_no_data", 0)),
        }
        input_switches = float(input_stats.get("input_switches", 0))

        play_http: list[tuple[str, str, str, float]] = []
        play_stats = stats.get("play", {})
        if isinstance(play_stats, dict):
            for key, value in play_stats.items():
                if not isinstance(key, str):
                    continue
                if isinstance(value, (int, float)):
                    m = PLAY_HTTP_RE.match(key)
                    if m:
                        protocol = m.group("protocol")
                        resource = m.group("resource") or "unknown"
                        status = m.group("status")
                        play_http.append((protocol, resource, status, float(value)))

        dvr_read: dict[str, float] = {}
        dvr_read_raw = stats.get("dvr_read_performance", {})
        if isinstance(dvr_read_raw, dict):
            for seg_type in ("segments_read_fast", "segments_read_slow", "segments_read_delayed"):
                seg_data = dvr_read_raw.get(seg_type, {})
                if isinstance(seg_data, dict):
                    total = (
                        float(seg_data.get("ram", 0))
                        + float(seg_data.get("cache", 0))
                        + float(seg_data.get("local", 0))
                        + float(seg_data.get("remote", 0))
                    )
                else:
                    total = 0.0
                dvr_read[seg_type.replace("segments_read_", "")] = total
            dvr_read["enoent"] = float(dvr_read_raw.get("segments_read_enoent", 0))
            dvr_read["failed"] = float(dvr_read_raw.get("segments_read_failed", 0))

        dvr_write: dict[str, float] = {}
        dvr_write_raw = stats.get("dvr_write", {})
        if isinstance(dvr_write_raw, dict):
            for metric_key, type_name in [
                ("segments_written_fast", "fast"),
                ("segments_written_slow", "slow"),
                ("segments_written_delayed", "delayed"),
                ("segments_written_collapsed", "collapsed"),
                ("segments_failed", "failed"),
                ("segments_skipped", "skipped"),
                ("segments_discontinuity", "discontinuity"),
            ]:
                dvr_write[type_name] = float(dvr_write_raw.get(metric_key, 0))

        hw = transcoder_stats.get("hw", "unknown")
        if not isinstance(hw, str):
            hw = str(hw)

        ps = ParsedStream(
            server_id=server_id,
            stream_name=stream_name,
            error_by_type=error_by_type,
            input_bits=bytes_in * 8.0,
            warnings=warnings,
            source_seconds=source_seconds,
            input_switches=input_switches,
            play_http=play_http,
            dvr_read=dvr_read,
            dvr_write=dvr_write,
            transcoder_hw=hw,
            transcoder_restarts=float(transcoder_stats.get("restarts", 0)),
            transcoder_overloaded=1.0 if stats.get("transcoder_overloaded", False) else 0.0,
            transcoder_qualities=float(transcoder_stats.get("qualities", 0)),
            transcoder_frames=float(transcoder_stats.get("frames", 0)),
            lifetime_ms=float(stats.get("lifetime", 0)),
        )
        out.append(ps)

    return out
