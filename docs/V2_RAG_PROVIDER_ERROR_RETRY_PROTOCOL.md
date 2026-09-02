# Version 2 RAG Provider-Error Retry Protocol

## Purpose

This protocol defines a strictly secondary retry harness for the Version 2 RAG development run provider errors.

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

Any mismatch must stop the retry harness before retrieval or provider execution.

## Frozen Configuration

The retry uses the existing frozen `evaluate_question` implementation from `scripts/evaluate_rag_development_v2.py`.

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

## Execution Policy

Exactly one secondary retry attempt is allowed for each of the nine selected provider-error cases.

No automatic retry loop, backoff loop, fallback model, alternate provider, or prompt variant is allowed.

Pipeline-abstained primary questions and primary non-provider-error questions cannot be retried by this harness.

Retry output is written to stdout using the primary result CSV schema where possible. Any saved retry evidence must be stored separately from the canonical primary result file.

## Evidence Interpretation

The secondary retry exists only as infrastructure recovery evidence for provider-side `429 RESOURCE_EXHAUSTED` outcomes.

Retry results must be analyzed separately from the primary canonical run. They may help explain whether provider-capacity failures blocked answer observation, but they do not erase or replace the original primary `PROVIDER_ERROR` outcomes.

No RAG answer-quality conclusions should merge primary and secondary outputs without explicitly preserving this distinction.
