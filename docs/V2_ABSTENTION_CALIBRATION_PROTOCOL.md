# Version 2 Abstention Calibration Protocol

## Purpose

This protocol pre-registers confidence and abstention calibration for the fixed Version 2 retrieval pipeline. The goal is to study whether available retrieval signals can separate supported questions from unsupported near-domain and clearly out-of-scope questions before any production abstention behavior is implemented.

The calibration set remains the existing 48-query development/calibration dataset:

- 32 supported questions
- 16 unsupported questions

The frozen V1 and V2 evaluation sets remain frozen test evidence. They must not be used for threshold selection, abstention tuning, or retrieval architecture selection.

## Frozen Retrieval Architecture

The selected retrieval architecture for this calibration phase is fixed as:

- dense retrieval with `BAAI/bge-small-en-v1.5`
- lexical BM25-style retrieval over `TITLE`, `TOPIC`, and `CHUNK_TEXT`
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

The approved candidate sizes remain:

- dense candidate chunks: 50
- lexical candidate chunks: 50
- RRF k: 60

## Calibration Signals

The analysis harness may evaluate only signals that already exist or can be derived without changing retrieval:

- dense top-1 cosine score
- dense top-1/top-2 document-level cosine margin
- hybrid rank-1/rank-2 document-level RRF margin
- agreement between dense rank-1 document and hybrid rank-1 document
- whether the same document has support from multiple high-ranking chunks
- combinations of these signals

The multiple-chunk support signal is diagnostic only. It should count how many high-ranking chunks support the rank-1 document without changing the retrieved ranking.

## Calibration Objective

Candidate abstention rules should distinguish three outcomes:

- supported questions that should be accepted
- unsupported near-domain questions that should be abstained
- clearly out-of-scope questions that should be abstained

No single absolute threshold should be assumed sufficient. The calibration output should show how individual and combined signals behave across supported, unsupported near-domain, and unsupported out-of-scope questions.

## Required Reporting

For every candidate rule, report confusion-matrix or equivalent metrics:

- true accepts
- false accepts
- true abstentions
- false rejects
- accept precision
- supported accept recall
- unsupported abstain rate
- near-domain unsupported abstain rate
- out-of-scope unsupported abstain rate

The output must explicitly list:

- false accepts
- false rejects
- per-query signal values

Unsupported questions must not be assigned invented correct documents.

## Non-Goals

This phase does not:

- choose a production abstention threshold
- implement production abstention
- modify production retrieval
- add a cross-encoder reranker
- add hybrid changes beyond the already selected Dense plus BM25-style plus RRF architecture
- modify corpus, chunking, embeddings, RRF k, HANA tables, or `app.py`
- use frozen V1/V2 evaluation sets for tuning
- implement an LLM
- implement RAG

## First-Step Validation

For this first step, create and review the protocol and analysis harness only. Do not run the 48-query abstention calibration against HANA until the protocol and harness are reviewed.
