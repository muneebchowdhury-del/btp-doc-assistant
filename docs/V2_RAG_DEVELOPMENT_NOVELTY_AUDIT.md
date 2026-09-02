# Version 2 RAG Development Novelty Audit

## Scope

This local-only audit checks the pre-registered RAG development questions against all prior Version 1, Version 2 foundation, Version 2 calibration, and Version 2 retrieval/abstention held-out questions.

The audit uses exact duplicate detection, normalized lexical Jaccard overlap, and local question-to-question embedding cosine similarity with FastEmbed `BAAI/bge-small-en-v1.5`. It does not query HANA, retrieve corpus documents, call Gemini, inspect retrieval scores, or execute the RAG development harness.

No arbitrary semantic-similarity rejection threshold is applied. Same-domain similarity is treated as acceptable when the question is substantively distinct and not an exact duplicate.

## Dataset Composition

- RAG development questions: `24`
- Prior questions compared: `134`
- `NEAR_DOMAIN_UNSUPPORTED`: `4`
- `OUT_OF_SCOPE`: `4`
- `SUPPORTED`: `16`

## Exact Duplicate Check

No exact duplicate questions were found.

## Per-Question Nearest Prior Diagnostics

| Query ID | Category | Nearest Lexical Prior | Lexical Jaccard | Nearest Semantic Prior | Embedding Cosine | Assessment |
| --- | --- | --- | ---: | --- | ---: | --- |
| RAGDEV001 | SUPPORTED | Q027: What is the SAP BTP Cloud Foundry environment? | 0.4545 | Q027: What is the SAP BTP Cloud Foundry environment? | 0.9232 | NO_EXACT_DUPLICATE_REVIEW_REQUIRED |
| RAGDEV002 | SUPPORTED | Q027: What is the SAP BTP Cloud Foundry environment? | 0.3125 | CAL003: I have an application package ready and need to get it running in SAP BTP Cloud Foundry. What deployment process applies? | 0.9046 | NO_EXACT_DUPLICATE_REVIEW_REQUIRED |
| RAGDEV003 | SUPPORTED | HOUT002: How can developers structure Cloud Foundry application work before deployment when they need SAP BTP development guidance? | 0.3684 | HOUT002: How can developers structure Cloud Foundry application work before deployment when they need SAP BTP development guidance? | 0.9027 | NO_EXACT_DUPLICATE_REVIEW_REQUIRED |
| RAGDEV004 | SUPPORTED | Q001: How do I bind an application to an existing service instance? | 0.2727 | HOUT004: How should I think about marketplace services and service instances before an application can consume a managed capability? | 0.8173 | NO_EXACT_DUPLICATE_REVIEW_REQUIRED |
| RAGDEV005 | SUPPORTED | Q002: How can I connect a Cloud Foundry application with a BTP service? | 0.2857 | Q024: What services can applications use in the Cloud Foundry environment? | 0.8266 | NO_EXACT_DUPLICATE_REVIEW_REQUIRED |
| RAGDEV006 | SUPPORTED | Q016: How do I create a route for a Cloud Foundry application? | 0.1765 | CAL006: I need to change a feature flag and API endpoint without rebuilding my Cloud Foundry app. Where should those values be managed? | 0.8312 | NO_EXACT_DUPLICATE_REVIEW_REQUIRED |
| RAGDEV007 | SUPPORTED | Q027: What is the SAP BTP Cloud Foundry environment? | 0.3636 | Q027: What is the SAP BTP Cloud Foundry environment? | 0.8914 | NO_EXACT_DUPLICATE_REVIEW_REQUIRED |
| RAGDEV008 | SUPPORTED | HOUT022: Can trial access be used to explore SAP BTP services without treating it as a long-term productive account? | 0.3158 | CAL022: I am evaluating SAP BTP without committing to paid usage yet. How should I think about trial accounts versus free tier plans? | 0.8527 | NO_EXACT_DUPLICATE_REVIEW_REQUIRED |
| RAGDEV009 | SUPPORTED | HOUT008: What administrative unit inside a Cloud Foundry org holds its own apps services routes and members? | 0.1739 | CAL008: Our org has several teams and we need separate areas for development and testing. How should we manage Cloud Foundry spaces? | 0.8732 | NO_EXACT_DUPLICATE_REVIEW_REQUIRED |
| RAGDEV010 | SUPPORTED | HOUT020: How do provider locations and regional availability affect where SAP BTP workloads and services can be used? | 0.2941 | HOUT020: How do provider locations and regional availability affect where SAP BTP workloads and services can be used? | 0.8887 | NO_EXACT_DUPLICATE_REVIEW_REQUIRED |
| RAGDEV011 | SUPPORTED | Q029: What development options are available in SAP BTP Cloud Foundry? | 0.2143 | V2F011: Which tools are available to develop and manage applications on SAP BTP? | 0.9087 | NO_EXACT_DUPLICATE_REVIEW_REQUIRED |
| RAGDEV012 | SUPPORTED | HOUT015: When an HTML5 frontend calls a backend through SAP BTP routing, where does destination configuration fit into that request path? | 0.3810 | HOUT015: When an HTML5 frontend calls a backend through SAP BTP routing, where does destination configuration fit into that request path? | 0.8813 | NO_EXACT_DUPLICATE_REVIEW_REQUIRED |
| RAGDEV013 | SUPPORTED | HOUT016: Why might an enterprise choose SAP BTP as a common layer for extending existing SAP landscapes and building new business applications? | 0.4211 | HOUT016: Why might an enterprise choose SAP BTP as a common layer for extending existing SAP landscapes and building new business applications? | 0.9036 | NO_EXACT_DUPLICATE_REVIEW_REQUIRED |
| RAGDEV014 | SUPPORTED | CAL017: I keep seeing subaccounts regions environments entitlements and quotas together. How do these basic SAP BTP concepts fit? | 0.4444 | CAL017: I keep seeing subaccounts regions environments entitlements and quotas together. How do these basic SAP BTP concepts fit? | 0.8827 | NO_EXACT_DUPLICATE_REVIEW_REQUIRED |
| RAGDEV015 | SUPPORTED | V2F006: Where do I deploy applications and manage services within the SAP BTP account structure? | 0.2500 | V2F005: How are global accounts subaccounts and directories related in SAP BTP? | 0.8287 | NO_EXACT_DUPLICATE_REVIEW_REQUIRED |
| RAGDEV016 | SUPPORTED | CAL019: A service tile appears in the cockpit but our subaccount still cannot create the selected plan. What entitlement or quota issue might explain this? | 0.2273 | HOUT019: Why can assigning entitlement to a subaccount still leave teams thinking carefully about quotas and available service plans? | 0.8963 | NO_EXACT_DUPLICATE_REVIEW_REQUIRED |
| RAGDEV017 | NEAR_DOMAIN_UNSUPPORTED | Q025: How does an application consume services in SAP BTP? | 0.2222 | HOUT012: How can service-instance credentials be issued for a command-line tool that runs outside the application lifecycle? | 0.7416 | NO_EXACT_DUPLICATE_REVIEW_REQUIRED |
| RAGDEV018 | NEAR_DOMAIN_UNSUPPORTED | Q005: What is a service key used for in SAP BTP? | 0.2222 | CAL021: I want to manage SAP BTP from the cockpit for some tasks and a command line for others. What tool options are available? | 0.7012 | NO_EXACT_DUPLICATE_REVIEW_REQUIRED |
| RAGDEV019 | NEAR_DOMAIN_UNSUPPORTED | CAL033: How do I configure SAP Build Work Zone page layouts and widgets? | 0.2500 | CAL037: How can I configure principal propagation through SAP Cloud Connector? | 0.7859 | NO_EXACT_DUPLICATE_REVIEW_REQUIRED |
| RAGDEV020 | NEAR_DOMAIN_UNSUPPORTED | Q022: How do I deploy an application to the Cloud Foundry environment? | 0.1818 | V2F006: Where do I deploy applications and manage services within the SAP BTP account structure? | 0.7661 | NO_EXACT_DUPLICATE_REVIEW_REQUIRED |
| RAGDEV021 | OUT_OF_SCOPE | CAL039: How do I set up event mesh queues and subscriptions for asynchronous messaging? | 0.0833 | HOUT034: What practice routine helps a beginner learn jazz piano chords? | 0.5756 | NO_EXACT_DUPLICATE_REVIEW_REQUIRED |
| RAGDEV022 | OUT_OF_SCOPE | Q001: How do I bind an application to an existing service instance? | 0.0000 | CAL041: What is the best recipe for baking sourdough bread? | 0.5953 | NO_EXACT_DUPLICATE_REVIEW_REQUIRED |
| RAGDEV023 | OUT_OF_SCOPE | HOUT037: How do I plan a vegetable garden for a shaded balcony? | 0.1250 | HOUT039: How should I organize a small conference agenda for two tracks? | 0.5804 | NO_EXACT_DUPLICATE_REVIEW_REQUIRED |
| RAGDEV024 | OUT_OF_SCOPE | Q001: How do I bind an application to an existing service instance? | 0.0000 | HOUT040: What exercises strengthen wrists for rock climbing? | 0.6506 | NO_EXACT_DUPLICATE_REVIEW_REQUIRED |

## Result

The pre-execution RAG development dataset passes the exact duplicate check. Lexical and semantic nearest-neighbor diagnostics are recorded for review before any RAG development execution.
