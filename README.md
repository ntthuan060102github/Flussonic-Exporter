# Flussonic Prometheus Exporter

A lightweight Prometheus exporter for **Flussonic Media Server**, designed to collect detailed stream metrics and expose them via HTTP for monitoring systems such as Prometheus and Grafana.

## 🚀 Features

- Collects real-time metrics from the Flussonic API (`GET /flussonic/api/v3/streams`, up to 200 streams per poll).
- Supports stream-level metrics, including:
  - Input errors and warnings
  - Input bits (from `stats.input.bytes`; use PromQL `rate()` for bit/s)
  - Input source activity and switches
  - DVR read/write performance
  - Play HTTP response statistics
  - Transcoder metrics (hardware, restarts, load, frames)
  - Stream uptime
- Exposes metrics in Prometheus text format on `/metrics` (default port **9105**).
- Configurable via environment variables (optional `.env` via `python-dotenv`).
- Small footprint: Flask + `prometheus_client` + `requests`; easy to run locally or in Docker.

## 🏗️ Architecture overview

```text
Flussonic API  --->  Exporter (Flask + Prometheus client)  --->  Prometheus  --->  Grafana
```

- The exporter periodically fetches stream data from Flussonic (HTTP Basic auth).
- It parses `stats` per stream and updates Prometheus gauges in a registry.
- Prometheus scrapes the `/metrics` endpoint; Grafana (or other tools) use Prometheus as a data source.

## ⚙️ Configuration

The exporter is configured using environment variables:

| Variable | Description | Default |
|----------|-------------|---------|
| `FLUSSONIC_IP` | Flussonic server host or IP | *(required)* |
| `FLUSSONIC_PORT` | Flussonic API port | `80` |
| `FLUSSONIC_USERNAME` | API username | *(required)* |
| `FLUSSONIC_PASSWORD` | API password | *(required)* |
| `FLUSSONIC_SERVER_ID` | Custom server identifier (`server_id` label on all metrics) | `{IP}:{PORT}` |
| `FLUSSONIC_FETCH_INTERVAL` | Poll interval (seconds) | `5` |
| `FLUSSONIC_HTTPS` | Use HTTPS when set to `true` (case-insensitive) | *(unset → HTTP)* |

## 🧪 Run locally

### 1. Install dependencies

```bash
pip install -r requirements.txt
```

### 2. Set environment variables

```bash
export FLUSSONIC_IP=127.0.0.1
export FLUSSONIC_PORT=80
export FLUSSONIC_USERNAME=admin
export FLUSSONIC_PASSWORD=your_password
```

### 3. Run the exporter

```bash
python main.py
```

### 4. Access metrics

Open `http://localhost:9105/metrics` in a browser or let Prometheus scrape that URL.

## 🐳 Docker

```bash
docker build -t flussonic-exporter .
docker run -p 9105:9105 \
  -e FLUSSONIC_IP=... \
  -e FLUSSONIC_USERNAME=... \
  -e FLUSSONIC_PASSWORD=... \
  flussonic-exporter
```

## 📊 Metrics overview

### 🔹 Input metrics

| Metric | Description |
|--------|-------------|
| `flussonic_input_errors_count` | Input errors by `error_type` |
| `flussonic_input_bits_count` | Input bits (cumulative total; `bytes × 8` from the API) |
| `flussonic_input_warnings_count` | Input warnings (`invalid_secondary_inputs`) |
| `flussonic_input_sources` | Time (seconds) on each input source (`primary` / `secondary` / `no_data`) |
| `flussonic_input_sources_switches` | Number of input source switches |

### 🔹 Playback metrics

| Metric | Description |
|--------|-------------|
| `flussonic_play_count` | HTTP play responses by `protocol`, `resource`, and `status` |

### 🔹 DVR metrics

| Metric | Description |
|--------|-------------|
| `flussonic_dvr_read_performance` | DVR read segments by `type` (e.g. fast, slow, delayed, enoent, failed) |
| `flussonic_dvr_write_performance` | DVR write segments by `type` (e.g. fast, slow, collapsed, failed, …) |

### 🔹 Transcoder metrics

| Metric | Description |
|--------|-------------|
| `flussonic_transcoder_hw` | Hardware encoder type (`hw` label; value `1` when present) |
| `flussonic_transcoder_restarts` | Transcoder restart count |
| `flussonic_transcoder_overloaded` | Overload flag (`1` / `0`) |
| `flussonic_transcoder_qualities` | Number of qualities |
| `flussonic_transcoder_frames` | Frames processed |

### 🔹 Stream metrics

| Metric | Description |
|--------|-------------|
| `flussonic_stream_uptime_miliseconds` | Stream uptime from `stats.lifetime` (metric name uses *miliseconds* as in code) |

## 📌 Labels

Most metrics include:

- `server_id` — Flussonic server identifier (from `FLUSSONIC_SERVER_ID` or `IP:PORT`).
- `stream_name` — Stream name (suffix `_stream` removed when present).

Additional labels depend on the metric:

| Label | Used on |
|-------|---------|
| `error_type` | `flussonic_input_errors_count` |
| `protocol`, `resource`, `status` | `flussonic_play_count` |
| `source` | `flussonic_input_sources` |
| `type` | DVR read/write metrics |
| `hw` | `flussonic_transcoder_hw` |

## 🔄 How it works

1. Fetch stream list and stats from the Flussonic API.
2. For each stream, parse `stats` (input, play, DVR, transcoder, lifetime, etc.).
3. Map fields to Prometheus `Gauge` series with the labels above.
4. A background thread repeats on `FLUSSONIC_FETCH_INTERVAL`.
5. The Flask app serves `generate_latest(registry)` at `/metrics`.

## 🛠️ Customization

You can extend the exporter by:

- Adding new metrics from additional Flussonic API fields.
- Filtering or renaming streams before export.
- Running **one exporter instance per Flussonic server** (each with its own `FLUSSONIC_SERVER_ID`) and scraping all targets from Prometheus.
- Feeding Prometheus into alerting (Alertmanager), Grafana, or other aggregation stacks.

## ⚠️ Notes

- Requires Flussonic API access with valid credentials; metrics are **gauges** reflecting API values—use `rate()` / `irate()` in PromQL for throughput (e.g. bits/s).
- If `FLUSSONIC_IP`, `FLUSSONIC_USERNAME`, or `FLUSSONIC_PASSWORD` is missing, the fetch loop does not run; `/metrics` may be empty or stale until configuration is fixed.
- Suitable for custom monitoring pipelines (Prometheus, Grafana, GCP Monitoring via Prometheus remote write, etc.).
- Designed for metrics aggregation outside Flussonic Retroview when you need open, scrapable time series.

## 📈 Example Prometheus config

```yaml
scrape_configs:
  - job_name: flussonic_exporter
    static_configs:
      - targets: ["localhost:9105"]
```

## 🤝 Contributing

Contributions are welcome. Feel free to open issues or submit pull requests.
