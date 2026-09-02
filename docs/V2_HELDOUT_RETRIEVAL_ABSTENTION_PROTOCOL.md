# Version 2 Fresh Held-Out Retrieval And Abstention Validation Protocol

## Purpose

This protocol defines a fresh held-out validation for the frozen Version 2 retrieval and candidate abstention gate. The purpose is to estimate retrieval quality, scope behavior, and answer-safety behavior on questions that were not used for Version 1 evaluation, Version 2 foundation evaluation, retrieval calibration, ranking experiments, or abstention calibration.

The held-out dataset must not be executed until this protocol, dataset, and evaluator have been reviewed.

## Dataset

Dataset file: `data/retrieval_abstention_heldout_v2.csv`

Composition:

- 40 total questions
- 24 supported questions
- 8 near-domain unsupported questions
- 8 clearly out-of-scope questions

The supported questions broadly cover the active Version 2 corpus:

- `DOC001` through `DOC007`
- `DOC009` through `DOC024`

The held-out questions are intentionally new and must not duplicate or closely paraphrase:

- `data/evaluation_queries.csv`
- `data/evaluation_queries_v2_foundation.csv`
- `data/retrieval_calibration_v2.csv`

No retrieval results may be inspected while creating or revising the held-out dataset.

## Pre-Execution Novelty Audit

Before any held-out retrieval execution, the dataset must pass a local novelty audit against:

- `data/evaluation_queries.csv`
- `data/evaluation_queries_v2_foundation.csv`
- `data/retrieval_calibration_v2.csv`

The audit must check:

- exact duplicate questions
- nearest prior question by normalized lexical overlap
- nearest prior question by local question-to-question embedding cosine similarity
- scenario-level or semantic closeness by manual review of the nearest lexical and semantic prior questions
- explicitly maintained `DISTINCT` or `TOO_SIMILAR` assessments with short rationales for all 40 held-out questions

The audit must not:

- query HANA
- retrieve corpus documents
- inspect retrieval scores
- execute the held-out evaluator

The approved pre-execution audit evidence is recorded in `docs/V2_HELDOUT_NOVELTY_AUDIT.md`. Manual assessments are maintained in `data/retrieval_abstention_heldout_v2_assessments.csv`; they must not be inferred automatically from exact-duplicate status. Every held-out question must have nearest prior query IDs, nearest prior questions, lexical and embedding similarity diagnostics, a manual assessment, and a rationale. Any question with a missing assessment or marked `TOO_SIMILAR` must be revised before execution.

## Frozen Candidate Configuration

The held-out evaluator must use exactly:

- Dense model: `BAAI/bge-small-en-v1.5`
- HANA table: `DOCUMENT_CHUNKS_V2`
- Dense retrieval: complete document chunk ranking by HANA `COSINE_SIMILARITY`
- Lexical retrieval: existing BM25-style implementation over `TITLE`, `TOPIC`, and `CHUNK_TEXT`
- Fusion: Reciprocal Rank Fusion over the complete dense and lexical chunk rankings
- `RRF k`: `60`
- Reranker: none
- Candidate abstention gate: accept only when dense document-level rank-1 cosine score is `>= 0.75`
- Below `0.75`: abstain

This validation must not modify:

- corpus
- chunking
- embeddings
- retrieval algorithm
- candidate abstention gate
- HANA tables
- production `app.py`
- frozen V1/V2 evaluation sets
- calibration dataset
- evaluation labels

## Required Retrieval Metrics

For supported held-out questions, report:

- Top-1
- Top-3
- Top-5
- MRR

For every question, preserve:

- dense rank-1 document
- dense rank-1 score
- dense rank-2 document
- dense rank-2 score
- dense rank-1/rank-2 margin
- hybrid rank-1 document
- hybrid rank-1 score
- hybrid rank-2 document
- hybrid rank-2 score
- hybrid rank-1/rank-2 margin
- hybrid expected document rank
- hybrid Top-5 document IDs
- dense/hybrid rank-1 agreement
- accept or abstain decision

## Required Abstention And Safety Metrics

Scope metrics:

- true accepts
- false accepts
- true abstentions
- false rejects
- accept precision
- supported accept recall
- unsupported abstain rate
- near-domain unsupported abstain rate
- out-of-scope unsupported abstain rate
- false-accept query IDs
- false-reject query IDs

Answer-safety metrics must be reported for both Top-3 and Top-5 context depths:

- safe accepts
- unsafe accepts
- false rejects of otherwise safe supported queries
- accepted-answer precision
- safe-answer recall
- coverage
- unsafe-accept query IDs
- safe-query false-reject IDs

Safety targets:

```javascript
SAFE_TO_ANSWER_TOP3 =
    EXPECTED_SUPPORTED == 1
    AND expected document rank <= 3

SAFE_TO_ANSWER_TOP5 =
    EXPECTED_SUPPORTED == 1
    AND expected document rank <= 5
```

Supported questions whose expected document ranks outside the context depth remain supported/in-scope for the scope analysis but count as unsafe to answer for that context depth.

## Non-Goals

This validation does not:

- tune the threshold
- add or compare additional candidate rules
- implement production abstention
- modify production retrieval
- add reranking
- add hybrid changes beyond the frozen selected architecture
- use the frozen V1/V2 test evidence for tuning
- use the calibration set for further threshold search
- implement an LLM
- implement RAG

## Execution

After review, execute:

```bash
python scripts/evaluate_retrieval_abstention_heldout_v2.py
```

If the held-out validation is run in Cloud Foundry, use the reviewed command exactly and stop immediately on technical, runtime, HANA, or model-loading failure rather than changing scientific parameters.
