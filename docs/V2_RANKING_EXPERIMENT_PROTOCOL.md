# Version 2 Retrieval Ranking Experiment Protocol

## Purpose

This protocol defines the first Version 2 retrieval-ranking experiment phase. The goal is to compare ranking variants on the pre-registered 48-query calibration set without changing the deployed corpus, chunking, embedding model, production search behavior, frozen test evidence, or recorded baseline results.

The experiment is calibration-only. The frozen V1/V2 evaluation sets remain held-out test evidence and must not be used for tuning or selecting retrieval parameters.

## Fixed Inputs

- Calibration dataset: `data/retrieval_calibration_v2.csv`
- Target table: `DOCUMENT_CHUNKS_V2`
- Dense embedding model: `BAAI/bge-small-en-v1.5`
- Dense vector dimension: 384
- Existing chunking and corpus contents
- Existing HANA cosine similarity behavior for the dense control

The experiment harness is read-only to HANA. It must not deploy HDI artifacts, ingest data, update `DOCUMENT_CHUNKS_V2`, or modify `DOCUMENT_CHUNKS`.

## Variants

### A: Dense Baseline

Variant A preserves the existing BGE query embedding plus HANA `COSINE_SIMILARITY` ranking behavior. It is the control condition and should reproduce the same retrieval method used by the pre-registered calibration baseline.

### B: Hybrid Retrieval

Variant B combines dense ranking with a local lexical BM25-style ranking over:

- `TITLE`
- `TOPIC`
- `CHUNK_TEXT`

The dense and lexical rankings are fused with Reciprocal Rank Fusion. This avoids arbitrary weighting between cosine scores and BM25 scores, which are on different scales.

### C: Dense Plus Cross-Encoder Reranking

Variant C starts from a broad dense candidate set so currently observed supported misses up to at least document rank 12 remain eligible. Candidate chunks are reranked with FastEmbed `TextCrossEncoder`.

Initial reranker:

- `Xenova/ms-marco-MiniLM-L-6-v2`

The reranker model name is configurable so another supported FastEmbed reranker can be tested later without changing the calibration dataset.

### D: Hybrid Plus Cross-Encoder Reranking

Variant D creates a union candidate pool from dense and lexical retrieval. The union is fused with Reciprocal Rank Fusion and then reranked with the same cross-encoder used in Variant C.

Final evaluation remains document-level: chunk results are deduplicated to document rankings before computing metrics.

## Metrics And Output

Each variant reports separately:

- Top-1 accuracy on supported calibration questions
- Top-3 accuracy on supported calibration questions
- Top-5 accuracy on supported calibration questions
- MRR on supported calibration questions
- Total retrieval/reranking latency
- Component latency for dense embedding, dense HANA retrieval, lexical ranking, and cross-encoder reranking where applicable
- Per-query expected document rank
- Per-query Top-5 document IDs

For all 48 questions, including the 16 unsupported questions, the harness preserves:

- Rank-1 document
- Rank-1 score
- Rank-2 document
- Rank-2 score
- Rank-1/rank-2 margin
- Top-5 document IDs

Unsupported questions do not receive invented correct documents. Their retrieval signals are recorded only for later abstention calibration.

## Comparison Rules

Variant A is the baseline for per-query movement analysis. Variants B, C, and D must report whether each individual calibration question improves, regresses, or remains unchanged relative to the dense baseline expected-document rank.

No variant may be selected as final based on the frozen V1/V2 test evidence. Final retrieval and RAG evaluation will require a separate approved held-out procedure.

## Explicit Non-Goals

This phase does not:

- choose or implement an abstention threshold
- implement production reranking in `app.py`
- implement production hybrid retrieval in `app.py`
- change chunking
- change the corpus
- change the embedding model
- modify evaluation labels
- implement an LLM
- implement RAG generation

## First-Step Validation

For this first step, only static and local validation is allowed. The 48-query variant comparison must not be run against HANA until the experiment harness and protocol are reviewed.
