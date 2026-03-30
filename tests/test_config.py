import pytest
from flussonic_exporter.config import ConfigError, load_settings


def test_load_settings_requires_vars(monkeypatch):
    monkeypatch.delenv("FLUSSONIC_IP", raising=False)
    monkeypatch.delenv("FLUSSONIC_USERNAME", raising=False)
    monkeypatch.delenv("FLUSSONIC_PASSWORD", raising=False)
    with pytest.raises(ConfigError, match="FLUSSONIC_IP"):
        load_settings()


def test_load_settings_ok(monkeypatch):
    monkeypatch.setenv("FLUSSONIC_IP", "10.0.0.1")
    monkeypatch.setenv("FLUSSONIC_USERNAME", "u")
    monkeypatch.setenv("FLUSSONIC_PASSWORD", "p")
    monkeypatch.setenv("FLUSSONIC_PORT", "443")
    s = load_settings()
    assert s.flussonic_host == "10.0.0.1"
    assert s.server_id == "10.0.0.1:443"
    assert "10.0.0.1:443" in s.streams_url


def test_scheme_from_env(monkeypatch):
    monkeypatch.setenv("FLUSSONIC_IP", "h")
    monkeypatch.setenv("FLUSSONIC_USERNAME", "u")
    monkeypatch.setenv("FLUSSONIC_PASSWORD", "p")
    monkeypatch.setenv("FLUSSONIC_SCHEME", "https")
    s = load_settings()
    assert s.scheme == "https"


def test_https_legacy(monkeypatch):
    monkeypatch.setenv("FLUSSONIC_IP", "h")
    monkeypatch.setenv("FLUSSONIC_USERNAME", "u")
    monkeypatch.setenv("FLUSSONIC_PASSWORD", "p")
    monkeypatch.setenv("FLUSSONIC_HTTPS", "true")
    s = load_settings()
    assert s.scheme == "https"
