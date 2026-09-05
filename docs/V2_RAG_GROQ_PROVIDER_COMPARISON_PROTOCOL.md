# Version 2 RAG Groq Provider Comparison Protocol

## Purpose

This protocol pre-registers a controlled development comparison of Groq GPT-OSS-120B as a second candidate generation provider for the Version 2 RAG generation layer.

Gemini remains historical development evidence. Groq is added as a new candidate provider and does not retroactively replace, reinterpret, or overwrite any Gemini result.

## Motivation

The comparison is motivated by Gemini free-tier operational quota constraints observed during development runs. Provider reliability and answer quality remain separate evidence streams.

This is development/model-selection evidence, not final holdout evidence.

## Frozen Retrieval Boundary

Retrieval, ranking, abstention, and context construction remain frozen:

- HANA table: `DOCUMENT_CHUNKS_V2`
- corpus, source catalog, chunking, and embeddings: unchanged
- embedding model: `BAAI/bge-small-en-v1.5`
- dense retrieval: existing HANA cosine ranking
- lexical retrieval: existing BM25-style ranking
- fusion: full dense ranking plus full lexical ranking through Reciprocal Rank Fusion
- `RRF k = 60`
- preliminary dense document-level top-1 gate: `>= 0.75`
- reranker: none
- context construction: preserved Top-5 unique-document contexts from the canonical confirmation evidence

The comparison harness must not query HANA, rerun retrieval, recompute BM25/RRF, recompute the `0.75` gate, or rebuild/reorder contexts.

## Fixed Inputs

The comparison uses only the preserved accepted questions and contexts from:

`data/rag_prompt_refinement_confirmation_results_v2.csv`

Exactly these 16 development query IDs are eligible, in order:

- `RAGDEV001`
- `RAGDEV002`
- `RAGDEV003`
- `RAGDEV004`
- `RAGDEV005`
- `RAGDEV006`
- `RAGDEV007`
- `RAGDEV008`
- `RAGDEV009`
- `RAGDEV011`
- `RAGDEV012`
- `RAGDEV013`
- `RAGDEV014`
- `RAGDEV015`
- `RAGDEV016`
- `RAGDEV019`

For every query, the harness reuses the exact preserved `QUERY_ID`, `QUESTION`, `PRIMARY_CONTEXT_DOCUMENT_IDS`, and serialized `CONTEXTS`.

## Groq Configuration

Provider: Groq

Model: `openai/gpt-oss-120b`

SDK: official Python `groq` package

Credential source:

- direct `GROQ_API_KEY` environment variable; or
- Cloud Foundry user-provided service named exactly `groq-rag-dev` via `VCAP_SERVICES`.

Groq SDK automatic retries are disabled with `max_retries=0` so each case has exactly one underlying provider attempt.

Generation uses chat completions with:

- `reasoning_effort="medium"`
- `include_reasoning=False`

No tools, web search, MCP, code execution, browsing, external retrieval, Groq compound functionality, fallback model, fallback provider, retry, or backoff is allowed.

The same existing grounded prompt and supplied SAP contexts are used. No Groq-specific quality prompt is introduced.

## Execution Policy

The comparison harness writes CSV to stdout only. It does not create the eventual evidence file.

The eventual capture file will be:

`data/rag_generation_provider_comparison_groq_v2.csv`

Execution order is fixed by the 16 eligible query IDs above.

Exactly one Groq provider attempt is made per row. Provider errors are preserved and processing continues to later rows.

The harness applies 30 seconds of pacing before every request except the first. This pacing is infrastructure-only because the Groq free tier currently has a token-per-minute limit in addition to request limits. It does not change the scientific generation configuration.

## Scoring Plan

No prompt tuning will be performed from Groq outputs before the comparison is scored.

The same human scoring dimensions will be used:

- groundedness;
- answer correctness;
- citation correctness;
- hallucination;
- refusal correctness where applicable;
- concision.

Provider reliability and answer quality must remain separately reported.

## Final Evaluation Boundary

This comparison is not the final fresh RAG end-to-end evaluation. Final fresh evaluation will happen only after provider selection and architecture freeze.

## Non-Execution Confirmation

Creating this protocol and harness does not:

- call Groq;
- call Gemini;
- query HANA;
- execute retrieval;
- modify canonical evidence CSVs;
- modify frozen retrieval, abstention, context construction, prompt, Gemini behavior, or production `app.py`.
