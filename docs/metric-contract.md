# Metric contract (baseline)

This document freezes the exporter’s Prometheus metrics and labels for compatibility testing. Values are **Gauges** unless noted.

## Common labels

- `server_id` — Flussonic instance identifier (from config or `host:port`).
- `stream_name` — Stream name with trailing `_stream` removed when present.

## Metrics

| Name | Labels | Description |
|------|--------|-------------|
| `flussonic_input_errors_count` | `error_type` | Per-type input error counters from API |
| `flussonic_input_bits_count` | — | Input bits (`bytes * 8`) |
| `flussonic_input_warnings_count` | — | Warnings (`invalid_secondary_inputs`) |
| `flussonic_input_sources` | `source` (`primary` / `secondary` / `no_data`) | Seconds per source |
| `flussonic_input_sources_switches` | — | Input switch count |
| `flussonic_dvr_read_performance` | `type` | DVR read segment counts by type |
| `flussonic_dvr_write_performance` | `type` | DVR write segment counts by type |
| `flussonic_play_count` | `protocol`, `resource`, `status` | Play HTTP response counts |
| `flussonic_transcoder_hw` | `hw` | Hardware encoder (value `1`) |
| `flussonic_transcoder_restarts` | — | Restarts |
| `flussonic_transcoder_overloaded` | — | `0` / `1` |
| `flussonic_transcoder_qualities` | — | Qualities count |
| `flussonic_transcoder_frames` | — | Frames processed |
| `flussonic_stream_uptime_miliseconds` | — | **Deprecated spelling**; same value as `flussonic_stream_uptime_milliseconds` |
| `flussonic_stream_uptime_milliseconds` | — | Stream uptime from `stats.lifetime` (ms) |

## Exporter self-metrics (process)

| Name | Labels | Description |
|------|--------|-------------|
| `flussonic_exporter_build_info` | *(Info labels: `version`, `python`)* | Exporter version and Python version |
| `flussonic_exporter_last_success_timestamp_seconds` | `server_id` | Unix time of last successful Flussonic fetch |

## HTTP

- Scrape path: `/metrics`
- Port: `EXPORTER_PORT` (default `9105`)
