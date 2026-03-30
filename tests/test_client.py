"""Tests for Flussonic HTTP client (retries, errors, JSON validation)."""

from __future__ import annotations

import json
from unittest.mock import MagicMock, patch

import pytest
import requests
from flussonic_exporter.client import FlussonicClient


def _ok_response(payload: dict) -> MagicMock:
    r = MagicMock()
    r.status_code = 200
    r.json.return_value = payload
    r.raise_for_status = MagicMock()
    return r


def test_fetch_success():
    client = FlussonicClient(
        "http://10.0.0.1/flussonic/api/v3/streams",
        "user",
        "pass",
        5.0,
        True,
        max_retries=1,
    )
    with patch("flussonic_exporter.client.requests.get") as mock_get:
        mock_get.return_value = _ok_response({"streams": []})
        out = client.fetch_streams_json()
        assert out == {"streams": []}
        mock_get.assert_called_once()


def test_fetch_invalid_json_raises():
    client = FlussonicClient("http://x/y", "u", "p", 5.0, True, max_retries=1)
    r = MagicMock()
    r.status_code = 200
    r.raise_for_status = MagicMock()
    r.json.side_effect = json.JSONDecodeError("expecting value", "", 0)
    with patch("flussonic_exporter.client.requests.get", return_value=r):
        with pytest.raises(ValueError, match="Invalid JSON"):
            client.fetch_streams_json()


def test_fetch_non_object_json_raises():
    client = FlussonicClient("http://x/y", "u", "p", 5.0, True, max_retries=1)
    r = MagicMock()
    r.status_code = 200
    r.raise_for_status = MagicMock()
    r.json.return_value = []
    with patch("flussonic_exporter.client.requests.get", return_value=r):
        with pytest.raises(ValueError, match="top-level JSON object"):
            client.fetch_streams_json()


def test_fetch_http_error_raises():
    client = FlussonicClient("http://x/y", "u", "p", 5.0, True, max_retries=1)
    r = MagicMock()
    r.raise_for_status.side_effect = requests.HTTPError("404")
    with patch("flussonic_exporter.client.requests.get", return_value=r):
        with pytest.raises(requests.HTTPError):
            client.fetch_streams_json()


@patch("flussonic_exporter.client.time.sleep", return_value=None)
def test_retries_then_success(mock_sleep):
    client = FlussonicClient("http://x/y", "u", "p", 5.0, True, max_retries=3)
    bad = MagicMock()
    bad.raise_for_status.side_effect = requests.ConnectionError("refused")
    good = _ok_response({"streams": [{"name": "a"}]})
    with patch(
        "flussonic_exporter.client.requests.get",
        side_effect=[bad, good],
    ) as mock_get:
        out = client.fetch_streams_json()
        assert "streams" in out
        assert mock_get.call_count == 2
        assert mock_sleep.call_count == 1


@patch("flussonic_exporter.client.time.sleep", return_value=None)
def test_all_retries_exhausted(mock_sleep):
    client = FlussonicClient("http://x/y", "u", "p", 5.0, True, max_retries=2)
    bad = MagicMock()
    bad.raise_for_status.side_effect = requests.Timeout("t")
    with patch("flussonic_exporter.client.requests.get", return_value=bad):
        with pytest.raises(requests.Timeout):
            client.fetch_streams_json()
        assert mock_sleep.call_count == 1
