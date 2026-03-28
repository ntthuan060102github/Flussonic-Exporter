import os
import re
import time

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass
import threading
import requests
from flask import Flask, Response
from prometheus_client import Gauge, generate_latest, CollectorRegistry

FLUSSONIC_IP = os.environ.get("FLUSSONIC_IP", "")
FLUSSONIC_PORT = os.environ.get("FLUSSONIC_PORT", "80")
FLUSSONIC_USERNAME = os.environ.get("FLUSSONIC_USERNAME", "")
FLUSSONIC_PASSWORD = os.environ.get("FLUSSONIC_PASSWORD", "")
FLUSSONIC_SERVER_ID = os.environ.get("FLUSSONIC_SERVER_ID", "")
FLUSSONIC_FETCH_INTERVAL = int(os.environ.get("FLUSSONIC_FETCH_INTERVAL", "5"))

API_PATH = "/flussonic/api/v3/streams?limit=200"

app = Flask(__name__)
registry = CollectorRegistry()

LABELS = ["server_id", "stream_name"]

PLAY_HTTP_RE = re.compile(
    r"^play_(?P<protocol>[^_]+(?:_[^_]+)?)(?:_(?P<resource>[^_]+))?_http_(?P<status>\d+)$"
)

# --- Required metrics ---
# input_errors_count
input_errors_count = Gauge(
    "flussonic_input_errors_count",
    "Input errors count by error type",
    LABELS + ["error_type"],
    registry=registry
)

# input_bits_count
input_bits_count = Gauge(
    "flussonic_input_bits_count",
    "Input bits received (bytes * 8)",
    LABELS,
    registry=registry
)

# input_warnings_count
input_warnings_count = Gauge(
    "flussonic_input_warnings_count",
    "Input warnings count (invalid_secondary_inputs)",
    LABELS,
    registry=registry
)

# input_sources: seconds active on each input source (primary, secondary, no_data)
input_sources = Gauge(
    "flussonic_input_sources",
    "Seconds active on each input source (primary, secondary, no_data)",
    LABELS + ["source"],
    registry=registry
)

# input_sources_switches
input_sources_switches = Gauge(
    "flussonic_input_sources_switches",
    "Number of input source switches",
    LABELS,
    registry=registry
)

# dvr_read_performance: segments read by type (fast/slow/delayed/enoent/failed)
dvr_read_performance = Gauge(
    "flussonic_dvr_read_performance",
    "DVR read performance segments count by type",
    LABELS + ["type"],
    registry=registry
)

# dvr_write_performance: segments write by type (fast/slow/delayed/collapsed/failed/skipped/discontinuity)
dvr_write_performance = Gauge(
    "flussonic_dvr_write_performance",
    "DVR write performance segments count by type",
    LABELS + ["type"],
    registry=registry
)

# play_http_responses: play HTTP responses by protocol, resource, status (stats.play.*_http_*)
play_count = Gauge(
    "flussonic_play_count",
    "Play HTTP responses count by protocol, resource type and status code",
    LABELS + ["protocol", "resource", "status"],
    registry=registry
)

# transcoder_hw: hardware encoder type (info metric: value=1, label hw)
transcoder_hw = Gauge(
    "flussonic_transcoder_hw",
    "Transcoder hardware encoder type (1 = present)",
    LABELS + ["hw"],
    registry=registry
)

# transcoder_restarts
transcoder_restarts = Gauge(
    "flussonic_transcoder_restarts",
    "Transcoder restart count",
    LABELS,
    registry=registry
)

# transcoder_overloaded
transcoder_overloaded = Gauge(
    "flussonic_transcoder_overloaded",
    "Transcoder overloaded (1=yes, 0=no)",
    LABELS,
    registry=registry
)

# transcoder_qualities
transcoder_qualities = Gauge(
    "flussonic_transcoder_qualities",
    "Transcoder qualities count",
    LABELS,
    registry=registry
)

# transcoder_frames
transcoder_frames = Gauge(
    "flussonic_transcoder_frames",
    "Transcoder frames processed",
    LABELS,
    registry=registry
)

# stream_uptime_seconds: stream uptime in miliseconds (from stats.lifetime)
stream_uptime_miliseconds = Gauge(
    "flussonic_stream_uptime_miliseconds",
    "Stream uptime in miliseconds (from stats.lifetime)",
    LABELS,
    registry=registry
)


def _get_server_config():
    if not FLUSSONIC_IP or not FLUSSONIC_USERNAME or not FLUSSONIC_PASSWORD:
        return None
    proto = "https" if os.environ.get("FLUSSONIC_HTTPS", "").lower() == "true" else "http"
    url = f"{proto}://{FLUSSONIC_IP}:{FLUSSONIC_PORT}{API_PATH}"
    server_id = FLUSSONIC_SERVER_ID.strip() if FLUSSONIC_SERVER_ID else f"{FLUSSONIC_IP}:{FLUSSONIC_PORT}"
    return {
        "url": url,
        "server_id": server_id,
        "username": FLUSSONIC_USERNAME,
        "password": FLUSSONIC_PASSWORD,
    }


def fetch_flussonic_data():
    config = _get_server_config()
    if not config:
        print("Missing FLUSSONIC_IP, FLUSSONIC_USERNAME or FLUSSONIC_PASSWORD. Not fetching data.")
        return
    while True:
        try:
            print(f"{config['server_id']} ({config['url']})")
            response = requests.get(
                config["url"],
                auth=(config["username"], config["password"]),
                timeout=5
            )
            response.raise_for_status()
            data = response.json()
            streams = data.get("streams", [])

            for stream in streams:
                stream_name = stream.get("name", "unknown").replace("_stream", "")
                server_id = config["server_id"]
                stats = stream.get("stats", {})
                input_stats = stats.get("input", {})
                transcoder_stats = stats.get("transcoder", {})

                # --- input_errors_count: detailed error types (from stats.input) ---
                error_types = {
                    "errors": input_stats.get("errors", 0),
                    "errors_lost_packets": input_stats.get("errors_lost_packets", 0),
                    "errors_decoder_reset": input_stats.get("errors_decoder_reset", 0),
                    "errors_broken_payload": input_stats.get("errors_broken_payload", 0),
                    "errors_dropped_frames": input_stats.get("errors_dropped_frames", 0),
                    "errors_desync": input_stats.get("errors_desync", 0),
                    "errors_ts_pat": input_stats.get("errors_ts_pat", 0),
                    "errors_ts_service_lost": input_stats.get("errors_ts_service_lost", 0),
                    "errors_ts_stuck_restarts": input_stats.get("errors_ts_stuck_restarts", 0),
                    "errors_ts_jump_restarts": input_stats.get("errors_ts_jump_restarts", 0),
                    "errors_404": input_stats.get("errors_404", 0),
                    "errors_403": input_stats.get("errors_403", 0),
                    "errors_500": input_stats.get("errors_500", 0),
                    "errors_crashed": input_stats.get("errors_crashed", 0),
                    "resync_count_drift": input_stats.get("resync_count_drift", 0),
                    "resync_count_jump": input_stats.get("resync_count_jump", 0),
                    "resync_count_normal": input_stats.get("resync_count_normal", 0),
                    "reorder_count": input_stats.get("reorder_count", 0),
                    "invalid_secondary_inputs": input_stats.get("invalid_secondary_inputs", 0),
                }
                for error_type, count in error_types.items():
                    input_errors_count.labels(
                        server_id=server_id,
                        stream_name=stream_name,
                        error_type=error_type
                    ).set(count)

                # --- input_bits_count (bytes * 8) ---
                bytes_in = input_stats.get("bytes", 0)
                input_bits_count.labels(
                    server_id=server_id,
                    stream_name=stream_name
                ).set(bytes_in * 8)

                # --- input_warnings_count ---
                warnings = input_stats.get("invalid_secondary_inputs", 0)
                input_warnings_count.labels(
                    server_id=server_id,
                    stream_name=stream_name
                ).set(warnings)

                # --- input_sources: seconds active on each input source (primary, secondary, no_data) ---
                input_sources.labels(
                    server_id=server_id,
                    stream_name=stream_name,
                    source="primary"
                ).set(input_stats.get("num_sec_on_primary_input", 0))
                input_sources.labels(
                    server_id=server_id,
                    stream_name=stream_name,
                    source="secondary"
                ).set(input_stats.get("num_sec_on_secondary_input", 0))
                input_sources.labels(
                    server_id=server_id,
                    stream_name=stream_name,
                    source="no_data"
                ).set(input_stats.get("num_sec_no_data", 0))

                # --- input_sources_switches ---
                input_sources_switches.labels(
                    server_id=server_id,
                    stream_name=stream_name
                ).set(input_stats.get("input_switches", 0))

                # --- play_count (play errors / HTTP status) ---
                play_stats = stats.get("play", {})
                for key, value in play_stats.items():
                    if isinstance(value, (int, float)):
                        m = PLAY_HTTP_RE.match(key)
                        if m:
                            protocol = m.group("protocol")
                            resource = m.group("resource") or "unknown"
                            status = m.group("status")
                            play_count.labels(
                                server_id=server_id,
                                stream_name=stream_name,
                                protocol=protocol,
                                resource=resource,
                                status=status
                            ).set(value)

                # --- dvr_read_performance ---
                dvr_read = stats.get("dvr_read_performance", {})
                for seg_type in ("segments_read_fast", "segments_read_slow", "segments_read_delayed"):
                    seg_data = dvr_read.get(seg_type, {})
                    if isinstance(seg_data, dict):
                        total = seg_data.get("ram", 0) + seg_data.get("cache", 0) + seg_data.get("local", 0) + seg_data.get("remote", 0)
                    else:
                        total = 0
                    dvr_read_performance.labels(
                        server_id=server_id,
                        stream_name=stream_name,
                        type=seg_type.replace("segments_read_", "")
                    ).set(total)
                dvr_read_performance.labels(
                    server_id=server_id,
                    stream_name=stream_name,
                    type="enoent"
                ).set(dvr_read.get("segments_read_enoent", 0))
                dvr_read_performance.labels(
                    server_id=server_id,
                    stream_name=stream_name,
                    type="failed"
                ).set(dvr_read.get("segments_read_failed", 0))

                # --- dvr_write_performance ---
                dvr_write = stats.get("dvr_write", {})
                for metric_key, type_name in [
                    ("segments_written_fast", "fast"),
                    ("segments_written_slow", "slow"),
                    ("segments_written_delayed", "delayed"),
                    ("segments_written_collapsed", "collapsed"),
                    ("segments_failed", "failed"),
                    ("segments_skipped", "skipped"),
                    ("segments_discontinuity", "discontinuity"),
                ]:
                    dvr_write_performance.labels(
                        server_id=server_id,
                        stream_name=stream_name,
                        type=type_name
                    ).set(dvr_write.get(metric_key, 0))

                # --- transcoder metrics ---
                hw = transcoder_stats.get("hw", "unknown")
                transcoder_hw.labels(
                    server_id=server_id,
                    stream_name=stream_name,
                    hw=hw
                ).set(1)

                transcoder_restarts.labels(
                    server_id=server_id,
                    stream_name=stream_name
                ).set(transcoder_stats.get("restarts", 0))

                transcoder_overloaded.labels(
                    server_id=server_id,
                    stream_name=stream_name
                ).set(1 if stats.get("transcoder_overloaded", False) else 0)

                transcoder_qualities.labels(
                    server_id=server_id,
                    stream_name=stream_name
                ).set(transcoder_stats.get("qualities", 0))

                transcoder_frames.labels(
                    server_id=server_id,
                    stream_name=stream_name
                ).set(transcoder_stats.get("frames", 0))

                # --- stream_uptime_seconds ---
                stream_uptime_miliseconds.labels(
                    server_id=server_id,
                    stream_name=stream_name
                ).set(stats.get("lifetime", 0))

            print(f"{config['server_id']} updated.")

        except requests.exceptions.RequestException as e:
            print(f"{config['server_id']} ({config['url']}) error: {e}")

        time.sleep(FLUSSONIC_FETCH_INTERVAL)


@app.route("/metrics")
def metrics():
    return Response(generate_latest(registry), mimetype="text/plain")


if __name__ == "__main__":
    threading.Thread(target=fetch_flussonic_data, daemon=True).start()
    app.run(host="0.0.0.0", port=9105)
