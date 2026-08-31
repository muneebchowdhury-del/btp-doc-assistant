# Version 2 Deployment and Evaluation Runbook

## Purpose

Deploy the already-reviewed `DOCUMENT_CHUNKS_V2` HDI artifact, ingest the isolated Version 2 corpus, and run the pre-registered Version 2 retrieval evaluation without changing Version 1.

## Preconditions

- Work from the current `rag-v2` branch.
- Pull the latest remote changes before running commands.
- Cloud Foundry CLI is installed and logged into the correct SAP BTP org/space.
- Target space is the existing project space that contains the bound service `btp-doc-assistant-hdi`.
- Do not modify or delete `DOCUMENT_CHUNKS`.
- Do not modify the frozen Version 1 query file or metrics.

## Step 1 — Sync local repository

From the repository root:

```powershell
git switch rag-v2
git pull origin rag-v2
git status
```

Expected: clean working tree before deployment.

## Step 2 — Confirm Cloud Foundry target

```powershell
cf target
```

Confirm that the intended org and the `btp-doc-assistant` space are targeted.

If necessary, log in again using the existing SSO workflow, then target the correct space.

## Step 3 — Deploy the HDI artifact

From the repository root:

```powershell
cd db
cf push -f manifest.yml
```

Because the deployer app has `instances: 0`, use the staged app to run the HDI deployer as a task:

```powershell
cf run-task btp-doc-assistant-db-deployer --command "npm start -- --exit" --name deploy-v2-table
```

Then inspect task status and logs:

```powershell
cf tasks btp-doc-assistant-db-deployer
cf logs btp-doc-assistant-db-deployer --recent
```

Success criterion: HDI deployment logs show a successful deployment / make completion and the task exits successfully.

Do not proceed if deployment fails.

## Step 4 — Verify the V2 table without changing data

Use the existing Cloud Foundry application execution context or an equivalent bound task to run a read-only SQL verification against `DOCUMENT_CHUNKS_V2`.

Minimum verification:

```sql
SELECT COUNT(*) FROM "DOCUMENT_CHUNKS_V2";
```

Before ingestion, a count of 0 is expected if the table is newly created.

Also confirm that the frozen `DOCUMENT_CHUNKS` table still exists and has its prior data. Do not delete or rewrite it.

## Step 5 — Run V2 ingestion

The V2 ingestion script writes only to `DOCUMENT_CHUNKS_V2`.

Stage/push the current application code if needed so the merged `rag-v2` files are available in the bound Cloud Foundry environment. Then run:

```powershell
cf run-task btp-doc-assistant-app --command "python scripts/ingest_documents_v2.py" --name ingest-v2-corpus -m 2G
```

Inspect task status and recent logs:

```powershell
cf tasks btp-doc-assistant-app
cf logs btp-doc-assistant-app --recent
```

Record:
- documents processed
- documents skipped
- total V2 chunks prepared
- embeddings generated
- final row count in `DOCUMENT_CHUNKS_V2`
- any errors or warnings

Do not alter source mappings or evaluation questions after observing ingestion/retrieval behavior without documenting a new experiment version.

## Step 6 — Run the pre-registered V2 retrieval evaluation

Run only after ingestion succeeds:

```powershell
cf run-task btp-doc-assistant-app --command "python scripts/evaluate_retrieval_v2.py" --name evaluate-v2-retrieval -m 1G
```

Inspect the task logs and preserve the complete output.

Record the two result blocks separately:

### A. V1 Regression Set
- Top-1
- Top-3
- Top-5
- MRR
- mean embedding time
- mean HANA retrieval time
- mean combined processing time

### B. V2 Foundation Coverage Set
- Top-1
- Top-3
- Top-5
- MRR
- mean embedding time
- mean HANA retrieval time
- mean combined processing time

Also preserve the detailed per-query ranks, especially any expected document outside Top-3 or Top-5.

## Step 7 — Sanity-check the known broad query

After the formal evaluation output has been captured, run the exploratory query:

`What is SAP BTP?`

This check is exploratory only and must not replace or modify the pre-registered evaluation results.

Expected qualitative behavior: an overview/foundation source such as `DOC017` or another appropriate new foundation document should rank near the top.

## Step 8 — Record evidence

Do not change evaluation labels based on results.

Create a deployment/evaluation evidence note containing:
- deployment task status
- ingestion row count
- exact aggregate metrics for both evaluation blocks
- failed/near-miss query IDs and ranks
- broad-query sanity check
- relevant task names and timestamps
- unresolved technical issues

Do not commit credentials, service-binding values, VCAP contents, or tokens.

## Stop condition

Stop after retrieval evaluation. Do not implement an LLM, abstention threshold, reranker, hybrid search, or RAG generation until the retrieval results have been reviewed and approved.
