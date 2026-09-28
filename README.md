# jev-rerank

**Fast, near-free RAG relevance filtering and reranking, powered by [TypeSafe AI's Jev](https://typesafe.ai/).**

Rerankers (Cohere Rerank, cross-encoders) are a RAG staple, but they are slow and cost real money per query. jev-rerank scores each candidate passage's relevance to the query with Jev's `Score` primitive, in one batched call at roughly a hundredth of the cost and latency, then sorts and filters.

```python
import os
from jev_rerank import rerank, TypeSafeProvider

provider = TypeSafeProvider(api_key=os.environ["JEV_API_KEY"])
ranked = rerank(query, passages, provider, top_n=5, min_score=2.0)
for p in ranked:
    print(p.score, p.text)
```

## How it works

- One batched Jev call per chunk: every passage becomes a `Score` question over shared `{query, passages}` state (adding questions is near-free, evaluated in parallel).
- Each passage gets a relevance score on an ordered rubric (0..N) plus a confidence.
- Results sort by score descending; `min_score` filters, `top_n` truncates. `batch_size` chunks large candidate sets so each call stays under Jev's context cap.

## Drop-in for LlamaIndex / LangChain

The framework reranker interfaces are a few lines over `rerank()`:

```python
# LlamaIndex BaseNodePostprocessor
class JevPostprocessor(BaseNodePostprocessor):
    def _postprocess_nodes(self, nodes, query_bundle):
        texts = [n.get_content() for n in nodes]
        ranked = rerank(query_bundle.query_str, texts, provider, top_n=self.top_n)
        return [nodes[r.index] for r in ranked]
```

First-class `jev-rerank[llamaindex]` and `[langchain]` adapters are on the v0.2 roadmap.

## Honest limitations

- **A cheap first pass, not a cross-encoder.** Jev is ~68% accurate; for the last few points of ranking quality a dedicated cross-encoder still wins. jev-rerank shines as a cheap prefilter before an expensive reranker, or when Cohere-scale cost and latency are the actual problem.
- **Text only**; each chunk must fit Jev's context (~32k tokens).
- **Needs a Jev key** (`JEV_API_KEY`; sign up at [TypeSafe](https://typesafe.ai/)).

## Status

**v0.1** - the core `rerank()` + `JevReranker` + zero-dependency provider (stdlib `urllib`), batched and chunked. Passes the [Foundry](https://github.com/CMaintz/foundry) gate (ruff, mypy, pytest, pip-audit). Roadmap: first-class LlamaIndex/LangChain adapters, async batching, and score caching.

MIT (c) Christoffer Maintz
