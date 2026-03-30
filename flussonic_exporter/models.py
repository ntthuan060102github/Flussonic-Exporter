"""Internal representations of parsed stream stats (no Prometheus imports)."""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class ParsedStream:
    """One stream’s stats, ready for metric mapping."""

    server_id: str
    stream_name: str
    error_by_type: dict[str, float] = field(default_factory=dict)
    input_bits: float = 0.0
    warnings: float = 0.0
    source_seconds: dict[str, float] = field(default_factory=dict)
    input_switches: float = 0.0
    play_http: list[tuple[str, str, str, float]] = field(default_factory=list)
    dvr_read: dict[str, float] = field(default_factory=dict)
    dvr_write: dict[str, float] = field(default_factory=dict)
    transcoder_hw: str = "unknown"
    transcoder_restarts: float = 0.0
    transcoder_overloaded: float = 0.0
    transcoder_qualities: float = 0.0
    transcoder_frames: float = 0.0
    lifetime_ms: float = 0.0
