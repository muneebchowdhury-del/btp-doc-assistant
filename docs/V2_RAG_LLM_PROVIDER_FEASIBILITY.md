# Version 2 RAG LLM Provider Feasibility

## Purpose

This document records a read-only feasibility check for using an SAP-native LLM provider for the Version 2 RAG phase through SAP AI Core and Generative AI Hub.

No RAG implementation, LLM request, SAP AI Core resource creation, service binding, service key creation, credential inspection, or production configuration change was performed.

## Current Architecture Boundary

The retrieval and abstention research phase is closed. This feasibility check does not modify:

- `DOCUMENT_CHUNKS_V2`
- corpus
- chunking
- embeddings
- `BAAI/bge-small-en-v1.5`
- BM25-style lexical retrieval
- full dense ranking
- full lexical ranking
- Reciprocal Rank Fusion
- `RRF k = 60`
- candidate abstention threshold `0.75`
- held-out datasets or results
- production `app.py`

The selected retrieval/abstention boundary remains frozen while LLM-provider feasibility is assessed.

## Commands Used

Read-only Cloud Foundry inspection commands:

```bash
cf target
cf services
cf marketplace
cf marketplace | Select-String -Pattern "AI|aicore|generative"
```

Commands that expose credentials were not run. In particular, no `cf env`, service-key display, service creation, service update, service binding, or service deletion command was run.

## Cloud Foundry Target

Relevant technical target information:

- API endpoint: `https://api.cf.eu01.hana.ondemand.com`
- API version: `3.225.0`
- Space: `btp-doc-assistant`

Personal usernames and unnecessary account identifiers are intentionally omitted from this evidence document.

## Existing Service Instances

Existing service instances visible in the current Cloud Foundry space:

| Service instance | Offering | Plan | Bound apps | Last operation |
| --- | --- | --- | --- | --- |
| `btp-doc-assistant-hdi` | `hana` | `hdi-shared` | `btp-doc-assistant-app`, `btp-doc-assistant-db-deployer` | create succeeded |

No existing SAP AI Core, Generative AI Hub, AI Launchpad, or other AI-related service instance was visible in `cf services`.

## Marketplace Findings

The full marketplace output did not include an SAP AI Core offering.

AI-related search terms checked:

- `AI Core`
- `aicore`
- `AI Launchpad`
- `generative`

The filtered command:

```powershell
cf marketplace | Select-String -Pattern "AI|aicore|generative"
```

did not return SAP AI Core, `aicore`, AI Launchpad, or Generative AI Hub offerings. It returned non-AI substring matches such as `service-manager` and `hana`, but these are not SAP AI Core or generative-AI-capable offerings.

Visible AI Core service-offering name:

- none

Visible AI Core plans:

- none

Whether SAP AI Core appears:

- no

Whether the required `extended` plan appears:

- no

## Feasibility Classification

Status: `UNAVAILABLE`

Reason:

Generative AI Hub requires SAP AI Core with the generative-AI-capable `extended` plan. In the currently targeted Cloud Foundry subaccount/space, SAP AI Core is not visible in existing service instances or in the marketplace, and the `extended` plan is not visible.

## SAP-Native Generative AI Hub Feasibility

A SAP-native Generative AI Hub implementation does not currently appear technically possible in this targeted environment because the required SAP AI Core service offering and `extended` plan are not available through the visible Cloud Foundry marketplace.

Access or entitlement still required:

- SAP AI Core service entitlement for the target subaccount
- Access to the `extended` plan
- Any required Generative AI Hub access and role collection assignment
- A later approved service-instance provisioning step, if entitlement becomes available

No alternative LLM provider was selected or substituted.

## Confirmation

This feasibility check changed no SAP services, no credentials, no production code, no deployment configuration, no retrieval configuration, no corpus data, and no evaluation artifacts.

No LLM model was selected, and no LLM request was made.
