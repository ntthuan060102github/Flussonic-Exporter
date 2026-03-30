# Flussonic Prometheus Exporter

A lightweight [Prometheus](https://prometheus.io/) exporter for **Flussonic Media Server**. It polls the Flussonic HTTP API (`GET /flussonic/api/v3/streams`), maps per-stream statistics to Prometheus gauges, and serves them on `/metrics` for scraping by Prometheus, Grafana, or compatible stacks.

## Table of contents

- [Purpose](#purpose)
- [Features](#features)
- [Architecture](#architecture-overview)
- [Project layout](#project-layout)
- [Configuration](#configuration)
- [Run locally](#run-locally)
- [Docker](#docker)
- [Docker Compose](#docker-compose)
- [HTTP endpoints](#http-endpoints)
- [Metric catalog](#metric-catalog)
- [Labels](#labels)
- [Prometheus scrape config](#prometheus-scrape-configuration)
- [Example PromQL queries](#example-promql-queries)
- [Known limitations](#known-limitations)
- [Migration notes](#migration-notes)
- [Documentation files](#documentation-files)
- [Grafana example](#grafana-example-dashboard)
- [Development](#development)
- [Contributing](#contributing)
- [Star History](#star-history)

## Purpose

Operators need **open, scrapable metrics** from Flussonic (input health, play HTTP stats, DVR, transcoder, uptime) in one place. This exporter bridges Flussonic’s JSON API and Prometheus text exposition so you can alert and dashboard without proprietary agents. It is designed for **one Flussonic server per exporter process**; use distinct `FLUSSONIC_SERVER_ID` values when you run multiple exporters and scrape them all from Prometheus.

## Features

- Polls the Flussonic API (up to 200 streams per request).
- Maps input, play, DVR, transcoder, and stream uptime metrics (see [Metric catalog](#metric-catalog)).
- Validates configuration at startup; structured logging instead of prints.
- Stale series cleanup when streams disappear from the API response.
- `/healthz` (liveness) and `/readyz` (readiness after first successful fetch); JSON variants via `?format=json` or `Accept: application/json`.
- Exporter self-metrics (`flussonic_exporter_build_info`, `flussonic_exporter_last_success_timestamp_seconds`).
- Optional `.env` loading via `python-dotenv`.

## Architecture overview

```text
Flussonic API  --->  Exporter (Flask + prometheus_client)  --->  Prometheus  --->  Grafana
```

1. A background thread fetches JSON on `FLUSSONIC_FETCH_INTERVAL`.
2. Response is parsed into internal models (no Flask/Prometheus coupling in the parser).
3. Gauges in a dedicated `CollectorRegistry` are updated; old label sets are removed when streams or dimensions disappear.
4. Exporter self-metrics (`flussonic_exporter_*`) record build info and the last successful fetch time.
5. Flask exposes `generate_latest(registry)` at `/metrics`.

## Project layout

```text
flussonic_exporter/   # Python package
  app.py              # Routes: /metrics, /healthz, /readyz
  config.py           # Environment + validation
  logging_config.py
  client.py           # HTTP + retries
  models.py           # Parsed stream dataclasses
  parser.py           # JSON → models
  metrics.py          # Gauges + label sync
  collector.py        # Fetch → parse → update loop
  scheduler.py
  health.py
  exporter_self.py    # Build info + last-success timestamp metrics
  run.py              # Entrypoint
main.py               # Shim: python main.py
deploy/prometheus/    # Optional Compose: Prometheus scrape config
examples/grafana/     # Sample Grafana dashboard JSON
docs/                 # Contract, naming, compatibility, migration
tests/                # pytest + fixtures
```

## Configuration

| Variable | Description | Default |
|----------|-------------|---------|
| `FLUSSONIC_IP` | Flussonic host or IP | *(required)* |
| `FLUSSONIC_PORT` | API port | `80` |
| `FLUSSONIC_USERNAME` | HTTP Basic user | *(required)* |
| `FLUSSONIC_PASSWORD` | HTTP Basic password | *(required)* |
| `FLUSSONIC_SERVER_ID` | Value for `server_id` label | `{IP}:{PORT}` |
| `FLUSSONIC_FETCH_INTERVAL` | Poll interval (seconds) | `5` |
| `FLUSSONIC_SCHEME` | `http` or `https` (overrides `FLUSSONIC_HTTPS` when set) | — |
| `FLUSSONIC_HTTPS` | `true` → HTTPS if scheme not set | `false` |
| `FLUSSONIC_TIMEOUT` | Request timeout (seconds) | `5` |
| `FLUSSONIC_VERIFY_SSL` | Verify TLS | `true` |
| `EXPORTER_PORT` | Listen port | `9105` |
| `LOG_LEVEL` | e.g. `INFO`, `DEBUG` | `INFO` |

Details: [`docs/current-env.md`](docs/current-env.md).

## Run locally

```bash
pip install -r requirements.txt
export FLUSSONIC_IP=127.0.0.1
export FLUSSONIC_PORT=80
export FLUSSONIC_USERNAME=admin
export FLUSSONIC_PASSWORD=your_password
python main.py
# or: python -m flussonic_exporter
```

Metrics: `http://localhost:9105/metrics` (or your `EXPORTER_PORT`).

### Tests

```bash
pip install -r requirements-dev.txt
pytest tests/
```

## Docker

```bash
docker build -t flussonic-exporter .
docker run -p 9105:9105 \
  -e FLUSSONIC_IP=... \
  -e FLUSSONIC_USERNAME=... \
  -e FLUSSONIC_PASSWORD=... \
  flussonic-exporter
```

Image entrypoint: `python -m flussonic_exporter`. A `HEALTHCHECK` calls `/healthz`. The process runs as a **non-root** user (`uid` 1000) after `pip install` and file copy.

## Docker Compose

For local or lab use, the repo includes [`docker-compose.yml`](docker-compose.yml).

1. Copy environment template and edit secrets:

   ```bash
   cp .env.example .env
   # edit .env — set FLUSSONIC_IP, FLUSSONIC_USERNAME, FLUSSONIC_PASSWORD, etc.
   ```

2. Start **only the exporter**:

   ```bash
   docker compose up -d
   ```

   Scrape `http://localhost:9105/metrics` (host port follows `EXPORTER_PORT`).

3. Optional **Prometheus** sidecar (profile `monitoring`) to scrape the exporter by service name:

   ```bash
   docker compose --profile monitoring up -d
   ```

   Prometheus UI: `http://localhost:9090` (override host port with `PROMETHEUS_PORT`). The bundled config is [`deploy/prometheus/prometheus.yml`](deploy/prometheus/prometheus.yml).

`depends_on: service_healthy` waits until the exporter passes its Docker healthcheck (HTTP `/healthz`), not until Flussonic is reachable; `/readyz` still reflects a successful API fetch.

## HTTP endpoints

| Path | Purpose |
|------|---------|
| `/metrics` | Prometheus scrape target |
| `/healthz` | Liveness. Plain text `ok` by default; JSON with `?format=json` or `Accept: application/json` |
| `/readyz` | Readiness — `503` until at least one successful Flussonic fetch. Plain text `ready` / `not ready`, or JSON with `?format=json` / `Accept: application/json` including `server_id`, `last_success_timestamp`, `last_error` |

Use JSON readiness in Kubernetes probes when you need timestamps for debugging (`httpGet` with header `Accept: application/json` and optional `?format=json`).

## Metric catalog

All series use **Gauges** with values as reported by Flussonic (often cumulative). Use `rate()` / `irate()` for per-second rates where appropriate.

| Metric | Extra labels | Description |
|--------|--------------|-------------|
| `flussonic_input_errors_count` | `error_type` | Per-type input error counters |
| `flussonic_input_bits_count` | — | Total input bits (`bytes × 8`) |
| `flussonic_input_warnings_count` | — | Warnings (`invalid_secondary_inputs`) |
| `flussonic_input_sources` | `source` | Seconds on `primary` / `secondary` / `no_data` |
| `flussonic_input_sources_switches` | — | Input switch count |
| `flussonic_dvr_read_performance` | `type` | DVR read segments by type |
| `flussonic_dvr_write_performance` | `type` | DVR write segments by type |
| `flussonic_play_count` | `protocol`, `resource`, `status` | Play HTTP response counts |
| `flussonic_transcoder_hw` | `hw` | HW encoder (`1` on that label) |
| `flussonic_transcoder_restarts` | — | Restarts |
| `flussonic_transcoder_overloaded` | — | `0` / `1` |
| `flussonic_transcoder_qualities` | — | Qualities count |
| `flussonic_transcoder_frames` | — | Frames processed |
| `flussonic_stream_uptime_miliseconds` | — | Deprecated spelling; same as below |
| `flussonic_stream_uptime_milliseconds` | — | Uptime from `stats.lifetime` (ms) |

**Exporter (process)**

| Metric | Extra labels | Description |
|--------|--------------|-------------|
| `flussonic_exporter_build_info` | Info: `version`, `python` | Exporter and Python version |
| `flussonic_exporter_last_success_timestamp_seconds` | `server_id` | Unix time of last successful API fetch |

Common labels on stream metrics: `server_id`, `stream_name`. Full contract: [`docs/metric-contract.md`](docs/metric-contract.md). Naming notes: [`docs/metric-naming.md`](docs/metric-naming.md).

## Labels

- `server_id` — From `FLUSSONIC_SERVER_ID` or `{IP}:{PORT}`.
- `stream_name` — Name with a `_stream` suffix removed when present.

Additional dimensions: `error_type`, `protocol`, `resource`, `status`, `source`, `type`, `hw` — see table above.

## Prometheus scrape configuration

```yaml
scrape_configs:
  - job_name: flussonic_exporter
    scrape_interval: 15s
    static_configs:
      - targets: ["localhost:9105"]
```

Kubernetes: point `targets` at the exporter Service or use Pod discovery; align `scrape_interval` with how often you need fresh rates (exporter polls Flussonic on `FLUSSONIC_FETCH_INTERVAL` independently).

## Example PromQL queries

Replace `demo` with your `stream_name` label value as needed.

**Approximate input bitrate (bits/s)** from cumulative bits:

```promql
rate(flussonic_input_bits_count{stream_name="demo"}[5m])
```

**Input errors per second** for a given `error_type`:

```promql
rate(flussonic_input_errors_count{stream_name="demo", error_type="errors_lost_packets"}[5m])
```

**Transcoder overloaded** (alert when `1`):

```promql
flussonic_transcoder_overloaded{stream_name="demo"} == 1
```

**Stream uptime (milliseconds)** — use the correctly spelled metric:

```promql
flussonic_stream_uptime_milliseconds{stream_name="demo"}
```

**Stale fetch detection (exporter vs Flussonic)** — seconds since last successful poll:

```promql
time() - flussonic_exporter_last_success_timestamp_seconds
```

## Known limitations

- **Single Flussonic target per process** — no built-in multi-server list; run one exporter per server or fork the project for multi-target.
- **API limit** — requests use `limit=200` streams; more streams require a code or API change.
- **Gauges, not counters** — values mirror the API; monotonicity is not guaranteed across resets; use `rate()` with care on noisy series.
- **Credentials in env** — use secrets management (Kubernetes Secrets, Docker secrets) in production.
- **TLS** — self-signed Flussonic certs require `FLUSSONIC_VERIFY_SSL=false` (understand the risk) or a proper trust store.
- **Readiness** — `/readyz` needs one successful fetch; if Flussonic is permanently down, readiness stays false while `/healthz` stays true.

## Migration notes

Renamed uptime series and policy: [`docs/migration-notes.md`](docs/migration-notes.md), [`docs/compatibility.md`](docs/compatibility.md).

## Documentation files

| File | Content |
|------|---------|
| [`docs/metric-contract.md`](docs/metric-contract.md) | Baseline metric and label contract |
| [`docs/current-env.md`](docs/current-env.md) | Environment variables |
| [`docs/metric-naming.md`](docs/metric-naming.md) | Gauge vs Counter conventions and review notes |
| [`docs/compatibility.md`](docs/compatibility.md) | Aliases and compatibility policy |
| [`docs/migration-notes.md`](docs/migration-notes.md) | Renamed metrics (e.g. uptime spelling) |
| [`tests/fixtures/README.md`](tests/fixtures/README.md) | Synthetic vs captured API fixtures |

## Grafana example dashboard

Import [`examples/grafana/dashboard.json`](examples/grafana/dashboard.json) into Grafana (see [`examples/grafana/README.md`](examples/grafana/README.md)). It includes example panels for input bitrate (`rate` of `flussonic_input_bits_count`) and last successful fetch timestamp. Select your Prometheus data source on import.

## Development

Formatting and linting use **Black**, **Ruff**, and **mypy** (see [`pyproject.toml`](pyproject.toml)).

A [`Makefile`](Makefile) wraps common tasks:

```bash
make help              # list targets
make install-dev       # pip install runtime + dev deps
make format            # black + ruff --fix
make lint              # ruff + black --check + mypy (read-only)
make test              # pytest
make ci                # lint + test (same as CI locally)
make build             # docker build
make compose-up        # docker compose up -d
```

Equivalent manual commands:

```bash
pip install -r requirements-dev.txt
black flussonic_exporter tests
ruff check flussonic_exporter tests
mypy flussonic_exporter
pytest tests/
```

**Pre-commit** (optional):

```bash
pip install pre-commit
pre-commit install
pre-commit run --all-files
```

Configuration: [`.pre-commit-config.yaml`](.pre-commit-config.yaml).

**CI**: GitHub Actions [`.github/workflows/ci.yml`](.github/workflows/ci.yml) runs Ruff, Black `--check`, mypy, and pytest on pushes and pull requests to `main`/`master`.

## Contributing

Issues and pull requests are welcome. Please run the checks in [Development](#development) before submitting.

## Star History

<a href="https://www.star-history.com/?repos=ntthuan060102github%2FFlussonic-Exporter&type=date&logscale=&legend=bottom-right">
 <picture>
   <source media="(prefers-color-scheme: dark)" srcset="https://api.star-history.com/image?repos=ntthuan060102github/Flussonic-Exporter&type=date&theme=dark&legend=bottom-right" />
   <source media="(prefers-color-scheme: light)" srcset="https://api.star-history.com/image?repos=ntthuan060102github/Flussonic-Exporter&type=date&legend=bottom-right" />
   <img alt="Star History Chart" src="https://api.star-history.com/image?repos=ntthuan060102github/Flussonic-Exporter&type=date&legend=bottom-right" />
 </picture>
</a>
