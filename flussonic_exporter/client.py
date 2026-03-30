"""HTTP client for Flussonic streams API."""

from __future__ import annotations

import json
import logging
import time
from typing import Any

import requests

logger = logging.getLogger(__name__)


class FlussonicClient:
    """Fetch streams JSON with retries."""

    def __init__(
        self,
        url: str,
        username: str,
        password: str,
        timeout: float,
        verify_ssl: bool,
        max_retries: int = 3,
    ) -> None:
        self._url = url
        self._auth = (username, password)
        self._timeout = timeout
        self._verify = verify_ssl
        self._max_retries = max(1, max_retries)

    def fetch_streams_json(self) -> dict[str, Any]:
        last_exc: Exception | None = None
        for attempt in range(self._max_retries):
            try:
                resp = requests.get(
                    self._url,
                    auth=self._auth,
                    timeout=self._timeout,
                    verify=self._verify,
                )
                resp.raise_for_status()
                try:
                    data = resp.json()
                except json.JSONDecodeError as e:
                    raise ValueError(f"Invalid JSON from Flussonic: {e}") from e
                if not isinstance(data, dict):
                    raise ValueError("Expected top-level JSON object from Flussonic")
                return data
            except (requests.RequestException, ValueError) as e:
                last_exc = e
                logger.warning(
                    "Fetch attempt %s/%s failed for %s: %s",
                    attempt + 1,
                    self._max_retries,
                    self._url,
                    e,
                )
                if attempt + 1 < self._max_retries:
                    time.sleep(2**attempt)
        assert last_exc is not None
        raise last_exc
