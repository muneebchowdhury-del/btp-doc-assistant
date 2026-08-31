# Version 2 Retrieval Evaluation Protocol

## Purpose

This protocol pre-registers the Version 2 retrieval evaluation before Version 2 deployment, ingestion, or observation of Version 2 retrieval results.

The goal is to evaluate whether the isolated Version 2 corpus improves foundation-level SAP BTP coverage while preserving comparability with the frozen Version 1 retrieval baseline.

## Evaluation Sets

### A. V1 Regression Set

The frozen Version 1 query set in `data/evaluation_queries.csv` is reused unchanged as a regression and comparability set.

This set keeps the original expected document IDs and is evaluated against `DOCUMENT_CHUNKS_V2`. Its purpose is to check whether the expanded Version 2 corpus still retrieves the original Version 1 documents for the existing 30 questions.

These results must not be used to reinterpret or overwrite the frozen Version 1 reported metrics.

### B. V2 Foundation Coverage Set

The held-out Version 2 foundation questions are defined in `data/evaluation_queries_v2_foundation.csv`.

This file contains exactly 16 questions: two natural user questions for each new Version 2 foundation document `DOC017` through `DOC024`.

These questions were written before deploying the Version 2 table, running Version 2 ingestion, or observing Version 2 retrieval output.

## Methodology

Both evaluation sets use the same retrieval methodology as Version 1:

- embedding model: `BAAI/bge-small-en-v1.5`
- query embedding method: `query_embed`
- vector dimension: 384
- HANA vector similarity: `COSINE_SIMILARITY`
- target table: `DOCUMENT_CHUNKS_V2`
- document-level deduplication: keep the first occurrence of each `DOCUMENT_ID` in chunk-score order

The two evaluation blocks are reported separately. Their metrics must not be combined into a single headline score.

## Metrics

Each evaluation block reports:

- Top-1 accuracy
- Top-3 accuracy
- Top-5 accuracy
- mean reciprocal rank
- mean query embedding time
- mean HANA retrieval time
- mean combined search time

The evaluator also prints per-query rankings for review and auditability.

## Constraints

The Version 2 evaluator is read-only with respect to HANA. It must not insert, update, delete, deploy, or ingest data.

No Version 1 files, Version 1 expected labels, Version 1 reported metrics, or historical Version 1 conclusions are changed by this protocol.
