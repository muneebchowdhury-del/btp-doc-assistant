# Version 2 RAG Development Scoring Protocol

## Purpose

This protocol defines the manual scoring framework for the frozen Version 2 RAG development experiment.

This is development-set evaluation, not the final end-to-end holdout. The development set may guide generation-layer decisions only. Retrieval architecture, corpus, chunking, embeddings, BM25, RRF, `RRF k = 60`, and the `0.75` preliminary gate are frozen and cannot be tuned from these results.

The already-used retrieval heldout cannot be reused for generation tuning. After the generation architecture is finalized, a completely fresh, preregistered end-to-end RAG evaluation is mandatory.

Human/manual evaluation is used instead of an LLM-as-judge to avoid adding another model-dependent evaluation layer.

## Evidence Boundary

Primary evidence is read from:

`data/rag_development_primary_results_v2.csv`

The canonical primary result file remains immutable:

- Total queries: `24`
- `PIPELINE_ABSTAIN`: `8`
- Gemini attempts: `16`
- `GENERATED_ANSWER`: `5`
- `LLM_REFUSAL`: `2`
- `PROVIDER_ERROR`: `9`
- Provider-error type: Gemini `429 RESOURCE_EXHAUSTED`

Provider errors are infrastructure/provider availability evidence, not answer quality.

An optional secondary provider-error retry file may be supplied later, for example:

`data/rag_development_provider_retry_results_v2.csv`

Primary and secondary retry evidence must remain separate. Retry outputs must never overwrite primary outcomes, and retry answers must not be silently substituted for primary answers. Secondary retry outputs remain secondary recovery evidence.

`REFERENCE_FACT` is offline evaluation evidence only. It must never be sent to Gemini or used to alter retrieval, context selection, prompting, or gate decisions.

## Prepared Scoring Rows

`scripts/prepare_rag_development_scoring_v2.py` prepares manual scoring rows from the immutable primary CSV. If an optional retry file is explicitly supplied, it adds separately labelled `SECONDARY_RETRY` scoring rows.

The preparation script preserves:

- `QUERY_ID`
- `QUESTION`
- `EXPECTED_SUPPORTED`
- `EXPECTED_DOCUMENT_ID`
- `CATEGORY`
- `REFERENCE_FACT`
- `DENSE_RANK1_DOCUMENT_ID`
- `DENSE_RANK1_SCORE`
- `ACCEPT_DECISION`
- `HYBRID_TOP5_DOCUMENTS`
- `CONTEXT_DOCUMENT_IDS`
- `CONTEXTS`
- primary `OUTCOME`
- primary answer/refusal
- primary provider error
- retrieval latency fields
- generation latency fields
- total latency fields

For optional retry evidence, the script validates that the retry file contains only the nine preregistered primary provider-error IDs and exposes retry fields under `SECONDARY_RETRY_*` columns.

## Context Diagnostics

The preparation script derives deterministic offline diagnostics:

`EXPECTED_DOC_IN_CONTEXT`

- `1` if `EXPECTED_DOCUMENT_ID` occurs in `CONTEXT_DOCUMENT_IDS`
- `0` if it does not
- blank for unsupported queries

`EXPECTED_DOC_CONTEXT_RANK`

- rank within `CONTEXT_DOCUMENT_IDS`
- blank if absent or unsupported

These diagnostics are for evaluation interpretation only. They do not change retrieval or generation behavior.

## Pipeline Outcome Assessment

Pipeline behavior is assessed separately from answer quality.

`PIPELINE_DECISION_ASSESSMENT` values:

- `CORRECT_ACCEPT`
- `INCORRECT_ACCEPT`
- `CORRECT_ABSTAIN`
- `INCORRECT_ABSTAIN`
- `NOT_ASSESSED`

`GENERATION_OBSERVABILITY` values:

- `OBSERVED`
- `PROVIDER_ERROR`
- `NOT_CALLED`

`PROVIDER_ERROR` must not be classified as an incorrect answer, hallucination, or refusal.

## Manual Scoring Rubric

Do not invent automatic scores. Manual scoring fields start blank with `SCORING_STATUS = UNSCORED`.

`GROUNDEDNESS`

- `1` = all substantive answer claims are supported by the supplied retrieved contexts
- `0` = one or more substantive claims are unsupported by the supplied contexts
- blank = not applicable / no observable LLM output

`ANSWER_CORRECTNESS`

- `1` = answer semantically conveys the preregistered `REFERENCE_FACT` when the evidence is sufficient
- `0` = answer does not correctly convey the expected fact despite sufficient evidence
- blank = not applicable, provider error, or legitimate refusal where the expected fact is not supported by supplied evidence

`CITATION_CORRECTNESS`

- `1` = cited document IDs / URLs correspond to supplied contexts and support the associated claims
- `0` = citation is missing where required, references an unsupplied source, invents a source/URL, or does not support the associated claim
- blank = no generated substantive answer where citation scoring is not applicable

`HALLUCINATION`

- `1` = answer invents or introduces unsupported factual claims, SAP features, commands, configuration steps, URLs, plans, service names, etc.
- `0` = no unsupported invention detected
- blank = provider error / pipeline abstain where no generated answer exists

`EVIDENCE_BASED_REFUSAL`

- `1` = refusal is appropriate because supplied evidence is insufficient
- `0` = refusal is inappropriate because supplied evidence sufficiently supports the requested answer
- blank = output is not an LLM refusal

`CONCISION`

- `2` = concise and directly answers/refuses
- `1` = understandable but unnecessarily verbose/repetitive
- `0` = substantially unfocused or unnecessarily long
- blank = no observable LLM output

Additional fields:

- `EVALUATOR_NOTES`
- `SCORING_STATUS = UNSCORED / SCORED`
- `EVIDENCE_SOURCE = PRIMARY / SECONDARY_RETRY`

## Summary Rules

`scripts/summarize_rag_development_scoring_v2.py` operates only on a completed manually scored file.

It refuses to report final answer-quality metrics if applicable observable LLM-output rows remain `UNSCORED`.

It reports separately:

- primary pipeline outcomes
- provider reliability for primary evidence
- provider reliability for secondary retry evidence, if present
- manually scored observable LLM outputs

All denominators must be printed explicitly. Blank or not-applicable values are excluded from denominators and must never be treated as zero.

Primary and secondary evidence must not be combined into one headline metric unless a separately labelled descriptive combined view is explicitly produced. Primary evidence must always remain identifiable.

## Non-Goals

This scoring framework does not:

- fill manual score values
- call Gemini
- execute the provider-error retry
- query HANA
- execute retrieval
- modify the primary result CSV
- change retrieval, generation, prompts, models, thresholds, corpus, HANA tables, or application behavior
