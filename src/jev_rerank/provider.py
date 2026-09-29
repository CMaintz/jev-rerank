"""Jev provider: POST /v1/systemone. Zero runtime deps (stdlib urllib)."""

from __future__ import annotations

import json
import time
import urllib.error
import urllib.request
from typing import Any, Protocol

_RETRYABLE = frozenset({429, 529})


class Provider(Protocol):
    """Anything that can answer typed questions about a state."""

    def evaluate(self, state: Any, questions: dict[str, Any]) -> dict[str, Any]: ...


def _post_json(url: str, headers: dict[str, str], body: dict[str, Any], attempts: int = 4) -> dict[str, Any]:
    """POST JSON with exponential backoff on 429/529 (the retry the docs recommend)."""
    data = json.dumps(body).encode("utf-8")
    for attempt in range(1, attempts + 1):
        request = urllib.request.Request(  # noqa: S310 - fixed https base_url
            url, data=data, method="POST", headers={"Content-Type": "application/json", **headers}
        )
        try:
            with urllib.request.urlopen(request) as response:  # noqa: S310
                parsed: dict[str, Any] = json.loads(response.read().decode("utf-8"))
                return parsed
        except urllib.error.HTTPError as err:
            if err.code in _RETRYABLE and attempt < attempts:
                time.sleep(0.25 * 2 ** (attempt - 1))
                continue
            raise
    raise RuntimeError("unreachable")


class TypeSafeProvider:
    """First-party Jev client (verified against docs.typesafe.ai/api)."""

    def __init__(self, api_key: str, model: str = "jev-latest", base_url: str = "https://api.typesafe.ai/v1") -> None:
        self._api_key = api_key
        self._model = model
        self._base_url = base_url

    def evaluate(self, state: Any, questions: dict[str, Any]) -> dict[str, Any]:
        return _post_json(
            f"{self._base_url}/systemone",
            {"Authorization": f"Bearer {self._api_key}"},
            {"model": self._model, "state": state, "questions": questions},
        )
