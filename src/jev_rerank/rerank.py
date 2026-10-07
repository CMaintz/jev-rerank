"""Rerank passages by relevance to a query, with one batched Jev Score call per chunk."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from .provider import Provider

DEFAULT_LEVELS = ["irrelevant", "loosely related", "relevant", "directly answers the query"]


@dataclass(frozen=True)
class RankedPassage:
    index: int
    text: str
    score: float
    confidence: float


def _key(i: int) -> str:
    return f"p{i}"


def _questions(count: int, levels: list[str]) -> dict[str, Any]:
    return {
        _key(i): {
            "type": "score",
            "instructions": f"Relevance of `passages.{_key(i)}` to the `query`",
            "criteria": levels,
        }
        for i in range(count)
    }


def _state(query: str, passages: list[str]) -> dict[str, Any]:
    return {"query": query, "passages": {_key(i): text for i, text in enumerate(passages)}}


def _ranked_from(answers: dict[str, Any], passages: list[str], offset: int) -> list[RankedPassage]:
    ranked: list[RankedPassage] = []
    for i, text in enumerate(passages):
        answer = answers.get(_key(i))
        if not isinstance(answer, dict) or answer.get("type") != "score":
            continue
        ranked.append(RankedPassage(offset + i, text, float(answer["score"]), float(answer.get("confidence", 0.0))))
    return ranked


class JevReranker:
    """Score every passage's relevance to the query, sort, and filter."""

    def __init__(
        self,
        provider: Provider,
        *,
        top_n: int | None = None,
        min_score: float | None = None,
        batch_size: int = 40,
        levels: list[str] | None = None,
    ) -> None:
        self._provider = provider
        self._top_n = top_n
        self._min_score = min_score
        self._batch_size = max(1, batch_size)
        self._levels = levels or DEFAULT_LEVELS

    def rerank(self, query: str, passages: list[str]) -> list[RankedPassage]:
        ranked: list[RankedPassage] = []
        for start in range(0, len(passages), self._batch_size):
            chunk = passages[start : start + self._batch_size]
            response = self._provider.evaluate(_state(query, chunk), _questions(len(chunk), self._levels))
            ranked.extend(_ranked_from(response.get("answers", {}), chunk, start))
        ranked.sort(key=lambda passage: passage.score, reverse=True)
        if self._min_score is not None:
            ranked = [passage for passage in ranked if passage.score >= self._min_score]
        return ranked if self._top_n is None else ranked[: self._top_n]


def rerank(  # noqa: PLR0913 - public one-shot API mirrors Reranker options
    query: str,
    passages: list[str],
    provider: Provider,
    *,
    top_n: int | None = None,
    min_score: float | None = None,
    batch_size: int = 40,
    levels: list[str] | None = None,
) -> list[RankedPassage]:
    """Functional shortcut for a one-off rerank."""
    reranker = JevReranker(provider, top_n=top_n, min_score=min_score, batch_size=batch_size, levels=levels)
    return reranker.rerank(query, passages)
