# Metric compatibility and aliases

## Renamed / duplicate series

| Preferred metric | Legacy / alias | Status |
|------------------|-----------------|--------|
| `flussonic_stream_uptime_milliseconds` | `flussonic_stream_uptime_miliseconds` | Both emitted with the **same value**; use the correctly spelled name in new dashboards. |

## Exporter metrics

`flussonic_exporter_*` names are stable for build info and last-success timestamp. If renamed, this file and [`migration-notes.md`](migration-notes.md) will be updated.

## Policy

- Breaking removals of legacy names will be called out in release notes and `migration-notes.md`.
- Prefer scraping `flussonic_exporter_build_info` to pin exporter version in support tickets.
