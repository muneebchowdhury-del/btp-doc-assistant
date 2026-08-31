# RAG Version 2 Development Log

Version 1 baseline:
`v1-semantic-retrieval`

Development branch:
`rag-v2`

---

## Development Entries

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
