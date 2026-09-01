# RAG Version 2 Development Log

Version 1 baseline:
`v1-semantic-retrieval`

Development branch:
`rag-v2`

---

## Development Entries

### Task 4: Retrieval ranking experiment harness

Changed:
- Added `scripts/evaluate_retrieval_variants_v2.py` to compare dense baseline, hybrid RRF, dense cross-encoder reranking, and hybrid cross-encoder reranking on the 48-query calibration set.
- Added `docs/V2_RANKING_EXPERIMENT_PROTOCOL.md` to document the four variants, fixed inputs, comparison rules, metrics, and explicit non-goals.
- Revised the experimental candidate pools to 50 dense chunks and 50 lexical chunks, and added supported-query candidate-recall diagnostics before reranking.

Why:
- Retrieval ranking changes need a separate experimental harness before any production search behavior changes are considered.
- Dense, lexical, and reranked variants must be compared against the same pre-registered calibration data while preserving frozen V1/V2 test evidence.
- Unsupported calibration queries need retrieval signals preserved for later abstention work without selecting a threshold yet.
- Candidate size is a calibration-time design parameter, and score values from cosine similarity, BM25-style ranking, RRF, and cross-encoder reranking must not be compared numerically across variants.

### Task 3: Retrieval optimization pre-registration and calibration set

Changed:
- Added `data/retrieval_calibration_v2.csv` with 48 fresh development/calibration questions: 32 supported questions and 16 unsupported questions.
- Added `docs/V2_RETRIEVAL_OPTIMIZATION_PROTOCOL.md` to document the separation between frozen test evidence, calibration data, and future held-out RAG evaluation.
- Added `scripts/evaluate_retrieval_calibration_v2.py` to evaluate the existing vector-only baseline against `DOCUMENT_CHUNKS_V2` and record retrieval signals for calibration.

Why:
- Retrieval and abstention parameters need a development set that is separate from frozen V1/V2 test evidence.
- Unsupported calibration questions need retrieval signals before any abstention threshold is selected.
- Baseline calibration must be captured before introducing reranking, hybrid retrieval, LLM generation, or RAG behavior.

### Task 2: V2 retrieval evaluation pre-registration

Changed:
- Added `data/evaluation_queries_v2_foundation.csv` with exactly 16 held-out foundation questions for `DOC017` through `DOC024`.
- Added `scripts/evaluate_retrieval_v2.py` to evaluate `DOCUMENT_CHUNKS_V2` with separate V1 regression and V2 foundation coverage blocks.
- Added `docs/V2_EVALUATION_PROTOCOL.md` documenting the pre-registered methodology and separation between regression and foundation coverage results.

Why:
- Version 2 retrieval evaluation must be fixed before deployment, ingestion, or observation of Version 2 retrieval output.
- The frozen Version 1 query set remains useful for regression and comparability, but its results must stay separate from Version 2 foundation coverage results.
- The Version 2 evaluator preserves the Version 1 embedding model, HANA cosine similarity, and document-level deduplication methodology while reading only from `DOCUMENT_CHUNKS_V2`.

### Task 1: V2 corpus and HANA table foundation

Changed:
- Added `data/document_sources_v2.csv` as an isolated Version 2 source catalog based on the Version 1 catalog.
- Added eight official SAP BTP foundation and overview documents to the Version 2 catalog so broad platform questions, including "What is SAP BTP?", have relevant source material.
- Added `db/src/DOCUMENT_CHUNKS_V2.hdbtable` as a separate HDI table artifact with the same core structure as `DOCUMENT_CHUNKS` and `REAL_VECTOR(384)`.
- Added `scripts/ingest_documents_v2.py` to ingest only `data/document_sources_v2.csv` into `DOCUMENT_CHUNKS_V2`.

Why:
- Version 1 must remain frozen and reproducible.
- Version 2 needs an isolated corpus and table foundation before adding generation, reranking, hybrid search, or abstention.
- The embedding model, vector dimension, and initial chunking settings are intentionally unchanged so corpus coverage can be studied before changing retrieval variables.
