# Version 2 RAG Provider-Error Retry Protocol

## Purpose

This protocol defines a strictly secondary retry harness for the Version 2 RAG development run provider errors. The secondary retry isolates provider availability after primary Gemini `429 RESOURCE_EXHAUSTED` failures.

The canonical primary result file remains:

`data/rag_development_primary_results_v2.csv`

That primary file is immutable. Retry outputs must not overwrite, replace, reinterpret, or retroactively alter the primary outcomes.

## Primary Run Status

The frozen primary RAG development run completed successfully as a Cloud Foundry task.

Canonical primary outcomes:

- Total queries: `24`
- `PIPELINE_ABSTAIN`: `8`
- Gemini calls: `16`
- `GENERATED_ANSWER`: `5`
- `LLM_REFUSAL`: `2`
- `PROVIDER_ERROR`: `9`
- Provider-error type: Gemini `429 RESOURCE_EXHAUSTED`
- Cloud Foundry primary task state: `SUCCEEDED`

Gemini `429 RESOURCE_EXHAUSTED` is treated as provider-capacity or quota behavior and is recorded separately from answer quality.

## Retry Scope

The secondary harness reads the canonical primary file and selects only rows where:

`OUTCOME == PROVIDER_ERROR`

The selected query IDs must be exactly:

- `RAGDEV008`
- `RAGDEV009`
- `RAGDEV011`
- `RAGDEV012`
- `RAGDEV013`
- `RAGDEV014`
- `RAGDEV015`
- `RAGDEV016`
- `RAGDEV019`

Any mismatch must stop the retry harness before provider execution.

## Frozen Configuration

The retry does not rerun retrieval. It reuses the exact `QUESTION` and serialized `CONTEXTS` stored in the canonical primary result file for each selected provider-error row.

`CONTEXTS` are parsed with safe literal parsing and validated as a non-empty list of dictionaries before any provider call. Malformed contexts must stop the retry before Gemini is called.

The retry must not change:

- questions
- reference facts
- retrieval architecture
- BGE model
- HANA table
- BM25 implementation
- RRF
- `RRF k = 60`
- dense top-1 gate `0.75`
- Top-5 context rule
- Gemini model `gemini-3.5-flash`
- grounding/refusal prompt
- provider parameters
- outcome classification

The retry must not run:

- `fetch_corpus_chunks`
- `fetch_dense_chunks`
- HANA retrieval
- BM25
- RRF
- the `0.75` gate
- `build_rag_contexts_from_hybrid_results`
- `evaluate_question`

## Execution Policy

Exactly one secondary retry attempt is allowed for each of the nine selected provider-error cases.

No automatic retry loop, backoff loop, fallback model, alternate provider, or prompt variant is allowed.

Pipeline-abstained primary questions and primary non-provider-error questions cannot be retried by this harness.

Retry output is written to stdout using secondary-specific fields that distinguish retry evidence from primary evidence:

- `QUERY_ID`
- `QUESTION`
- `PRIMARY_OUTCOME`
- `PRIMARY_CONTEXT_DOCUMENT_IDS`
- `RETRY_OUTCOME`
- `RETRY_GEMINI_ANSWER_OR_REFUSAL`
- `RETRY_PROVIDER_ERROR`
- `RETRY_GENERATION_MS`

Any saved retry evidence must be stored separately from the canonical primary result file.

## Evidence Interpretation

The secondary retry exists only as infrastructure recovery evidence for provider-side `429 RESOURCE_EXHAUSTED` outcomes.

Retry results must be analyzed separately from the primary canonical run. They may help explain whether provider-capacity failures blocked answer observation, but they do not erase or replace the original primary `PROVIDER_ERROR` outcomes.

No RAG answer-quality conclusions should merge primary and secondary outputs without explicitly preserving this distinction.
