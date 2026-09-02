# Version 2 Abstention Calibration Protocol

## Purpose

This protocol pre-registers confidence and abstention calibration for the fixed Version 2 retrieval pipeline. The goal is to study whether available retrieval signals can separate supported questions from unsupported near-domain and clearly out-of-scope questions before any production abstention behavior is implemented.

The calibration set remains the existing 48-query development/calibration dataset:

- 32 supported questions
- 16 unsupported questions

The frozen V1 and V2 evaluation sets remain frozen test evidence. They must not be used for threshold selection, abstention tuning, or retrieval architecture selection.

## Frozen Retrieval Architecture

The selected retrieval architecture for this calibration phase is fixed as:

- dense retrieval with `BAAI/bge-small-en-v1.5` over the complete ranked chunk list
- lexical BM25-style retrieval over `TITLE`, `TOPIC`, and `CHUNK_TEXT` over the complete ranked chunk list
- Reciprocal Rank Fusion
- no cross-encoder reranker

This phase must not modify:

- corpus contents
- chunking
- embeddings
- RRF configuration
- calibration questions
- calibration labels
- HANA tables
- production `app.py`
- the experiment protocol

The calibration must reproduce the exact Hybrid Variant B behavior that generated the architecture-selection evidence. The 50 dense / 50 lexical values used during ranking experiments were reranker candidate-pool settings for variants C and D. They are not part of the selected no-reranker Hybrid RRF architecture and must not truncate the selected hybrid pipeline during abstention calibration.

RRF k remains fixed at 60.

## Calibration Signals

The analysis harness may evaluate only signals that already exist or can be derived without changing retrieval:

- dense top-1 cosine score
- dense top-1/top-2 document-level cosine margin
- hybrid rank-1/rank-2 document-level RRF margin
- agreement between dense rank-1 document and hybrid rank-1 document
- whether the same document has support from multiple high-ranking chunks
- combinations of these signals

The multiple-chunk support signal is diagnostic only. It should count how many high-ranking chunks support the rank-1 document without changing the retrieved ranking. The high-ranking chunk support window is fixed at 10 for this calibration run and must not be tuned after seeing results.

## Calibration Objective

Candidate abstention rules should distinguish three outcomes:

- supported questions that should be accepted
- unsupported near-domain questions that should be abstained
- clearly out-of-scope questions that should be abstained

A separate answer-safety view must distinguish whether an accepted query has enough retrieved evidence inside the context depth that would be passed to a later answer generator:

```javascript
SAFE_TO_ANSWER_TOP3 =
    EXPECTED_SUPPORTED == 1
    AND expected document rank <= 3

SAFE_TO_ANSWER_TOP5 =
    EXPECTED_SUPPORTED == 1
    AND expected document rank <= 5
```

A supported query whose expected document is outside the evaluated context depth remains supported/in-scope for scope analysis, but counts as unsafe-to-answer for the corresponding Top-k safety analysis. This does not change labels or retrieval; it evaluates the safety implication of retrieval quality.

No single absolute threshold should be assumed sufficient. The calibration output should show how individual and combined signals behave across supported, unsupported near-domain, and unsupported out-of-scope questions.

## Required Reporting

For every candidate rule, report confusion-matrix or equivalent metrics:

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

Top-3 answer-safety metrics:

- safe accepts at Top-3
- unsafe accepts at Top-3
- false rejects of otherwise safe Top-3 queries
- accepted-answer precision at Top-3
- safe-answer recall at Top-3
- coverage at Top-3

Top-5 answer-safety metrics:

- safe accepts at Top-5
- unsafe accepts at Top-5
- false rejects of otherwise safe Top-5 queries
- accepted-answer precision at Top-5
- safe-answer recall at Top-5
- coverage at Top-5

The output must explicitly list:

- false accepts
- false rejects
- Top-3 unsafe accepts
- Top-3 false rejects of otherwise safe questions
- Top-5 unsafe accepts
- Top-5 false rejects of otherwise safe questions
- per-query signal values

Unsupported questions must not be assigned invented correct documents.

## Non-Goals

This phase does not:

- choose a production abstention threshold
- implement production abstention
- modify production retrieval
- add a cross-encoder reranker
- add hybrid changes beyond the already selected Dense plus BM25-style plus RRF architecture
- tune the fixed 10-chunk support diagnostic window after observing results
- modify corpus, chunking, embeddings, RRF k, HANA tables, or `app.py`
- use frozen V1/V2 evaluation sets for tuning
- implement an LLM
- implement RAG

## First-Step Validation

For this first step, create and review the protocol and analysis harness only. Do not run the 48-query abstention calibration against HANA until the protocol and harness are reviewed.
