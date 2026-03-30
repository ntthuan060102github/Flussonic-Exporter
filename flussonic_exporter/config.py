"""Environment-based configuration with validation."""

from __future__ import annotations

import os
from dataclasses import dataclass


def _load_dotenv() -> None:
    try:
        from dotenv import load_dotenv as _load
    except ImportError:
        return
    _load()


class ConfigError(ValueError):
    """Invalid or incomplete configuration."""


def _env_bool(name: str, default: bool) -> bool:
    raw = os.environ.get(name)
    if raw is None or raw.strip() == "":
        return default
    return raw.strip().lower() in ("1", "true", "yes", "on")


def _env_int(name: str, default: int) -> int:
    raw = os.environ.get(name)
    if raw is None or raw.strip() == "":
        return default
    try:
        return int(raw)
    except ValueError as e:
        raise ConfigError(f"{name} must be an integer, got {raw!r}") from e


def _env_float(name: str, default: float) -> float:
    raw = os.environ.get(name)
    if raw is None or raw.strip() == "":
        return default
    try:
        return float(raw)
    except ValueError as e:
        raise ConfigError(f"{name} must be a number, got {raw!r}") from e


@dataclass(frozen=True)
class Settings:
    flussonic_host: str
    flussonic_port: int
    flussonic_username: str
    flussonic_password: str
    server_id: str
    scheme: str
    api_path: str
    fetch_interval: float
    timeout: float
    verify_ssl: bool
    exporter_port: int
    log_level: str

    @property
    def streams_url(self) -> str:
        return f"{self.scheme}://{self.flussonic_host}:{self.flussonic_port}{self.api_path}"


def load_settings(api_path: str = "/flussonic/api/v3/streams?limit=200") -> Settings:
    """Load and validate settings from the environment. Raises ConfigError on failure."""
    _load_dotenv()

    host = os.environ.get("FLUSSONIC_IP", "").strip()
    user = os.environ.get("FLUSSONIC_USERNAME", "").strip()
    password = os.environ.get("FLUSSONIC_PASSWORD", "").strip()

    missing = [
        n
        for n, v in (
            ("FLUSSONIC_IP", host),
            ("FLUSSONIC_USERNAME", user),
            ("FLUSSONIC_PASSWORD", password),
        )
        if not v
    ]
    if missing:
        raise ConfigError(f"Missing required environment variable(s): {', '.join(missing)}")

    port = _env_int("FLUSSONIC_PORT", 80)
    if port < 1 or port > 65535:
        raise ConfigError("FLUSSONIC_PORT must be between 1 and 65535")

    scheme_raw = os.environ.get("FLUSSONIC_SCHEME", "").strip().lower()
    if scheme_raw:
        if scheme_raw not in ("http", "https"):
            raise ConfigError("FLUSSONIC_SCHEME must be 'http' or 'https'")
        scheme = scheme_raw
    else:
        scheme = "https" if _env_bool("FLUSSONIC_HTTPS", False) else "http"

    sid = os.environ.get("FLUSSONIC_SERVER_ID", "").strip()
    server_id = sid if sid else f"{host}:{port}"

    fetch_interval = _env_float("FLUSSONIC_FETCH_INTERVAL", 5.0)
    if fetch_interval <= 0:
        raise ConfigError("FLUSSONIC_FETCH_INTERVAL must be positive")

    timeout = _env_float("FLUSSONIC_TIMEOUT", 5.0)
    if timeout <= 0:
        raise ConfigError("FLUSSONIC_TIMEOUT must be positive")

    verify_ssl = _env_bool("FLUSSONIC_VERIFY_SSL", True)
    exporter_port = _env_int("EXPORTER_PORT", 9105)
    if exporter_port < 1 or exporter_port > 65535:
        raise ConfigError("EXPORTER_PORT must be between 1 and 65535")

    log_level = os.environ.get("LOG_LEVEL", "INFO").strip().upper() or "INFO"

    return Settings(
        flussonic_host=host,
        flussonic_port=port,
        flussonic_username=user,
        flussonic_password=password,
        server_id=server_id,
        scheme=scheme,
        api_path=api_path,
        fetch_interval=fetch_interval,
        timeout=timeout,
        verify_ssl=verify_ssl,
        exporter_port=exporter_port,
        log_level=log_level,
    )
