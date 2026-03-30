"""Prometheus metric definitions and mapping from parsed streams."""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING

from prometheus_client import CollectorRegistry, Gauge

if TYPE_CHECKING:
    from flussonic_exporter.models import ParsedStream

logger = logging.getLogger(__name__)

LABELS = ["server_id", "stream_name"]


class LabelTracker:
    """Remove stale labeled series when label sets change between updates."""

    def __init__(self) -> None:
        self._last: dict[int, set[tuple]] = {}

    def sync(self, gauge: Gauge, new_keys: set[tuple]) -> None:
        gid = id(gauge)
        old = self._last.get(gid, set())
        for t in old - new_keys:
            try:
                gauge.remove(*t)
            except KeyError:
                logger.debug("remove skipped for gauge labels=%s", t)
        self._last[gid] = new_keys


class FlussonicMetrics:
    """Registers all exporter gauges and applies ParsedStream updates with stale cleanup."""

    def __init__(self, registry: CollectorRegistry) -> None:
        self.registry = registry
        self._tracker = LabelTracker()

        self.input_errors_count = Gauge(
            "flussonic_input_errors_count",
            "Input errors count by error type",
            LABELS + ["error_type"],
            registry=registry,
        )
        self.input_bits_count = Gauge(
            "flussonic_input_bits_count",
            "Input bits received (bytes * 8)",
            LABELS,
            registry=registry,
        )
        self.input_warnings_count = Gauge(
            "flussonic_input_warnings_count",
            "Input warnings count (invalid_secondary_inputs)",
            LABELS,
            registry=registry,
        )
        self.input_sources = Gauge(
            "flussonic_input_sources",
            "Seconds active on each input source (primary, secondary, no_data)",
            LABELS + ["source"],
            registry=registry,
        )
        self.input_sources_switches = Gauge(
            "flussonic_input_sources_switches",
            "Number of input source switches",
            LABELS,
            registry=registry,
        )
        self.dvr_read_performance = Gauge(
            "flussonic_dvr_read_performance",
            "DVR read performance segments count by type",
            LABELS + ["type"],
            registry=registry,
        )
        self.dvr_write_performance = Gauge(
            "flussonic_dvr_write_performance",
            "DVR write performance segments count by type",
            LABELS + ["type"],
            registry=registry,
        )
        self.play_count = Gauge(
            "flussonic_play_count",
            "Play HTTP responses count by protocol, resource type and status code",
            LABELS + ["protocol", "resource", "status"],
            registry=registry,
        )
        self.transcoder_hw = Gauge(
            "flussonic_transcoder_hw",
            "Transcoder hardware encoder type (1 = present)",
            LABELS + ["hw"],
            registry=registry,
        )
        self.transcoder_restarts = Gauge(
            "flussonic_transcoder_restarts",
            "Transcoder restart count",
            LABELS,
            registry=registry,
        )
        self.transcoder_overloaded = Gauge(
            "flussonic_transcoder_overloaded",
            "Transcoder overloaded (1=yes, 0=no)",
            LABELS,
            registry=registry,
        )
        self.transcoder_qualities = Gauge(
            "flussonic_transcoder_qualities",
            "Transcoder qualities count",
            LABELS,
            registry=registry,
        )
        self.transcoder_frames = Gauge(
            "flussonic_transcoder_frames",
            "Transcoder frames processed",
            LABELS,
            registry=registry,
        )
        self.stream_uptime_miliseconds = Gauge(
            "flussonic_stream_uptime_miliseconds",
            "Stream uptime in miliseconds (from stats.lifetime) [deprecated spelling]",
            LABELS,
            registry=registry,
        )
        self.stream_uptime_milliseconds = Gauge(
            "flussonic_stream_uptime_milliseconds",
            "Stream uptime in milliseconds (from stats.lifetime)",
            LABELS,
            registry=registry,
        )

    def _collect_label_keys(self, streams: list[ParsedStream]) -> dict[str, set[tuple]]:
        keys_err: set[tuple] = set()
        keys_bits: set[tuple] = set()
        keys_warn: set[tuple] = set()
        keys_src: set[tuple] = set()
        keys_sw: set[tuple] = set()
        keys_dvr_r: set[tuple] = set()
        keys_dvr_w: set[tuple] = set()
        keys_play: set[tuple] = set()
        keys_hw: set[tuple] = set()
        keys_tr: set[tuple] = set()
        keys_ov: set[tuple] = set()
        keys_q: set[tuple] = set()
        keys_f: set[tuple] = set()
        keys_up_old: set[tuple] = set()
        keys_up_new: set[tuple] = set()

        for s in streams:
            sid, sn = s.server_id, s.stream_name
            for et in s.error_by_type:
                keys_err.add((sid, sn, et))
            keys_bits.add((sid, sn))
            keys_warn.add((sid, sn))
            for src in s.source_seconds:
                keys_src.add((sid, sn, src))
            keys_sw.add((sid, sn))
            for t, _v in s.dvr_read.items():
                keys_dvr_r.add((sid, sn, t))
            for t, _v in s.dvr_write.items():
                keys_dvr_w.add((sid, sn, t))
            for proto, res, st, _v in s.play_http:
                keys_play.add((sid, sn, proto, res, st))
            keys_hw.add((sid, sn, s.transcoder_hw))
            keys_tr.add((sid, sn))
            keys_ov.add((sid, sn))
            keys_q.add((sid, sn))
            keys_f.add((sid, sn))
            keys_up_old.add((sid, sn))
            keys_up_new.add((sid, sn))

        return {
            "err": keys_err,
            "bits": keys_bits,
            "warn": keys_warn,
            "src": keys_src,
            "sw": keys_sw,
            "dvr_r": keys_dvr_r,
            "dvr_w": keys_dvr_w,
            "play": keys_play,
            "hw": keys_hw,
            "tr": keys_tr,
            "ov": keys_ov,
            "q": keys_q,
            "f": keys_f,
            "up_old": keys_up_old,
            "up_new": keys_up_new,
        }

    def _sync_all_trackers(self, k: dict[str, set[tuple]]) -> None:
        self._tracker.sync(self.input_errors_count, k["err"])
        self._tracker.sync(self.input_bits_count, k["bits"])
        self._tracker.sync(self.input_warnings_count, k["warn"])
        self._tracker.sync(self.input_sources, k["src"])
        self._tracker.sync(self.input_sources_switches, k["sw"])
        self._tracker.sync(self.dvr_read_performance, k["dvr_r"])
        self._tracker.sync(self.dvr_write_performance, k["dvr_w"])
        self._tracker.sync(self.play_count, k["play"])
        self._tracker.sync(self.transcoder_hw, k["hw"])
        self._tracker.sync(self.transcoder_restarts, k["tr"])
        self._tracker.sync(self.transcoder_overloaded, k["ov"])
        self._tracker.sync(self.transcoder_qualities, k["q"])
        self._tracker.sync(self.transcoder_frames, k["f"])
        self._tracker.sync(self.stream_uptime_miliseconds, k["up_old"])
        self._tracker.sync(self.stream_uptime_milliseconds, k["up_new"])

    def _apply_stream(self, s: ParsedStream) -> None:
        sid, sn = s.server_id, s.stream_name
        for et, val in s.error_by_type.items():
            self.input_errors_count.labels(sid, sn, et).set(val)
        self.input_bits_count.labels(sid, sn).set(s.input_bits)
        self.input_warnings_count.labels(sid, sn).set(s.warnings)
        for src, sec in s.source_seconds.items():
            self.input_sources.labels(sid, sn, src).set(sec)
        self.input_sources_switches.labels(sid, sn).set(s.input_switches)
        for t, val in s.dvr_read.items():
            self.dvr_read_performance.labels(sid, sn, t).set(val)
        for t, val in s.dvr_write.items():
            self.dvr_write_performance.labels(sid, sn, t).set(val)
        for proto, res, st, val in s.play_http:
            self.play_count.labels(sid, sn, proto, res, st).set(val)
        self.transcoder_hw.labels(sid, sn, s.transcoder_hw).set(1)
        self.transcoder_restarts.labels(sid, sn).set(s.transcoder_restarts)
        self.transcoder_overloaded.labels(sid, sn).set(s.transcoder_overloaded)
        self.transcoder_qualities.labels(sid, sn).set(s.transcoder_qualities)
        self.transcoder_frames.labels(sid, sn).set(s.transcoder_frames)
        self.stream_uptime_miliseconds.labels(sid, sn).set(s.lifetime_ms)
        self.stream_uptime_milliseconds.labels(sid, sn).set(s.lifetime_ms)

    def update(self, streams: list[ParsedStream]) -> None:
        """Sync all gauges from parsed streams; remove series for disappeared streams/labels."""
        keys = self._collect_label_keys(streams)
        self._sync_all_trackers(keys)
        for s in streams:
            self._apply_stream(s)
