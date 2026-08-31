# SAP BTP Documentation Assistant — Agent Instructions

## Project governance

The user is the project lead and final decision maker.

Version 1 is frozen and must remain reproducible.

Do not modify or reinterpret:
- the Git tag `v1-semantic-retrieval`
- historical Version 1 results
- Version 1 reported metrics
- Version 1 evaluation conclusions

All new development belongs to the `rag-v2` branch.

## Version 1 baseline

Architecture:

Browser
→ Flask on SAP BTP Cloud Foundry
→ FastEmbed BAAI/bge-small-en-v1.5
→ 384-dimensional query embedding
→ SAP HANA Cloud / HDI
→ DOCUMENT_CHUNKS
→ COSINE_SIMILARITY
→ ranked SAP documentation passages

Frozen Version 1 configuration:
- 15 indexed SAP BTP documents
- 5,788 cleaned words
- 64 chunks
- chunk size: 120 words
- overlap: 25 words
- vector dimension: 384
- embedding model: BAAI/bge-small-en-v1.5

Frozen Version 1 evaluation:
- 30 queries
- Top-1: 66.67%
- Top-3: 96.67%
- Top-5: 100%
- MRR: 0.8083

## Version 2 objectives

1. Improve corpus coverage.
2. Add relevance / abstention handling.
3. Preserve source-grounded retrieval.
4. Add a RAG generation layer.
5. Return citations to SAP sources.
6. Evaluate retrieval and generated answers separately.
7. Keep Version 1 evidence and results untouched.

## Security

Never commit or expose:
- passwords
- `.env`
- VCAP_SERVICES contents
- service keys
- certificates
- access tokens
- credentials

## Working method

Before major architectural changes:
1. Analyse.
2. Propose a plan.
3. Wait for approval.

After implementation tasks:
- explain files changed
- explain why they changed
- run relevant tests
- report test results
- report unresolved issues
- make small, reviewable Git commits

Do not silently change evaluation datasets or expected labels to improve scores.