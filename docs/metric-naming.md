# Metric naming and semantics

This document describes how Flussonic API fields are mapped to Prometheus names and how to interpret types.

## Current model: Gauges

All **Flussonic-derived** series are exposed as **Gauges**. Values are whatever the Flussonic API returns at poll time (often cumulative totals: bytes, counts, seconds). They are **not** Prometheus `Counter` types because:

- The API does not guarantee strict monotonicity across process restarts or server resets.
- Deriving rates is still done in PromQL with `rate()` / `irate()` on suitable series.

## Exporter self-metrics

Metrics prefixed with `flussonic_exporter_` describe the **exporter process**, not individual streams:

| Name | Type | Role |
|------|------|------|
| `flussonic_exporter_build_info` | Info | `version`, `python` |
| `flussonic_exporter_last_success_timestamp_seconds` | Gauge | Unix time of last successful API fetch + metric update (`server_id` label) |

## Naming conventions for future changes

- Prefer **`_total`** suffix for cumulative counters when migrating to true counters or when adding new series that are clearly monotonic.
- Avoid overloading `_count` for non-count semantics; prefer descriptive names (`_seconds`, `_bits`, etc.).
- When renaming for clarity, keep the old name for at least one release or document in [`compatibility.md`](compatibility.md).

## Review list (plan §6)

| Metric | Notes |
|--------|--------|
| `flussonic_input_errors_count` | Per-type error tallies from API; Gauge snapshot. |
| `flussonic_input_sources_switches` | Switch count from API; Gauge. |
| `flussonic_transcoder_restarts` | Restart count; Gauge. |
| `flussonic_play_count` | Play HTTP response tallies keyed by protocol/resource/status; Gauge. |
| `flussonic_stream_uptime_miliseconds` | Deprecated spelling; duplicate of `*_milliseconds`. |

Deep reclassification (Counter vs Gauge) should be done together with API guarantees and a major version bump.
