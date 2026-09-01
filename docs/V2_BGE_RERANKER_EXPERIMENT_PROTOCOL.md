# Version 2 BGE Reranker Experiment Protocol

## Purpose

This protocol pre-registers the final planned reranker-model comparison before selecting a Version 2 retrieval architecture. The experiment reuses the approved retrieval-variant harness and changes only the cross-encoder reranker model used by variants C and D.

No frozen V1 or V2 test set is used for model selection. The existing V1/V2 evaluation sets remain frozen test evidence and are not tuning inputs.

After this experiment, retrieval pipeline selection should proceed and reranker-model exploration should stop unless a technical failure invalidates the experiment.

## Fixed Inputs

- Calibration dataset: `data/retrieval_calibration_v2.csv`
- Calibration set size: 48 queries
- Supported calibration queries: 32
- Unsupported calibration queries: 16
- Target table: `DOCUMENT_CHUNKS_V2`
- Dense embedding model: `BAAI/bge-small-en-v1.5`
- Dense vector dimension: 384
- Existing corpus, source mappings, chunking, HANA table, and stored embeddings
- Dense candidate chunks: 50
- Lexical candidate chunks: 50
- Reciprocal Rank Fusion k: 60

The experiment must not modify the calibration data, corpus, chunking, embeddings, HANA table, production `app.py`, frozen evaluation datasets, or recorded baseline evidence.

## Variants

### A: Dense Baseline Control

Variant A preserves the existing dense BGE query embedding plus HANA `COSINE_SIMILARITY` ranking behavior. It remains a control and does not use a reranker.

### B: Hybrid RRF Control

Variant B preserves the approved hybrid retrieval behavior: dense ranking plus local BM25-style lexical ranking over `TITLE`, `TOPIC`, and `CHUNK_TEXT`, fused with Reciprocal Rank Fusion. It remains a control and does not use a reranker.

### C: Dense Plus BGE Cross-Encoder Reranking

Variant C uses the same 50 dense candidate chunks as the MiniLM experiment, then reranks those chunks with FastEmbed `TextCrossEncoder` using:

- `BAAI/bge-reranker-base`

### D: Hybrid Plus BGE Cross-Encoder Reranking

Variant D uses the same union candidate pool from 50 dense chunks and 50 lexical chunks, applies the same RRF candidate-generation behavior, then reranks with:

- `BAAI/bge-reranker-base`

Final metrics remain document-level after chunk results are deduplicated to document rankings.

## Metrics And Required Evidence

For supported questions, each variant must report:

- Top-1 accuracy
- Top-3 accuracy
- Top-5 accuracy
- MRR
- Mean retrieval/reranking latency
- Mean reranker latency where applicable
- Per-query expected-document rank
- Per-query Top-5 documents

For reranking variants C and D, candidate recall must still be recorded before reranking so candidate-generation failures can be separated from reranker-ordering failures.

For all 48 questions, including unsupported questions, the output must preserve:

- Rank-1 document
- Rank-1 score
- Rank-2 document
- Rank-2 score
- Rank-1/rank-2 margin
- Top-5 document IDs

Unsupported signals are preserved only for later abstention calibration. No abstention threshold is selected in this experiment.

Cosine similarity scores, RRF scores, and cross-encoder scores are on different scales and must not be compared numerically across variants. Variant comparison must use document ranks, Top-5 document IDs, candidate recall, aggregate metrics, and latency.

## Execution Rule

Run the existing approved harness:

```powershell
cf run-task btp-doc-assistant-app --command "V2_RERANKER_MODEL_NAME=BAAI/bge-reranker-base python scripts/evaluate_retrieval_variants_v2.py" --name evaluate-v2-bge-reranker-experiment -m 3G
```

The Cloud Foundry task memory allocation is 3G because `BAAI/bge-reranker-base` is substantially larger than the previous MiniLM reranker. Production app memory must not be changed.

If the model fails to load because of memory, model availability, download, or another technical runtime issue, stop and report the exact command and error. Do not change the model or experiment parameters.

## Non-Goals

This experiment does not:

- select or implement the production retrieval architecture
- choose or implement an abstention threshold
- implement production reranking
- implement production hybrid retrieval
- change candidate sizes
- change RRF configuration
- change calibration data
- change corpus content
- change chunking
- change embeddings
- change `DOCUMENT_CHUNKS_V2`
- change production `app.py`
- use frozen V1/V2 test sets for tuning
- implement an LLM
- implement RAG
