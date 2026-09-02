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
| RAGDEV001 | SUPPORTED | Q027: What is the SAP BTP Cloud Foundry environment? | 0.5000 | Q027: What is the SAP BTP Cloud Foundry environment? | 0.9733 | NO_EXACT_DUPLICATE_REVIEW_REQUIRED |
| RAGDEV002 | SUPPORTED | HOUT002: How can developers structure Cloud Foundry application work before deployment when they need SAP BTP development guidance? | 0.2857 | CAL002: We are starting a new Cloud Foundry app and need to choose development tools before deployment. What workflow should we follow? | 0.9037 | NO_EXACT_DUPLICATE_REVIEW_REQUIRED |
| RAGDEV003 | SUPPORTED | Q016: How do I create a route for a Cloud Foundry application? | 0.2308 | HOUT003: What deployment artifacts and parameters influence how Cloud Foundry stages an app and creates running instances? | 0.9069 | NO_EXACT_DUPLICATE_REVIEW_REQUIRED |
| RAGDEV004 | SUPPORTED | Q002: How can I connect a Cloud Foundry application with a BTP service? | 0.2000 | Q012: Which roles are available in the Cloud Foundry environment? | 0.8351 | NO_EXACT_DUPLICATE_REVIEW_REQUIRED |
| RAGDEV005 | SUPPORTED | HOUT003: What deployment artifacts and parameters influence how Cloud Foundry stages an app and creates running instances? | 0.2105 | HOUT003: What deployment artifacts and parameters influence how Cloud Foundry stages an app and creates running instances? | 0.8400 | NO_EXACT_DUPLICATE_REVIEW_REQUIRED |
| RAGDEV006 | SUPPORTED | Q027: What is the SAP BTP Cloud Foundry environment? | 0.2667 | Q027: What is the SAP BTP Cloud Foundry environment? | 0.8764 | NO_EXACT_DUPLICATE_REVIEW_REQUIRED |
| RAGDEV007 | SUPPORTED | Q016: How do I create a route for a Cloud Foundry application? | 0.2727 | Q016: How do I create a route for a Cloud Foundry application? | 0.8780 | NO_EXACT_DUPLICATE_REVIEW_REQUIRED |
| RAGDEV008 | SUPPORTED | Q013: What permissions do Cloud Foundry roles provide? | 0.2857 | Q013: What permissions do Cloud Foundry roles provide? | 0.9115 | NO_EXACT_DUPLICATE_REVIEW_REQUIRED |
| RAGDEV009 | SUPPORTED | HOUT010: Can I stream application instance output while reproducing an error in SAP BTP Cloud Foundry? | 0.3333 | HOUT010: Can I stream application instance output while reproducing an error in SAP BTP Cloud Foundry? | 0.9068 | NO_EXACT_DUPLICATE_REVIEW_REQUIRED |
| RAGDEV010 | SUPPORTED | Q016: How do I create a route for a Cloud Foundry application? | 0.2308 | HOUT011: Which Cloud Foundry record helps confirm that the platform processed scaling deployment or crash-related actions? | 0.8371 | NO_EXACT_DUPLICATE_REVIEW_REQUIRED |
| RAGDEV011 | SUPPORTED | HOUT024: An external scheduler and a deployed application both need the same service instance. Why might they use different credential mechanisms? | 0.2381 | HOUT012: How can service-instance credentials be issued for a command-line tool that runs outside the application lifecycle? | 0.8643 | NO_EXACT_DUPLICATE_REVIEW_REQUIRED |
| RAGDEV012 | SUPPORTED | Q020: How do I manage quota limits for a Cloud Foundry space? | 0.3333 | Q020: How do I manage quota limits for a Cloud Foundry space? | 0.8873 | NO_EXACT_DUPLICATE_REVIEW_REQUIRED |
| RAGDEV013 | SUPPORTED | Q027: What is the SAP BTP Cloud Foundry environment? | 0.3333 | Q027: What is the SAP BTP Cloud Foundry environment? | 0.8919 | NO_EXACT_DUPLICATE_REVIEW_REQUIRED |
| RAGDEV014 | SUPPORTED | Q030: How do application routes and destinations work together? | 0.3636 | Q030: How do application routes and destinations work together? | 0.8951 | NO_EXACT_DUPLICATE_REVIEW_REQUIRED |
| RAGDEV015 | SUPPORTED | CAL016: I need a concise explanation of what SAP BTP offers across development integration data analytics automation and AI. What is the platform scope? | 0.2500 | CAL016: I need a concise explanation of what SAP BTP offers across development integration data analytics automation and AI. What is the platform scope? | 0.8563 | NO_EXACT_DUPLICATE_REVIEW_REQUIRED |
| RAGDEV016 | SUPPORTED | V2F004: How do runtimes regions accounts entitlements and quotas fit together in SAP BTP? | 0.3333 | CAL017: I keep seeing subaccounts regions environments entitlements and quotas together. How do these basic SAP BTP concepts fit? | 0.8502 | NO_EXACT_DUPLICATE_REVIEW_REQUIRED |
| RAGDEV017 | NEAR_DOMAIN_UNSUPPORTED | Q025: How does an application consume services in SAP BTP? | 0.2222 | HOUT012: How can service-instance credentials be issued for a command-line tool that runs outside the application lifecycle? | 0.7416 | NO_EXACT_DUPLICATE_REVIEW_REQUIRED |
| RAGDEV018 | NEAR_DOMAIN_UNSUPPORTED | Q005: What is a service key used for in SAP BTP? | 0.2222 | CAL021: I want to manage SAP BTP from the cockpit for some tasks and a command line for others. What tool options are available? | 0.7012 | NO_EXACT_DUPLICATE_REVIEW_REQUIRED |
| RAGDEV019 | NEAR_DOMAIN_UNSUPPORTED | CAL033: How do I configure SAP Build Work Zone page layouts and widgets? | 0.2500 | CAL037: How can I configure principal propagation through SAP Cloud Connector? | 0.7859 | NO_EXACT_DUPLICATE_REVIEW_REQUIRED |
| RAGDEV020 | NEAR_DOMAIN_UNSUPPORTED | Q022: How do I deploy an application to the Cloud Foundry environment? | 0.1818 | V2F006: Where do I deploy applications and manage services within the SAP BTP account structure? | 0.7661 | NO_EXACT_DUPLICATE_REVIEW_REQUIRED |
| RAGDEV021 | OUT_OF_SCOPE | CAL039: How do I set up event mesh queues and subscriptions for asynchronous messaging? | 0.0833 | HOUT034: What practice routine helps a beginner learn jazz piano chords? | 0.5756 | NO_EXACT_DUPLICATE_REVIEW_REQUIRED |
| RAGDEV022 | OUT_OF_SCOPE | Q001: How do I bind an application to an existing service instance? | 0.0000 | CAL041: What is the best recipe for baking sourdough bread? | 0.5953 | NO_EXACT_DUPLICATE_REVIEW_REQUIRED |
| RAGDEV023 | OUT_OF_SCOPE | HOUT037: How do I plan a vegetable garden for a shaded balcony? | 0.1250 | HOUT039: How should I organize a small conference agenda for two tracks? | 0.5804 | NO_EXACT_DUPLICATE_REVIEW_REQUIRED |
| RAGDEV024 | OUT_OF_SCOPE | Q001: How do I bind an application to an existing service instance? | 0.0000 | HOUT040: What exercises strengthen wrists for rock climbing? | 0.6506 | NO_EXACT_DUPLICATE_REVIEW_REQUIRED |

## Supported Question Manual Distinctness Review

| Query ID | Manual Assessment | Rationale |
| --- | --- | --- |
| RAGDEV001 | DISTINCT_FACT_OR_TASK | Tests the Cloud Foundry platform basis rather than asking only what the environment is or which runtimes it supports. |
| RAGDEV002 | DISTINCT_FACT_OR_TASK | Tests where development-phase responsibilities are documented before operations work, not the prior workflow or tool-choice scenario. |
| RAGDEV003 | DISTINCT_FACT_OR_TASK | Tests identification of the deployment lifecycle documentation after development, not the detailed push process or deployment artifacts. |
| RAGDEV004 | DISTINCT_FACT_OR_TASK | Tests how managed service capabilities are represented before credential attachment, not how an application consumes a service. |
| RAGDEV005 | DISTINCT_FACT_OR_TASK | Tests the binding operation as the app-service relationship, not where bound credentials can be found. |
| RAGDEV006 | DISTINCT_FACT_OR_TASK | Tests configuration separation from source code, not the earlier feature-flag or endpoint-change examples. |
| RAGDEV007 | DISTINCT_FACT_OR_TASK | Tests reserving and managing route addresses, not only making an app reachable or assigning a route. |
| RAGDEV008 | DISTINCT_FACT_OR_TASK | Tests choosing the roles documentation for organization and space permission assignment, not generic role availability. |
| RAGDEV009 | DISTINCT_FACT_OR_TASK | Tests viewing recent instance output during troubleshooting, not crash diagnosis generally. |
| RAGDEV010 | DISTINCT_FACT_OR_TASK | Tests lifecycle record type identification for restaging or crashes, not broad event history lookup. |
| RAGDEV011 | DISTINCT_FACT_OR_TASK | Tests unbound service-instance credential artifacts, not service-key purpose in general. |
| RAGDEV012 | DISTINCT_FACT_OR_TASK | Tests locating documentation for assigning space resource limits, not explaining global entitlement or quota troubleshooting. |
| RAGDEV013 | DISTINCT_FACT_OR_TASK | Tests the feature that defines container network traffic rules, not a broad security-group how-to. |
| RAGDEV014 | DISTINCT_FACT_OR_TASK | Tests the relationship between routes and destination configuration for backend access, not only request forwarding. |
| RAGDEV015 | DISTINCT_FACT_OR_TASK | Tests SAP BTP as an extension and integration platform layer, not the broad capability inventory question. |
| RAGDEV016 | DISTINCT_FACT_OR_TASK | Tests where to learn shared terminology before service-specific guides, not an entitlement/quota failure scenario. |

## Result

The pre-execution RAG development dataset passes the exact duplicate check. Lexical and semantic nearest-neighbor diagnostics are recorded for review before any RAG development execution.
