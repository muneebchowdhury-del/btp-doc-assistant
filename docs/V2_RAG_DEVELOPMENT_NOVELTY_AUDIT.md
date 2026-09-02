# Version 2 RAG Development Novelty Audit

## Scope

This local-only audit checks the pre-registered RAG development questions against all prior Version 1, Version 2 foundation, Version 2 calibration, and Version 2 retrieval/abstention held-out questions.

The audit uses exact duplicate detection, normalized lexical Jaccard overlap, and local question-to-question embedding cosine similarity with FastEmbed `BAAI/bge-small-en-v1.5`. It does not query HANA, retrieve corpus documents, call Gemini, inspect retrieval scores, or execute the RAG development harness.

No arbitrary semantic-similarity rejection threshold is applied. Same-domain factual or conceptual overlap is expected because this is a development set over the same frozen corpus, not an independent final holdout.

The questions must not be interpreted as a fresh independent final evaluation set. Retrieval architecture and thresholds will not be tuned from these results. A completely fresh end-to-end RAG evaluation set will be created only after the generation architecture is finalized.

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

## Supported Question Manual Development-Set Review

| Query ID | Manual Assessment | Rationale |
| --- | --- | --- |
| RAGDEV001 | NEW_DEVELOPMENT_FORMULATION_OR_SCENARIO | Uses a new development formulation focused on the Cloud Foundry platform basis; factual overlap with prior Cloud Foundry environment questions is expected. |
| RAGDEV002 | NEW_DEVELOPMENT_FORMULATION_OR_SCENARIO | Uses a new development scenario about development-phase responsibility before operations; overlap with prior Cloud Foundry development questions is expected. |
| RAGDEV003 | NEW_DEVELOPMENT_FORMULATION_OR_SCENARIO | Uses a new development formulation about deployment lifecycle documentation after development; overlap with prior deployment questions is expected. |
| RAGDEV004 | NEW_DEVELOPMENT_FORMULATION_OR_SCENARIO | Uses a new service-representation framing before credentials are attached; overlap with prior service-consumption questions is expected. |
| RAGDEV005 | NEW_DEVELOPMENT_FORMULATION_OR_SCENARIO | Uses a new formulation around the app-service relationship created by binding; overlap with prior binding and credential questions is expected. |
| RAGDEV006 | NEW_DEVELOPMENT_FORMULATION_OR_SCENARIO | Uses a new configuration-management framing around source-code separation; overlap with prior environment-variable questions is expected. |
| RAGDEV007 | NEW_DEVELOPMENT_FORMULATION_OR_SCENARIO | Uses a new route-administration formulation around reserving and managing addresses; overlap with prior route questions is expected. |
| RAGDEV008 | NEW_DEVELOPMENT_FORMULATION_OR_SCENARIO | Uses a new permission-assignment scenario across organization and space roles; overlap with prior roles questions is expected. |
| RAGDEV009 | NEW_DEVELOPMENT_FORMULATION_OR_SCENARIO | Uses a new troubleshooting formulation focused on recent instance output; overlap with prior application-log questions is expected. |
| RAGDEV010 | NEW_DEVELOPMENT_FORMULATION_OR_SCENARIO | Uses a new formulation focused on lifecycle record type for restaging or crashes; overlap with prior application-event questions is expected. |
| RAGDEV011 | NEW_DEVELOPMENT_FORMULATION_OR_SCENARIO | Uses a new credential-artifact scenario for access without a running bound app; overlap with prior service-key questions is expected. |
| RAGDEV012 | NEW_DEVELOPMENT_FORMULATION_OR_SCENARIO | Uses a new documentation-location formulation for assigning space resource limits; overlap with prior quota questions is expected. |
| RAGDEV013 | NEW_DEVELOPMENT_FORMULATION_OR_SCENARIO | Uses a new feature-identification formulation for container network traffic rules; overlap with prior security-group questions is expected. |
| RAGDEV014 | NEW_DEVELOPMENT_FORMULATION_OR_SCENARIO | Uses a new routes-and-destinations relationship formulation for backend access; overlap with prior routing/destination questions is expected. |
| RAGDEV015 | NEW_DEVELOPMENT_FORMULATION_OR_SCENARIO | Uses a new overview framing around extension and integration across SAP landscapes; overlap with prior SAP BTP overview questions is expected. |
| RAGDEV016 | NEW_DEVELOPMENT_FORMULATION_OR_SCENARIO | Uses a new terminology-before-service-guides scenario; overlap with prior basic platform concept questions is expected. |

## Result

The pre-execution RAG development dataset passes the exact duplicate check. Lexical and semantic nearest-neighbor diagnostics are recorded for review before any RAG development execution.
