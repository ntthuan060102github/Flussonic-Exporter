# Grafana example dashboard

## Import

1. In Grafana: **Dashboards → New → Import**.
2. Upload `dashboard.json` or paste its contents.
3. Select your **Prometheus** data source when prompted.

## Panels

- **Input bitrate (bits/s)** — `rate(flussonic_input_bits_count[5m])` by `stream_name`.
- **Last successful fetch** — `flussonic_exporter_last_success_timestamp_seconds` (Unix time).

Adjust queries and thresholds for your environment. The JSON uses generic `datasource` placeholders; Grafana resolves them on import.
