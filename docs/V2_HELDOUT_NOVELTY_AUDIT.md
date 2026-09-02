# Version 2 Held-Out Novelty Audit

## Purpose

This pre-execution audit checks the proposed held-out questions against prior Version 1, Version 2 foundation, and Version 2 calibration questions. It uses normalized lexical Jaccard overlap only. It does not query HANA, retrieve corpus documents, inspect retrieval scores, or execute the held-out evaluator.

## Inputs

- Held-out dataset: `data\retrieval_abstention_heldout_v2.csv`
- Prior question files:
  - `data\evaluation_queries.csv`
  - `data\evaluation_queries_v2_foundation.csv`
  - `data\retrieval_calibration_v2.csv`

## Method

For each held-out question, the audit tokenizes text, lowercases tokens, removes common question stopwords, computes lexical Jaccard overlap against every prior question, and reports the nearest prior question. Manual assessment is recorded as `DISTINCT` after reviewing the nearest prior match for scenario-level novelty.

## Results

| Held-Out ID | Nearest Prior ID | Similarity | Manual Assessment | Held-Out Question | Nearest Prior Question |
| --- | --- | ---: | --- | --- | --- |
| HOUT001 | Q027 | 0.3077 | DISTINCT | Does SAP BTP Cloud Foundry provide a standards-based runtime where applications can be staged and operated with Cloud Foundry concepts? | What is the SAP BTP Cloud Foundry environment? |
| HOUT002 | Q029 | 0.3125 | DISTINCT | Can a Cloud Foundry team mix local development workflows with SAP BTP tooling while preparing application code? | What development options are available in SAP BTP Cloud Foundry? |
| HOUT003 | Q023 | 0.2308 | DISTINCT | When a manifest-driven deployment does not behave as expected, what parts of the Cloud Foundry deployment process should I verify? | What is the process for pushing an application to Cloud Foundry? |
| HOUT004 | Q025 | 0.2500 | DISTINCT | How should I think about marketplace services and service instances before an application can consume a managed capability? | How does an application consume services in SAP BTP? |
| HOUT005 | CAL005 | 0.1200 | DISTINCT | If an app is moved between spaces, why must its service bindings be recreated or checked instead of assuming the old connection follows it? | I already created a database service instance. How do I make its connection information available to my application? |
| HOUT006 | CAL010 | 0.1429 | DISTINCT | Where should runtime-specific values such as destinations flags or credentials be represented so an app can read them at startup? | My app starts and then fails during startup. Where can I inspect the runtime output written by the app and platform? |
| HOUT007 | Q024 | 0.1667 | DISTINCT | If two applications need different hostnames in the same domain, what Cloud Foundry routing concept separates those entry points? | What services can applications use in the Cloud Foundry environment? |
| HOUT008 | Q024 | 0.2000 | DISTINCT | What administrative unit inside a Cloud Foundry org holds its own apps services routes and members? | What services can applications use in the Cloud Foundry environment? |
| HOUT009 | Q027 | 0.3077 | DISTINCT | How are user responsibilities separated between organization-level and space-level administration in SAP BTP Cloud Foundry? | What is the SAP BTP Cloud Foundry environment? |
| HOUT010 | Q006 | 0.2308 | DISTINCT | Where does Cloud Foundry expose recent stdout and stderr output when an application instance is being diagnosed? | How can I view logs from my Cloud Foundry application? |
| HOUT011 | Q009 | 0.2308 | DISTINCT | How can I distinguish application-generated log messages from platform-recorded lifecycle events during troubleshooting? | Where can I check recent application lifecycle events? |
| HOUT012 | Q013 | 0.2000 | DISTINCT | How can administrators provide standalone service-instance credentials for scripts or integrations that are not deployed as Cloud Foundry apps? | What permissions do Cloud Foundry roles provide? |
| HOUT013 | Q011 | 0.2000 | DISTINCT | How can an administrator cap memory routes or service usage for a Cloud Foundry space without changing global account entitlements? | What is a Cloud Foundry space used for? |
| HOUT014 | Q011 | 0.2308 | DISTINCT | What mechanism controls which external network destinations application containers may reach from a Cloud Foundry space? | What is a Cloud Foundry space used for? |
| HOUT015 | V2F004 | 0.1500 | DISTINCT | When an HTML5 frontend calls a backend through SAP BTP routing, where does destination configuration fit into that request path? | How do runtimes regions accounts entitlements and quotas fit together in SAP BTP? |
| HOUT016 | V2F009 | 0.1579 | DISTINCT | Why might an enterprise choose SAP BTP as a common layer for extending existing SAP landscapes and building new business applications? | What does a region mean for applications and services on SAP BTP? |
| HOUT017 | V2F007 | 0.1250 | DISTINCT | What platform concepts explain the difference between where resources are organized, where they run, and what services may be consumed? | What is the difference between an entitlement and a quota in SAP BTP? |
| HOUT018 | CAL018 | 0.2000 | DISTINCT | When should a company use directories or multiple subaccounts instead of putting all work under one account area? | Our company wants to separate global administration from deployable work areas. How should global accounts directories and subaccounts be used? |
| HOUT019 | CAL019 | 0.1538 | DISTINCT | Why can assigning entitlement to a subaccount still leave teams thinking carefully about quotas and available service plans? | A service tile appears in the cockpit but our subaccount still cannot create the selected plan. What entitlement or quota issue might explain this? |
| HOUT020 | Q005 | 0.2727 | DISTINCT | What does it mean for a SAP BTP service or application to be available only in certain regions? | What is a service key used for in SAP BTP? |
| HOUT021 | V2F002 | 0.1667 | DISTINCT | Which tooling categories help developers and administrators work with SAP BTP from browsers local machines or command lines? | How does SAP BTP help teams build extend integrate and use data? |
| HOUT022 | V2F013 | 0.2353 | DISTINCT | Can a team start with no-cost SAP BTP exploration and later use free service plans in a regular account model? | When should I use a trial account instead of free tier service plans? |
| HOUT023 | V2F015 | 0.2222 | DISTINCT | What initial onboarding paths does SAP BTP recommend for someone choosing an environment and learning basic platform tasks? | Where should a new user start after learning the basic SAP BTP concepts? |
| HOUT024 | CAL024 | 0.1481 | DISTINCT | If a team confuses service keys with app bindings, how should they decide which credential mechanism fits an app versus an external tool? | My app team says they need a service from the marketplace but operations says no binding exists yet. What is the difference between using a service and binding it? |
| HOUT025 | V2F002 | 0.1333 | DISTINCT | How do I model approval workflows and business rules in SAP Build Process Automation? | How does SAP BTP help teams build extend integrate and use data? |
| HOUT026 | V2F015 | 0.1176 | DISTINCT | What serving template should I choose for deploying a machine learning model in SAP AI Core? | Where should a new user start after learning the basic SAP BTP concepts? |
| HOUT027 | Q025 | 0.1818 | DISTINCT | How do I configure push notifications and offline stores in SAP Mobile Services? | How does an application consume services in SAP BTP? |
| HOUT028 | Q027 | 0.2000 | DISTINCT | What transport nodes and routes are required in SAP Cloud Transport Management? | What is the SAP BTP Cloud Foundry environment? |
| HOUT029 | Q010 | 0.2000 | DISTINCT | How do I create a planning model and story in SAP Analytics Cloud? | How do I create or manage spaces in Cloud Foundry? |
| HOUT030 | Q027 | 0.2000 | DISTINCT | Which monitoring use cases are covered by SAP Cloud ALM for operations? | What is the SAP BTP Cloud Foundry environment? |
| HOUT031 | Q004 | 0.2222 | DISTINCT | How do I create conditions and actions in SAP Alert Notification service? | How do I create a service key for a service instance? |
| HOUT032 | Q005 | 0.1667 | DISTINCT | What repository roles are needed for SAP Document Management service integration option? | What is a service key used for in SAP BTP? |
| HOUT033 | Q001 | 0.0000 | DISTINCT | How do I compare fixed-rate and variable-rate student loans? | How do I bind an application to an existing service instance? |
| HOUT034 | Q001 | 0.0000 | DISTINCT | What practice routine helps a beginner learn jazz piano chords? | How do I bind an application to an existing service instance? |
| HOUT035 | Q007 | 0.1111 | DISTINCT | How can I diagnose why a car engine overheats in traffic? | Where can I check why my application crashed? |
| HOUT036 | Q011 | 0.1250 | DISTINCT | What factors should I consider when buying a used apartment? | What is a Cloud Foundry space used for? |
| HOUT037 | CAL019 | 0.0500 | DISTINCT | How do I plan a vegetable garden for a shaded balcony? | A service tile appears in the cockpit but our subaccount still cannot create the selected plan. What entitlement or quota issue might explain this? |
| HOUT038 | Q001 | 0.0000 | DISTINCT | What are the major themes in the novel Frankenstein? | How do I bind an application to an existing service instance? |
| HOUT039 | Q001 | 0.0000 | DISTINCT | How should I organize a small conference agenda for two tracks? | How do I bind an application to an existing service instance? |
| HOUT040 | Q001 | 0.0000 | DISTINCT | What exercises strengthen wrists for rock climbing? | How do I bind an application to an existing service instance? |

## Summary

- Held-out questions checked: 40
- Prior questions checked: 94
- Exact duplicates found: 0
- Manual `TOO_SIMILAR` assessments remaining: 0
- HANA retrieval executed: no
- Held-out evaluator executed: no

Unsupported near-domain families were checked against the active source catalog by title/topic. The current source list covers SAP BTP platform overview, Cloud Foundry, services, routes, roles, logs, events, account model, entitlements, regions, tools, trial/free tier, and getting started. It does not include SAP Build Process Automation, SAP AI Core, SAP Mobile Services, SAP Cloud Transport Management, SAP Analytics Cloud, SAP Cloud ALM, Alert Notification, or SAP Document Management service-specific documentation.
