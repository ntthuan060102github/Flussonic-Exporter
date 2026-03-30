# Environment variables (current)

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `FLUSSONIC_IP` | yes | — | Flussonic host or IP |
| `FLUSSONIC_PORT` | no | `80` | API port |
| `FLUSSONIC_USERNAME` | yes | — | HTTP Basic user |
| `FLUSSONIC_PASSWORD` | yes | — | HTTP Basic password |
| `FLUSSONIC_SERVER_ID` | no | `{IP}:{PORT}` | `server_id` label |
| `FLUSSONIC_FETCH_INTERVAL` | no | `5` | Poll interval (seconds) |
| `FLUSSONIC_SCHEME` | no | — | `http` or `https`; overrides `FLUSSONIC_HTTPS` when set |
| `FLUSSONIC_HTTPS` | no | — | Set `true` for HTTPS if `FLUSSONIC_SCHEME` is unset |
| `FLUSSONIC_TIMEOUT` | no | `5` | HTTP timeout (seconds) |
| `FLUSSONIC_VERIFY_SSL` | no | `true` | Verify TLS certificates |
| `EXPORTER_PORT` | no | `9105` | Flask listen port |
| `LOG_LEVEL` | no | `INFO` | Logging level |

Optional `.env` is loaded when `python-dotenv` is installed.
