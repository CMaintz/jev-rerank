from __future__ import annotations

import json
import time
import urllib.error
import urllib.request
from typing import Any

from pytest import MonkeyPatch

from jev_rerank import TypeSafeProvider


class _Response:
    def __init__(self, payload: dict[str, Any]) -> None:
        self._data = json.dumps(payload).encode("utf-8")

    def read(self) -> bytes:
        return self._data

    def __enter__(self) -> _Response:
        return self

    def __exit__(self, *args: object) -> None:
        return None


def test_evaluate_posts_and_parses(monkeypatch: MonkeyPatch) -> None:
    captured: dict[str, Any] = {}

    def fake_urlopen(request: Any) -> _Response:
        captured["url"] = request.full_url
        captured["body"] = json.loads(request.data)
        captured["auth"] = request.get_header("Authorization")
        return _Response({"model": "jev-latest", "answers": {"p0": {"type": "score", "score": 2.0}}})

    monkeypatch.setattr(urllib.request, "urlopen", fake_urlopen)
    out = TypeSafeProvider("k").evaluate({"query": "x"}, {"p0": {"type": "score"}})

    assert out["answers"]["p0"]["score"] == 2.0
    assert captured["url"].endswith("/v1/systemone")
    assert captured["body"]["model"] == "jev-latest"
    assert captured["auth"] == "Bearer k"


def test_retries_on_429(monkeypatch: MonkeyPatch) -> None:
    calls = {"n": 0}

    def flaky(request: Any) -> _Response:
        calls["n"] += 1
        if calls["n"] == 1:
            raise urllib.error.HTTPError(request.full_url, 429, "rate limited", {}, None)  # type: ignore[arg-type]
        return _Response({"answers": {}})

    monkeypatch.setattr(urllib.request, "urlopen", flaky)
    monkeypatch.setattr(time, "sleep", lambda _seconds: None)

    out = TypeSafeProvider("k").evaluate({}, {})
    assert calls["n"] == 2
    assert out == {"answers": {}}
