# Version 2 RAG Prompt Confirmation Provider Recovery Protocol

## Purpose

This protocol pre-registers a provider-only recovery harness for the three provider errors observed during the Version 2 RAG prompt-refinement confirmation run.

The original 16-query prompt-refinement confirmation remains canonical development evidence. Recovery results are secondary infrastructure-recovery evidence only.

## Canonical Confirmation Evidence

Canonical confirmation evidence is stored in:

`data/rag_prompt_refinement_confirmation_results_v2.csv`

The confirmation run produced:

- 16 provider-call candidates from the accepted primary RAG development rows;
- 13 observable provider responses;
- 3 provider errors.

The provider errors occurred only for:

- `RAGDEV015`
- `RAGDEV016`
- `RAGDEV019`

All three failed because Gemini reported `429 RESOURCE_EXHAUSTED` for the free-tier daily/project/model quota:

- quota ID: `GenerateRequestsPerDayPerProjectPerModel-FreeTier`
- quota value: `20`
- model: `gemini-3.5-flash`

This daily/project/model quota is distinct from the earlier 5-requests-per-minute quota observed during the primary RAG development run. Request pacing can reduce per-minute quota failures, but it cannot prevent a daily/project/model request ceiling. No reset timing is inferred beyond the provider error itself.

## Recovery Scope

This recovery run is infrastructure-only. It does not change or reinterpret answer-quality evidence.

Exactly three cases are eligible:

- `RAGDEV015`
- `RAGDEV016`
- `RAGDEV019`

Each eligible row must have `CONFIRMATION_OUTCOME == PROVIDER_ERROR` in the canonical confirmation CSV.

## Frozen Inputs

For each eligible case, the recovery harness reuses exactly the preserved:

- `QUERY_ID`
- `QUESTION`
- `CONTEXTS`
- `PRIMARY_CONTEXT_DOCUMENT_IDS`

`CONTEXTS` is parsed safely with `ast.literal_eval` and must be a non-empty list of dictionaries. Contexts are not rebuilt, reordered, regenerated, or retrieved again.

The harness must not run:

- HANA retrieval;
- dense search;
- BM25;
- Reciprocal Rank Fusion;
- threshold computation;
- context rebuilding;
- the 16-query confirmation harness.

## Generation Configuration

The recovery uses the unchanged provider interface:

`generate_grounded_answer(question, contexts)`

The same currently refined prompt, same Gemini model `gemini-3.5-flash`, same provider, and same generation configuration are used.

There is exactly one recovery provider attempt per eligible case.

The recovery uses no:

- automatic retry;
- backoff;
- fallback provider;
- fallback model.

If a recovery provider request fails, the case remains `PROVIDER_ERROR` in the recovery output and is not retried.

## Output

Recovery results are written to stdout as CSV and must be captured separately if executed later.

The planned live output file is:

`data/rag_prompt_confirmation_provider_recovery_results_v2.csv`

This protocol and harness do not create that live output file.

Recovery output must never overwrite or retroactively alter:

- `data/rag_prompt_refinement_confirmation_results_v2.csv`
- `data/rag_development_primary_results_v2.csv`
- `data/rag_development_provider_retry_results_v2.csv`
- `data/rag_development_scoring_v2.csv`
- `data/rag_development_scoring_with_retry_v2.csv`

## Decision Boundary

No prompt decision is made until `RAGDEV019` becomes observable or remains a documented provider failure.

This recovery is development evidence, not final holdout evidence. It must not be treated as final end-to-end RAG evaluation.

## Non-Execution Confirmation

Creating the harness and protocol does not:

- call Gemini;
- query HANA;
- run retrieval;
- execute the recovery harness live;
- modify `llm_provider.py`;
- modify any canonical CSV evidence;
- modify retrieval, abstention, model, prompt, or production `app.py`.
