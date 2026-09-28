from __future__ import annotations

from typing import Any

from jev_rerank import JevReranker, rerank


class FakeProvider:
    """Returns preset scores keyed by passage text; records how many calls it took."""

    def __init__(self, scores: dict[str, float]) -> None:
        self.scores = scores
        self.calls = 0

    def evaluate(self, state: Any, questions: dict[str, Any]) -> dict[str, Any]:
        self.calls += 1
        answers = {
            key: {"type": "score", "score": self.scores[state["passages"][key]], "confidence": 0.9} for key in questions
        }
        return {"answers": answers, "usage": {"input_tokens": 10, "output_tokens": 2}}


def test_ranks_by_score_descending() -> None:
    provider = FakeProvider({"a": 2.9, "b": 0.1, "c": 1.5})
    ranked = rerank("q", ["a", "b", "c"], provider)
    assert [p.text for p in ranked] == ["a", "c", "b"]
    assert ranked[0].score == 2.9
    assert provider.calls == 1


def test_min_score_and_top_n() -> None:
    provider = FakeProvider({"a": 2.9, "b": 0.1, "c": 1.5})
    ranked = rerank("q", ["a", "b", "c"], provider, min_score=1.0, top_n=1)
    assert [p.text for p in ranked] == ["a"]


def test_batching_makes_multiple_calls_and_preserves_global_index() -> None:
    provider = FakeProvider({"a": 1.0, "b": 2.0, "c": 3.0, "d": 0.5})
    ranked = JevReranker(provider, batch_size=2).rerank("q", ["a", "b", "c", "d"])
    assert provider.calls == 2
    assert [p.text for p in ranked] == ["c", "b", "a", "d"]
    assert [p.index for p in ranked] == [2, 1, 0, 3]


def test_non_score_answers_are_skipped() -> None:
    class Noul:
        def evaluate(self, state: Any, questions: dict[str, Any]) -> dict[str, Any]:
            return {"answers": {"p0": {"type": "noul", "noul": 0.5}}}

    assert rerank("q", ["only"], Noul()) == []
