# Version 2 Deployment and Retrieval Evaluation Evidence

## Scope

This note records the Version 2 HDI deployment, V2 ingestion, pre-registered retrieval evaluation, and post-evaluation broad-query sanity check.

No evaluation questions, expected labels, source mappings, embedding model, chunking configuration, retrieval logic, or Version 1 files were changed based on observed results.

No LLM, RAG generation, abstention, reranking, or hybrid retrieval work was implemented.

## Environment

- Local branch: `rag-v2`
- Cloud Foundry API endpoint: `https://api.cf.eu01.hana.ondemand.com`
- Cloud Foundry space: `btp-doc-assistant`
- HDI service: `btp-doc-assistant-hdi`
- Application: `btp-doc-assistant-app`
- HDI deployer application: `btp-doc-assistant-db-deployer`
- Target V2 table: `DOCUMENT_CHUNKS_V2`
- Frozen V1 table checked for preservation: `DOCUMENT_CHUNKS`
- Embedding model: `BAAI/bge-small-en-v1.5`
- Vector dimension: 384

## Commands Run

Repository sync:

```powershell
git switch rag-v2
git pull --ff-only origin rag-v2
git status --short
```

Cloud Foundry target:

```powershell
cf target
```

HDI deployment:

```powershell
cd db
cf push -f manifest.yml
cf run-task btp-doc-assistant-db-deployer --command "npm start -- --exit" --name deploy-v2-table
cf tasks btp-doc-assistant-db-deployer
cf logs btp-doc-assistant-db-deployer --recent
```

Pre-ingestion read-only table verification:

```powershell
cf run-task btp-doc-assistant-app --command "python -c <read-only DOCUMENT_CHUNKS_V2 and DOCUMENT_CHUNKS count check>" --name verify-v2-table-readonly
cf tasks btp-doc-assistant-app
cf logs btp-doc-assistant-app --recent
```

Application code staging:

```powershell
cf push btp-doc-assistant-app
```

V2 ingestion:

```powershell
cf run-task btp-doc-assistant-app --command "python scripts/ingest_documents_v2.py" --name ingest-v2-corpus -m 2G
cf tasks btp-doc-assistant-app
cf logs btp-doc-assistant-app --recent
```

Post-ingestion row count verification:

```powershell
cf run-task btp-doc-assistant-app --command "python -c <read-only DOCUMENT_CHUNKS_V2 count check>" --name verify-v2-row-count
cf tasks btp-doc-assistant-app
cf logs btp-doc-assistant-app --recent
```

Pre-registered V2 retrieval evaluation:

```powershell
cf run-task btp-doc-assistant-app --command "python scripts/evaluate_retrieval_v2.py" --name evaluate-v2-retrieval -m 1G
cf tasks btp-doc-assistant-app
cf logs btp-doc-assistant-app --recent
```

Post-evaluation exploratory broad-query sanity check:

```powershell
cf run-task btp-doc-assistant-app --command "python -c <read-only DOCUMENT_CHUNKS_V2 search for 'What is SAP BTP?'>" --name broad-query-sanity-v2
cf tasks btp-doc-assistant-app
cf logs btp-doc-assistant-app --recent
```

## Deployment Status

### HDI Deployment

- Task name: `deploy-v2-table`
- Task id: `3`
- Start time: `2026-08-31 21:04:48 UTC`
- Status: `SUCCEEDED`
- Relevant log result: `Make succeeded (0 warnings): 1 files deployed (effective 1), 0 files undeployed (effective 0), 0 dependent files redeployed`
- Deployed artifact: `src/DOCUMENT_CHUNKS_V2.hdbtable`

### Pre-Ingestion Verification

- Task name: `verify-v2-table-readonly`
- Task id: `8`
- Start time: `2026-08-31 21:05:45 UTC`
- Status: `SUCCEEDED`
- `DOCUMENT_CHUNKS_V2_ROWS`: 0
- `DOCUMENT_CHUNKS_ROWS`: 64

### Application Staging

- Command: `cf push btp-doc-assistant-app`
- Last uploaded: `2026-08-31 23:11:37 CEST`
- Status: application started successfully
- Instance state: `1/1 running`
- Start command: `gunicorn --bind 0.0.0.0:$PORT app:app`

## Ingestion Evidence

- Task name: `ingest-v2-corpus`
- Task id: `10`
- Start time: `2026-08-31 21:12:11 UTC`
- Status: `SUCCEEDED`
- Command: `python scripts/ingest_documents_v2.py`
- Documents processed: 23
- Documents skipped: 1
- Skipped document: `DOC008` because it has no `CONTENT_URL`
- Total V2 chunks prepared: 138
- V2 embeddings generated: 138
- Final row count reported by ingestion: 138
- Embedding model: `BAAI/bge-small-en-v1.5`
- Vector dimension: 384
- Warning observed: unauthenticated Hugging Face Hub download warning for model files

Processed documents:

- `DOC001`: Cloud Foundry Environment
- `DOC002`: Development in the Cloud Foundry Environment
- `DOC003`: Deploying to the Cloud Foundry Environment
- `DOC004`: Using Services in the Cloud Foundry Environment
- `DOC005`: Bind an Application to a Service
- `DOC006`: Manage Environment Variables
- `DOC007`: Create Routes
- `DOC009`: Managing Spaces
- `DOC010`: About Roles in the Cloud Foundry Environment
- `DOC011`: Using Application Logs
- `DOC012`: Using Application Events
- `DOC013`: Service Keys
- `DOC014`: Managing Space Quotas
- `DOC015`: Security Groups
- `DOC016`: Application Routes and Destinations
- `DOC017`: SAP Business Technology Platform
- `DOC018`: Basic Platform Concepts
- `DOC019`: Account Model
- `DOC020`: Entitlements and Quotas
- `DOC021`: Regions
- `DOC022`: Tools
- `DOC023`: Trial Accounts and Free Tier
- `DOC024`: Getting Started

Post-ingestion verification:

- Task name: `verify-v2-row-count`
- Task id: `11`
- Start time: `2026-08-31 21:12:58 UTC`
- Status: `SUCCEEDED`
- `DOCUMENT_CHUNKS_V2_ROWS`: 138

## Pre-Registered Retrieval Evaluation

- Task name: `evaluate-v2-retrieval`
- Task id: `12`
- Start time: `2026-08-31 21:13:22 UTC`
- Status: `SUCCEEDED`
- Command: `python scripts/evaluate_retrieval_v2.py`
- Target table: `DOCUMENT_CHUNKS_V2`
- Evaluation script stated it reads from `DOCUMENT_CHUNKS_V2` only and does not write to HANA.
- Warning observed: unauthenticated Hugging Face Hub download warning for model files

### A. V1 Regression Set

- Evaluation file: `data/evaluation_queries.csv`
- Queries evaluated: 30
- Top-1 Accuracy: 0.6333 (19/30)
- Top-3 Accuracy: 0.9333 (28/30)
- Top-5 Accuracy: 0.9667 (29/30)
- MRR: 0.7731
- Mean Query Embedding Time: 25.32 ms
- Mean HANA Retrieval Time: 8.49 ms
- Mean Search Processing Time: 33.81 ms

Detailed results:

```csv
QUERY_ID,EXPECTED_DOCUMENT_ID,EXPECTED_RANK,TOP_RESULT_DOCUMENT_ID,TOP_RESULT_SCORE,TOP5_DOCUMENTS,TOP1_CORRECT,TOP3_CORRECT,TOP5_CORRECT,RECIPROCAL_RANK,EMBEDDING_MS,HANA_QUERY_MS
Q001,DOC005,1,DOC005,0.8275,DOC005;DOC004;DOC007;DOC013;DOC006,1,1,1,1.0,16.18,22.85
Q002,DOC005,3,DOC001,0.8308,DOC001;DOC002;DOC005;DOC003;DOC004,0,1,1,0.3333,38.83,9.19
Q003,DOC005,2,DOC013,0.7617,DOC013;DOC005;DOC004;DOC015;DOC006,0,1,1,0.5,27.96,7.93
Q004,DOC013,1,DOC013,0.8113,DOC013;DOC005;DOC004;DOC006;DOC007,1,1,1,1.0,31.32,7.22
Q005,DOC013,9,DOC022,0.7855,DOC022;DOC004;DOC005;DOC018;DOC020,0,0,0,0.1111,23.45,7.86
Q006,DOC011,1,DOC011,0.831,DOC011;DOC004;DOC001;DOC002;DOC006,1,1,1,1.0,24.36,8.19
Q007,DOC011,2,DOC012,0.6187,DOC012;DOC011;DOC015;DOC023;DOC021,0,1,1,0.5,30.85,7.84
Q008,DOC012,1,DOC012,0.7625,DOC012;DOC011;DOC015;DOC005;DOC009,1,1,1,1.0,24.52,8.22
Q009,DOC012,1,DOC012,0.7356,DOC012;DOC011;DOC015;DOC005;DOC013,1,1,1,1.0,26.32,8.41
Q010,DOC009,1,DOC009,0.8297,DOC009;DOC006;DOC007;DOC010;DOC019,1,1,1,1.0,26.37,8.39
Q011,DOC009,1,DOC009,0.8162,DOC009;DOC001;DOC004;DOC006;DOC002,1,1,1,1.0,20.68,8.07
Q012,DOC010,1,DOC010,0.8267,DOC010;DOC004;DOC002;DOC005;DOC001,1,1,1,1.0,11.32,8.51
Q013,DOC010,1,DOC010,0.8185,DOC010;DOC005;DOC004;DOC006;DOC007,1,1,1,1.0,24.13,7.54
Q014,DOC006,1,DOC006,0.7752,DOC006;DOC016;DOC013;DOC002;DOC005,1,1,1,1.0,40.14,8.28
Q015,DOC006,1,DOC006,0.7745,DOC006;DOC016;DOC013;DOC002;DOC004,1,1,1,1.0,19.26,7.77
Q016,DOC007,1,DOC007,0.8583,DOC007;DOC002;DOC005;DOC006;DOC001,1,1,1,1.0,21.63,8.35
Q017,DOC007,1,DOC007,0.7935,DOC007;DOC016;DOC019;DOC020;DOC005,1,1,1,1.0,22.6,8.16
Q018,DOC015,1,DOC015,0.7507,DOC015;DOC016;DOC019;DOC007;DOC013,1,1,1,1.0,26.8,8.45
Q019,DOC015,1,DOC015,0.8582,DOC015;DOC004;DOC002;DOC010;DOC001,1,1,1,1.0,22.84,8.15
Q020,DOC014,3,DOC020,0.823,DOC020;DOC009;DOC014;DOC006;DOC002,0,1,1,0.3333,25.13,7.56
Q021,DOC014,2,DOC009,0.7398,DOC009;DOC014;DOC020;DOC019;DOC023,0,1,1,0.5,22.04,7.29
Q022,DOC003,3,DOC002,0.843,DOC002;DOC001;DOC003;DOC005;DOC004,0,1,1,0.3333,31.26,7.59
Q023,DOC003,4,DOC002,0.8166,DOC002;DOC005;DOC001;DOC003;DOC004,0,0,1,0.25,34.28,8.97
Q024,DOC004,2,DOC002,0.8391,DOC002;DOC004;DOC001;DOC005;DOC003,0,1,1,0.5,31.24,7.72
Q025,DOC004,3,DOC022,0.8045,DOC022;DOC018;DOC004;DOC002;DOC020,0,1,1,0.3333,21.69,8.36
Q026,DOC001,2,DOC002,0.8403,DOC002;DOC001;DOC022;DOC004;DOC018,0,1,1,0.5,22.43,7.76
Q027,DOC001,1,DOC001,0.9085,DOC001;DOC002;DOC018;DOC003;DOC022,1,1,1,1.0,25.41,7.65
Q028,DOC002,1,DOC002,0.847,DOC002;DOC001;DOC004;DOC005;DOC003,1,1,1,1.0,22.15,7.68
Q029,DOC002,1,DOC002,0.8699,DOC002;DOC001;DOC003;DOC018;DOC022,1,1,1,1.0,33.24,7.18
Q030,DOC016,1,DOC016,0.8251,DOC016;DOC007;DOC019;DOC021;DOC018,1,1,1,1.0,11.11,7.49
```

Failures and near-misses:

- Outside Top-5: `Q005` expected `DOC013`, rank 9, top result `DOC022`.
- Outside Top-3 but inside Top-5: `Q023` expected `DOC003`, rank 4, top result `DOC002`.
- Top-1 misses inside Top-3: `Q002`, `Q003`, `Q007`, `Q020`, `Q021`, `Q022`, `Q024`, `Q025`, `Q026`.

### B. V2 Foundation Coverage Set

- Evaluation file: `data/evaluation_queries_v2_foundation.csv`
- Queries evaluated: 16
- Top-1 Accuracy: 0.7500 (12/16)
- Top-3 Accuracy: 0.9375 (15/16)
- Top-5 Accuracy: 0.9375 (15/16)
- MRR: 0.8299
- Mean Query Embedding Time: 26.48 ms
- Mean HANA Retrieval Time: 7.97 ms
- Mean Search Processing Time: 34.45 ms

Detailed results:

```csv
QUERY_ID,EXPECTED_DOCUMENT_ID,EXPECTED_RANK,TOP_RESULT_DOCUMENT_ID,TOP_RESULT_SCORE,TOP5_DOCUMENTS,TOP1_CORRECT,TOP3_CORRECT,TOP5_CORRECT,RECIPROCAL_RANK,EMBEDDING_MS,HANA_QUERY_MS
V2F001,DOC017,1,DOC017,0.8239,DOC017;DOC018;DOC022;DOC002;DOC003,1,1,1,1.0,26.92,7.77
V2F002,DOC017,1,DOC017,0.8413,DOC017;DOC018;DOC022;DOC003;DOC002,1,1,1,1.0,26.43,9.18
V2F003,DOC018,3,DOC024,0.8073,DOC024;DOC017;DOC018;DOC022;DOC023,0,1,1,0.3333,25.96,8.56
V2F004,DOC018,1,DOC018,0.8325,DOC018;DOC019;DOC020;DOC021;DOC024,1,1,1,1.0,11.55,7.47
V2F005,DOC019,1,DOC019,0.86,DOC019;DOC018;DOC021;DOC020;DOC024,1,1,1,1.0,28.74,8.0
V2F006,DOC019,9,DOC018,0.8143,DOC018;DOC022;DOC024;DOC003;DOC017,0,0,0,0.1111,27.67,6.99
V2F007,DOC020,1,DOC020,0.8254,DOC020;DOC018;DOC019;DOC023;DOC017,1,1,1,1.0,26.6,8.61
V2F008,DOC020,1,DOC020,0.8077,DOC020;DOC018;DOC019;DOC021;DOC023,1,1,1,1.0,18.85,8.55
V2F009,DOC021,1,DOC021,0.8794,DOC021;DOC018;DOC019;DOC004;DOC022,1,1,1,1.0,22.85,8.15
V2F010,DOC021,3,DOC019,0.8228,DOC019;DOC018;DOC021;DOC024;DOC023,0,1,1,0.3333,29.27,8.05
V2F011,DOC022,1,DOC022,0.8449,DOC022;DOC018;DOC017;DOC002;DOC024,1,1,1,1.0,11.03,7.68
V2F012,DOC022,1,DOC022,0.8347,DOC022;DOC003;DOC018;DOC002;DOC017,1,1,1,1.0,28.89,7.96
V2F013,DOC023,1,DOC023,0.821,DOC023;DOC024;DOC020;DOC018;DOC019,1,1,1,1.0,26.15,8.62
V2F014,DOC023,2,DOC024,0.8214,DOC024;DOC023;DOC018;DOC020;DOC022,0,1,1,0.5,38.54,7.04
V2F015,DOC024,1,DOC024,0.8331,DOC024;DOC017;DOC018;DOC022;DOC023,1,1,1,1.0,42.36,6.83
V2F016,DOC024,1,DOC024,0.8148,DOC024;DOC017;DOC018;DOC022;DOC002,1,1,1,1.0,31.87,8.03
```

Failures and near-misses:

- Outside Top-5: `V2F006` expected `DOC019`, rank 9, top result `DOC018`.
- Top-1 misses inside Top-3: `V2F003`, `V2F010`, `V2F014`.

## Exploratory Broad-Query Sanity Check

This check was run only after the formal pre-registered evaluation output was captured.

- Task name: `broad-query-sanity-v2`
- Task id: `13`
- Start time: `2026-08-31 21:14:49 UTC`
- Status: `SUCCEEDED`
- Query: `What is SAP BTP?`

Top 5 document-level results:

1. `DOC017` - SAP Business Technology Platform - 0.7716
2. `DOC022` - Tools - 0.7537
3. `DOC020` - Entitlements and Quotas - 0.7463
4. `DOC018` - Basic Platform Concepts - 0.7346
5. `DOC002` - Development in the Cloud Foundry Environment - 0.7327

Qualitative result: an overview/foundation document, `DOC017`, ranked first.

## Unresolved Technical Issues

- The application and HDI deployer are currently on `cflinuxfs4`, which Cloud Foundry reported as deprecated with maintenance/support ending May 31, 2027.
- FastEmbed/Hugging Face model downloads ran unauthenticated and emitted a warning recommending `HF_TOKEN` for higher rate limits and faster downloads.
- The deployed app did not initially contain the merged V2 scripts, so `cf push btp-doc-assistant-app` was required before ingestion.
- A pre-push script-presence check failed with exit status 1 because the V2 scripts were not yet present in the deployed app droplet. This was resolved by staging/pushing the current `rag-v2` app code.
- One local exploratory sanity-check command failed before reaching Cloud Foundry because PowerShell interpreted formatting characters inside the nested Python command. It was retried with safer command text and then succeeded.

## Stop Point

Stopped after the retrieval evaluation and post-evaluation broad-query sanity check.

No LLM, abstention threshold, reranker, hybrid search, or RAG generation was implemented.
