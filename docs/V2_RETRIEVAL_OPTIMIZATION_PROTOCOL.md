# Version 2 Retrieval Optimization Protocol

## Purpose

This protocol starts the Version 2 retrieval optimization phase after the evaluated vector-only baseline was preserved with the `v2-retrieval-baseline` tag.

The goal of this phase is to create a development calibration set for future retrieval and abstention experiments without changing the deployed corpus, embedding model, chunking, retrieval algorithm, evaluation labels, or Version 1 files.

## Frozen Test Evidence

The existing evaluation evidence is now frozen test evidence:

- `data/evaluation_queries.csv`
- `data/evaluation_queries_v2_foundation.csv`
- `docs/V2_EVALUATION_PROTOCOL.md`
- `docs/V2_DEPLOYMENT_EVIDENCE.md`
- Git tag `v2-retrieval-baseline`

These evaluation sets and recorded results will not be used for tuning retrieval parameters, choosing abstention thresholds, selecting rerankers, or adjusting source mappings.

The frozen Version 1 metrics and conclusions remain unchanged.

## Calibration Dataset

`data/retrieval_calibration_v2.csv` is a development and calibration dataset.

It contains 48 fresh questions written before observing retrieval results for those questions:

- 32 supported questions grounded in the current Version 2 corpus
- 16 unsupported questions for future abstention calibration

Supported questions include semantically overlapping SAP BTP areas such as platform overview, basic concepts, account model, entitlements and quotas, regions, tools, getting started, Cloud Foundry concepts, services, service bindings, routes, destinations, and environment variables.

Unsupported questions include near-domain SAP or BTP questions where the current indexed corpus is not expected to contain sufficient answer evidence, plus clearly out-of-scope questions.

Unsupported questions intentionally do not have an expected correct document. They are used to inspect retrieval signals such as rank-1 score, score margin, and retrieved document mix.

## Baseline Calibration Evaluation

`scripts/evaluate_retrieval_calibration_v2.py` evaluates only the existing vector-only baseline against `DOCUMENT_CHUNKS_V2`.

The script must not write to HANA. It records retrieval signals for both supported and unsupported questions.

For supported questions, it reports:

- Top-1
- Top-3
- Top-5
- MRR

For every question, it records:

- rank-1 document
- rank-1 score
- rank-2 document
- rank-2 score
- score margin between rank 1 and rank 2
- top-5 document IDs

## Out Of Scope For This Phase

This phase does not choose an abstention threshold.

This phase does not implement reranking, hybrid retrieval, an LLM, or RAG generation.

This phase does not modify source mappings, chunking, embeddings, retrieval logic, deployed corpus contents, or Version 1 files.

## Future Held-Out Evaluation

A separate fresh held-out set will later be created for final RAG evaluation.

That future held-out set should be created after retrieval optimization decisions are documented, and it should evaluate final source-grounded answer behavior separately from retrieval behavior.
