# Version 2 Retrieval And Abstention Candidate Freeze

## Purpose

This document freezes the candidate retrieval and abstention configuration for fresh held-out validation. The calibration phase is complete, and no additional analysis or threshold search will be performed on the existing 48-query calibration dataset.

The configuration below is not a production threshold. It is a candidate rule selected for review through a fresh held-out retrieval and abstention validation run.

## Frozen Candidate Configuration

- Dense model: `BAAI/bge-small-en-v1.5`
- Lexical retrieval: existing BM25-style implementation over `TITLE`, `TOPIC`, and `CHUNK_TEXT`
- Fusion: full dense ranking plus full lexical ranking with Reciprocal Rank Fusion
- `RRF k`: `60`
- Reranker: none
- Candidate abstention gate: accept only when dense document-level top-1 cosine score is `>= 0.75`
- Below `0.75`: abstain

This freeze does not change:

- corpus
- chunking
- embeddings
- HANA tables
- retrieval SQL
- production `app.py`
- evaluation labels
- Version 1 files or results
- Version 2 frozen evidence

## Calibration Rationale

The candidate gate `DENSE_SCORE_GE_0.75` was selected for fresh held-out validation because it prioritized abstaining on unsupported questions during calibration:

- Calibration scope precision: `1.0000`
- Unsupported abstain rate: `1.0000`
- Near-domain abstain rate: `1.0000`
- Out-of-scope abstain rate: `1.0000`
- Supported accept recall: `0.6562`
- Top-3 accepted-answer precision: `0.9524`
- Top-3 safe-answer recall: `0.6452`
- Coverage: `0.4375`

Known calibration failure:

- `CAL031` remained an accepted but unsafe retrieval failure. The expected document was outside the evaluated answer context depth. This failure is documented as evidence and must not be tuned against with additional calibration-set threshold search.

## Decision Boundary

This freeze authorizes only a fresh held-out validation of the candidate configuration. It does not authorize production implementation, further calibration on the existing 48-query set, LLM generation, RAG, reranking, corpus changes, or threshold tuning.

Final production selection still requires review of the fresh held-out validation results.
