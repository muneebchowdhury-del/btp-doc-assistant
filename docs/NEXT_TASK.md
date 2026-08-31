# Next Task — V2 Retrieval Evaluation Pre-Registration

## Purpose

Before deploying or ingesting the Version 2 corpus, define and freeze the Version 2 retrieval evaluation so results are not influenced by observing retrieval output first.

## Branch

Create and work on:

`task/v2-evaluation-preregistration`

Base it on the current `rag-v2` branch.

## Constraints

Follow `AGENTS.md`.

Do not modify Version 1 files, Version 1 reported results, or the `v1-semantic-retrieval` tag.

Do not deploy to SAP BTP, do not run ingestion, and do not inspect Version 2 retrieval results yet.

Do not modify:
- `data/document_sources.csv`
- `data/evaluation_queries.csv`
- `scripts/evaluate_retrieval.py`
- `db/src/DOCUMENT_CHUNKS.hdbtable`

## Required work

1. Add `data/evaluation_queries_v2_foundation.csv` containing exactly 16 new held-out foundation questions: two questions for each new V2 document `DOC017` through `DOC024`.

2. Questions must be natural user questions and must be written before observing any V2 retrieval output. Avoid simply copying document titles verbatim. Each row must contain:
   - `QUERY_ID`
   - `QUESTION`
   - `EXPECTED_DOCUMENT_ID`

3. Add `scripts/evaluate_retrieval_v2.py` that evaluates `DOCUMENT_CHUNKS_V2` and reports two evaluation blocks separately:

   **A. V1 Regression Set**
   - reuse the existing frozen `data/evaluation_queries.csv`
   - run the same 30 questions against `DOCUMENT_CHUNKS_V2`
   - preserve the original expected document IDs
   - report Top-1, Top-3, Top-5, MRR, mean embedding time, mean HANA retrieval time, and mean combined search time

   **B. V2 Foundation Coverage Set**
   - use `data/evaluation_queries_v2_foundation.csv`
   - report the same metrics separately

4. Use the existing embedding model `BAAI/bge-small-en-v1.5`, 384-dimensional vectors, HANA `COSINE_SIMILARITY`, and document-level deduplication methodology so the comparison remains consistent with Version 1.

5. The script must read only from `DOCUMENT_CHUNKS_V2`. It must not write to HANA.

6. Print detailed per-query rankings and aggregate metrics for each evaluation block. Do not combine the two sets into a single headline score.

7. Add a short methodology note in `docs/V2_EVALUATION_PROTOCOL.md` stating that the V2 foundation questions were fixed before deployment/ingestion or observation of V2 retrieval results, and that the frozen V1 set is reused only as a regression/comparability set.

8. Update `CHANGELOG_V2.md` describing the evaluation pre-registration.

9. Run only static/local checks that do not require querying HANA. Confirm the new Python script parses/compiles successfully.

## Completion

Commit and push the branch. Do not merge it. If PR creation is unavailable in the Codex environment, stop after pushing; ChatGPT will open the PR through the connected GitHub integration.
