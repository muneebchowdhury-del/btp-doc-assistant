# Codex Version 2 Architecture Review

## 1. Current Version 1 Architecture

Version 1 is a semantic retrieval assistant for selected SAP BTP documentation. It is intentionally frozen and should remain reproducible.

Current runtime architecture:

```text
Browser
-> Flask on SAP BTP Cloud Foundry
-> FastEmbed BAAI/bge-small-en-v1.5
-> 384-dimensional query embedding
-> SAP HANA Cloud / HDI
-> DOCUMENT_CHUNKS
-> COSINE_SIMILARITY
-> ranked SAP documentation passages
```

The system does not currently generate natural-language answers. It retrieves and displays the most semantically similar documentation chunks.

Frozen Version 1 configuration:

- 15 indexed SAP BTP documents
- 5,788 cleaned words
- 64 chunks
- chunk size: 120 words
- overlap: 25 words
- vector dimension: 384
- embedding model: `BAAI/bge-small-en-v1.5`

Frozen Version 1 evaluation:

- 30 queries
- Top-1: 66.67%
- Top-3: 96.67%
- Top-5: 100%
- MRR: 0.8083

## 2. Important Files and Responsibilities

`app.py`

The Flask runtime application. It handles the web UI, HANA connection setup, lazy embedding model initialization, query embedding, vector search, result rendering, and diagnostic endpoints.

`Procfile`

Defines the Cloud Foundry web process:

```text
web: gunicorn --bind 0.0.0.0:$PORT app:app
```

`requirements.txt`

Defines Python runtime dependencies: Flask, Gunicorn, HANA client, FastEmbed, Requests, and BeautifulSoup.

`data/document_sources.csv`

The curated source catalog. It maps logical document IDs to SAP documentation titles, topics, SAP Help URLs, and raw Markdown content URLs.

`data/evaluation_queries.csv`

The fixed retrieval evaluation dataset. Each row maps a query to the expected source document ID.

`scripts/ingest_documents.py`

The production ingestion script for Version 1. It loads source metadata, downloads raw Markdown, cleans and chunks text, generates embeddings, and replaces the contents of `DOCUMENT_CHUNKS`.

`scripts/evaluate_retrieval.py`

The formal Version 1 retrieval evaluation script. It measures document-ranking quality using Top-1, Top-3, Top-5, MRR, and timing metrics.

`scripts/validate_sources.py`

Checks whether configured raw content URLs are reachable and return enough text.

`scripts/validate_chunking.py`

Reports word and chunk counts using the Version 1 chunking approach.

`scripts/test_markdown_extraction.py`, `scripts/test_chunking.py`, `scripts/test_semantic_search.py`, `scripts/test_source_extraction.py`

Exploratory validation scripts for extraction, chunking, and semantic search behavior.

`scripts/resolve_btp_source.py`, `scripts/resolve_all_btp_sources.py`

Utilities for resolving SAP Help pages to raw Markdown files in the SAP documentation GitHub repository. `resolve_all_btp_sources.py` writes back to `data/document_sources.csv` and should not be run when preserving Version 1 evidence.

`db/src/DOCUMENT_CHUNKS.hdbtable`

The HDI table artifact for the HANA vector store. It defines chunk metadata, source fields, chunk text, and a `REAL_VECTOR(384)` embedding column.

`db/package.json`

Defines the HDI deployer dependency on `@sap/hdi-deploy`.

`db/manifest.yml`

Defines the Cloud Foundry HDI deployer application bound to the `btp-doc-assistant-hdi` service.

## 3. Current Ingestion Flow

The ingestion flow is implemented in `scripts/ingest_documents.py`.

1. Load source rows from `data/document_sources.csv`.
2. Skip rows without a `CONTENT_URL`.
3. Download raw Markdown from each configured content URL.
4. Clean Markdown by removing metadata comments, images, Markdown link targets, headings, common formatting markers, HTML tags, escaped Markdown characters, blockquote markers, and navigation-heavy related information.
5. Split cleaned text into 120-word chunks with 25-word overlap.
6. Generate passage embeddings with FastEmbed using `BAAI/bge-small-en-v1.5`.
7. Read HANA credentials from `VCAP_SERVICES`.
8. Connect to the HDI-bound SAP HANA Cloud instance.
9. Set the schema from the HDI service binding.
10. Delete existing rows from `DOCUMENT_CHUNKS`.
11. Insert each chunk with metadata, text, timestamp, and `TO_REAL_VECTOR(?)`.

This is a full-refresh ingestion process. It is simple and reproducible, but it is not incremental.

## 4. Current Runtime Retrieval Flow

The runtime retrieval flow is implemented in `app.py`.

1. The user submits a question through the Flask form at `/`.
2. `semantic_search(question, top_k=5)` clamps the requested result count between 1 and 10.
3. The FastEmbed model generates a query embedding with `query_embed`.
4. The app connects to HANA through the bound HDI service.
5. SQL computes similarity with:

```sql
COSINE_SIMILARITY("EMBEDDING", TO_REAL_VECTOR(?))
```

6. Results are ordered by descending similarity score.
7. The UI displays the title, topic, document ID, source URL, chunk text, and similarity score.

The returned result is a ranked set of source passages. No answer synthesis, citation formatting, reranking, score thresholding, or abstention logic is currently applied.

## 5. HANA / HDI Integration

SAP HANA Cloud is used as the vector store. HDI is used to manage the database artifact.

The `DOCUMENT_CHUNKS` table contains:

- `CHUNK_ID`: primary key
- `DOCUMENT_ID`: source document identifier
- `CHUNK_INDEX`: chunk position within the document
- `TITLE`: source title
- `TOPIC`: source topic
- `SOURCE_URL`: SAP Help source URL
- `CHUNK_TEXT`: cleaned passage text
- `EMBEDDING`: `REAL_VECTOR(384)`
- `INGESTED_AT`: ingestion timestamp

Both ingestion and runtime expect the same bound HDI service name:

```text
btp-doc-assistant-hdi
```

The application reads `VCAP_SERVICES`, finds the HDI service credentials, connects with `hdbcli`, and sets the schema from the service binding before querying.

## 6. Evaluation Methodology

Version 1 evaluation is retrieval-only and is implemented in `scripts/evaluate_retrieval.py`.

Evaluation process:

1. Load the fixed query set from `data/evaluation_queries.csv`.
2. Generate a query embedding for each question.
3. Retrieve chunks from HANA ordered by vector similarity.
4. Convert chunk-level results into document-level ranking by keeping the first occurrence of each `DOCUMENT_ID`.
5. Find the rank of the expected document.
6. Aggregate retrieval metrics.

Current metrics:

- Top-1 accuracy
- Top-3 accuracy
- Top-5 accuracy
- Mean reciprocal rank
- Mean query embedding time
- Mean HANA retrieval time
- Mean combined search processing time

This evaluation measures whether the expected source document appears high in the retrieval ranking. It does not evaluate generated answers, citation correctness, faithfulness, or abstention behavior.

## 7. Identified Limitations

Version 1 is intentionally narrow and effective as a baseline, but it has clear limitations for a RAG assistant:

- Retrieval-only user experience; no generated answer.
- Small curated corpus with limited SAP BTP coverage.
- One source document has no raw content URL and is skipped during ingestion.
- Full-refresh ingestion only; no incremental updates, content hashes, or ingestion run history.
- Chunking is word-count based and does not preserve section hierarchy.
- Retrieved chunks do not include stable section anchors or neighboring context.
- No relevance threshold or abstention behavior for unsupported questions.
- No reranking stage.
- No hybrid retrieval using lexical and vector signals together.
- No answer-quality evaluation.
- No citation-quality evaluation.
- No separation between retrieval evaluation and RAG answer evaluation.
- Shared logic is duplicated across production and validation scripts.
- HANA schema stores only chunk-level records, not normalized document or ingestion metadata.

## 8. Proposed Version 2 RAG Architecture

Version 2 should be created separately on the `rag-v2` branch while preserving Version 1 behavior and evidence.

Proposed Version 2 architecture:

```text
Browser
-> Flask V2 application
-> query analysis
-> FastEmbed query embedding
-> SAP HANA Cloud / HDI vector retrieval
-> optional lexical or metadata filtering
-> optional reranking
-> context assembly
-> LLM generation layer
-> grounded answer with SAP citations
-> answer and retrieval diagnostics
```

Recommended V2 components:

- V2 runtime entrypoint, for example `app_v2.py` or `v2/app.py`.
- V2 ingestion script, for example `scripts/ingest_documents_v2.py`.
- V2 retrieval module with explicit score thresholds and context assembly.
- V2 generation module with a provider boundary for the LLM.
- V2 evaluation scripts for retrieval quality and answer quality.
- V2 HANA artifacts if schema changes are required.

Potential V2 HANA model:

- `DOCUMENTS_V2`: document-level metadata, source URL, content URL, content hash, source version, and ingestion status.
- `DOCUMENT_CHUNKS_V2`: chunk text, section metadata, source URL, vector, and neighboring chunk references.
- `INGESTION_RUNS_V2`: ingestion run metadata, timestamps, source counts, chunk counts, and errors.

The generation layer should:

- Use retrieved SAP documentation chunks as the only factual context.
- Refuse or abstain when retrieved context is insufficient.
- Cite SAP sources in the answer.
- Expose supporting passages for auditability.
- Keep LLM provider details behind a small interface so SAP AI Core / Generative AI Hub or another provider can be introduced without rewriting retrieval.

## 9. Recommended Implementation Sequence

1. Freeze and protect Version 1 evidence.

   Keep the existing Version 1 files, metrics, datasets, and evaluation conclusions unchanged.

2. Add V2 documentation and design approval.

   Use this review as the starting point for implementation approval before changing application behavior.

3. Create shared internal modules for V2.

   Add reusable V2 modules for configuration, HANA access, embeddings, chunking, retrieval, generation, and evaluation. Avoid changing V1 imports until there is an explicit reason and approval.

4. Improve corpus coverage.

   Expand source coverage in a V2-specific source catalog or table. Track source resolution status instead of silently skipping unresolved documents.

5. Implement V2 ingestion.

   Add content hashing, ingestion run records, section-aware chunk metadata, and optional incremental updates.

6. Implement V2 retrieval.

   Keep HANA vector search as the foundation. Add deduplication, score thresholds, context assembly, optional reranking, and abstention signals.

7. Implement RAG generation.

   Add a generation interface, construct grounded prompts from retrieved context, and return answers with citations.

8. Add V2 UI.

   Show generated answers, citations, supporting chunks, similarity scores, and diagnostic timings.

9. Add V2 evaluation.

   Evaluate retrieval separately from generated answers. Preserve the V1 retrieval evaluation as the baseline and add RAG-specific metrics for faithfulness, citation correctness, completeness, and abstention.

10. Deploy V2 separately.

   Use a separate Cloud Foundry app name and route. Decide whether V2 should share the existing HDI container using separate tables or use a separate HDI container.

## 10. Risks and Open Decisions

Risks:

- V2 answer generation may introduce unsupported claims unless strict grounding and abstention are enforced.
- Expanded corpus coverage can reduce precision if source quality and chunking are not controlled.
- Changing chunking or retrieval can make comparisons with V1 misleading unless V1 remains untouched.
- LLM latency and cost may dominate runtime behavior.
- Citation quality depends on preserving stable source metadata and section context.
- HANA schema changes need careful separation from the frozen V1 table.
- Evaluation scores can be distorted if datasets or expected labels are adjusted after observing results.

Open decisions:

- Which LLM provider should V2 use on SAP BTP?
- Should V2 use the same HDI container with separate tables or a separate HDI container?
- Should V2 keep CSV source catalogs, move source metadata into HANA, or use both?
- Should retrieval remain vector-only or add hybrid lexical/vector retrieval?
- Should reranking be introduced in V2 immediately or after a stronger retrieval baseline?
- What minimum similarity or confidence threshold should trigger abstention?
- What citation format should the UI and evaluation expect?
- Should V2 expose retrieved passages by default or hide them behind diagnostics?
- What answer-quality evaluation method should be accepted as the project standard?

