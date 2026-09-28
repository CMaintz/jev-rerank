# Changelog

All notable changes to this project are documented here. Format: [Keep a Changelog](https://keepachangelog.com/en/1.1.0/); this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added

- **v0.1:** `rerank(query, passages, provider)` and `JevReranker` - score each passage's relevance to the query with one batched Jev `Score` call, sort descending, filter by `min_score`, truncate to `top_n`.
- Chunked batching (`batch_size`) so large candidate sets stay under Jev's context cap; global passage indices preserved across chunks.
- Zero-dependency `TypeSafeProvider` (stdlib `urllib`) with 429/529 backoff; `Provider` protocol for swappable backends.
- Onboarded onto the Foundry Python gate (ruff, mypy `--strict`, pytest, pip-audit).

### Roadmap

- First-class LlamaIndex `BaseNodePostprocessor` and LangChain `BaseDocumentCompressor` adapters (optional extras).
- Async batching; score caching for repeated queries; a live-key end-to-end run.
