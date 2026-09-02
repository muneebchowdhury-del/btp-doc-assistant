# Version 2 RAG LLM Connectivity Results

## Purpose

This document records the isolated provider-connectivity investigation for the Version 2 RAG generation layer.

The investigation was limited to proving whether the application runtime can make a controlled external LLM request through the selected provider boundary. It was not a RAG answer-quality evaluation, prompt-tuning exercise, retrieval test, or production application change.

## Architecture Boundary

The frozen retrieval and abstention system was not changed:

- SAP HANA Cloud / HDI table: `DOCUMENT_CHUNKS_V2`
- dense embedding model: `BAAI/bge-small-en-v1.5`
- lexical retrieval: existing BM25-style implementation
- fusion: full dense + full lexical Reciprocal Rank Fusion
- `RRF k = 60`
- preliminary dense-score gate: `0.75`
- reranker: none
- production `app.py`: unchanged

No frozen retrieval held-out questions were used during connectivity testing.

## Provider Path

SAP-native AI Core / Generative AI Hub remains unavailable in the current academic BTP environment. The required SAP AI Core / Generative AI Hub-capable access was not visible during the earlier feasibility check.

An OpenAI adapter prototype existed briefly as an unexecuted implementation artifact. No OpenAI API request was made. It was replaced before any generation experiment because this project requires a free external provider.

Gemini Developer API was selected as the external generation provider. Gemini is not SAP-native.

## Connectivity Investigation

The initial local `google-genai` import failed before any API request was made. This was resolved by installing the project requirements.

An earlier malformed one-character `GEMINI_API_KEY` caused `API_KEY_INVALID` responses. No generation occurred from that key. The exposed old key was revoked. No key value is included in this repository or this documentation.

After the corrected key was configured, authentication was confirmed.

Model connectivity outcomes:

- `gemini-3.7-flash`: repeated authenticated `503 UNAVAILABLE` / high-demand provider-side failures.
- `gemini-3.6-flash`: model metadata endpoint succeeded, but a controlled `generateContent` request timed out after 45 seconds with zero response bytes.
- `gemini-3.5-flash`: controlled synthetic generation succeeded.

## Test Data Used

Connectivity tests used only synthetic text such as `CONNECTIVITY_OK` and `TEST-DOC`.

The synthetic context was not part of any final retrieval, abstention, or RAG evaluation set. No frozen held-out retrieval questions were used.

## Selected Generation Model

The selected external generation provider configuration is:

- Provider: Google Gemini Developer API
- Model: `gemini-3.5-flash`
- Python SDK: `google-genai`
- Credential environment variable: `GEMINI_API_KEY`
- Tier: Free

No automatic fallback model, retry policy, search grounding, tool use, file retrieval, or alternate provider path is part of this configuration.

## Security Notes

No API key value is recorded in this document.

Credentials must continue to come only from environment variables or approved runtime configuration. They must not be printed, logged, committed, or embedded in source code.

Free-tier Gemini data may be used by Google to improve its products, so future RAG generation tests must send only public SAP documentation excerpts and non-sensitive research questions.

## Non-Goals

This connectivity investigation did not:

- use retrieval held-out data
- run RAG answer-quality evaluation
- tune prompts
- change retrieval parameters
- change abstention thresholds
- change HANA tables
- change corpus, chunking, or embeddings
- integrate generation into `app.py`
- modify production application behavior
