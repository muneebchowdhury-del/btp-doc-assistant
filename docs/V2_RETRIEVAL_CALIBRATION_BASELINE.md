# Version 2 Retrieval Calibration Baseline

Date: 2026-09-01  
Branch: `rag-v2`  
Evaluated commit: `38c1a7d`  
Task name: `evaluate-v2-retrieval-calibration-baseline`  
Task ID: `14`  
Task status: `SUCCEEDED`  
Command: `cf run-task btp-doc-assistant-app --command "python scripts/evaluate_retrieval_calibration_v2.py" --name evaluate-v2-retrieval-calibration-baseline -m 1G`

## Scope

This run executed the pre-registered vector-only calibration baseline against `DOCUMENT_CHUNKS_V2`.

No calibration questions, expected labels, embedding model, chunking, corpus contents, retrieval SQL, scoring, reranking, hybrid retrieval, abstention logic, LLM, or RAG behavior were changed.

The Cloud Foundry app was pushed first so the merged `rag-v2` calibration script and CSV were available in the bound runtime.

## Run Header

```text
SAP BTP Documentation Assistant
Version 2 Retrieval Calibration Baseline
==========================================================================================
Calibration file: data/retrieval_calibration_v2.csv
Target table: DOCUMENT_CHUNKS_V2
Embedding model: BAAI/bge-small-en-v1.5
Questions: 48
This script evaluates the existing vector-only baseline and does not write to HANA.
```

## Supported Metrics

Supported questions evaluated: 32

| Metric | Result |
| --- | --- |
| Top-1 Accuracy | 0.5938 (19/32) |
| Top-3 Accuracy | 0.9062 (29/32) |
| Top-5 Accuracy | 0.9062 (29/32) |
| MRR | 0.7461 |

## Supported-Query Misses

Top-1 misses:

| Query | Expected | Expected Rank | Rank 1 | Rank 1 Score | Rank 2 | Rank 2 Score | Margin | Top 5 |
| --- | --- | ---: | --- | ---: | --- | ---: | ---: | --- |
| CAL001 | DOC001 | 3 | DOC002 | 0.8711 | DOC022 | 0.8412 | 0.0299 | DOC002;DOC022;DOC001;DOC018;DOC003 |
| CAL004 | DOC004 | 2 | DOC005 | 0.7284 | DOC004 | 0.7182 | 0.0102 | DOC005;DOC004;DOC013;DOC016;DOC007 |
| CAL006 | DOC006 | 8 | DOC021 | 0.7590 | DOC010 | 0.7119 | 0.0471 | DOC021;DOC010;DOC007;DOC002;DOC004 |
| CAL007 | DOC007 | 2 | DOC016 | 0.7186 | DOC007 | 0.7119 | 0.0066 | DOC016;DOC007;DOC015;DOC021;DOC005 |
| CAL008 | DOC009 | 3 | DOC002 | 0.7861 | DOC019 | 0.7833 | 0.0028 | DOC002;DOC019;DOC009;DOC007;DOC010 |
| CAL009 | DOC010 | 2 | DOC002 | 0.7444 | DOC010 | 0.7350 | 0.0094 | DOC002;DOC010;DOC004;DOC005;DOC007 |
| CAL020 | DOC021 | 2 | DOC019 | 0.8532 | DOC021 | 0.8117 | 0.0415 | DOC019;DOC021;DOC018;DOC022;DOC020 |
| CAL024 | DOC004 | 3 | DOC005 | 0.8066 | DOC007 | 0.7144 | 0.0921 | DOC005;DOC007;DOC004;DOC013;DOC018 |
| CAL025 | DOC005 | 2 | DOC013 | 0.7411 | DOC005 | 0.7175 | 0.0235 | DOC013;DOC005;DOC004;DOC016;DOC007 |
| CAL026 | DOC013 | 2 | DOC005 | 0.7018 | DOC013 | 0.6905 | 0.0113 | DOC005;DOC013;DOC004;DOC016;DOC010 |
| CAL029 | DOC011 | 2 | DOC012 | 0.6653 | DOC011 | 0.6607 | 0.0047 | DOC012;DOC011;DOC015;DOC016;DOC005 |
| CAL031 | DOC009 | 12 | DOC002 | 0.7694 | DOC004 | 0.7506 | 0.0188 | DOC002;DOC004;DOC003;DOC020;DOC007 |
| CAL032 | DOC014 | 6 | DOC020 | 0.8674 | DOC018 | 0.8311 | 0.0363 | DOC020;DOC018;DOC019;DOC009;DOC021 |

Outside Top-3 and Top-5:

| Query | Expected | Expected Rank | Rank 1 | Top 5 |
| --- | --- | ---: | --- | --- |
| CAL006 | DOC006 | 8 | DOC021 | DOC021;DOC010;DOC007;DOC002;DOC004 |
| CAL031 | DOC009 | 12 | DOC002 | DOC002;DOC004;DOC003;DOC020;DOC007 |
| CAL032 | DOC014 | 6 | DOC020 | DOC020;DOC018;DOC019;DOC009;DOC021 |

## Unsupported Summary

Unsupported questions are not assigned a correct document. These rows are preserved only as retrieval signals for later abstention calibration.

Near-domain unsupported questions produced substantially higher rank-1 scores than clearly out-of-scope questions.

| Unsupported Group | Count | Rank-1 Score Mean | Rank-1 Score Min | Rank-1 Score Max | Margin Mean | Margin Min | Margin Max |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| Near-domain SAP/BTP | 8 | 0.6989 | 0.6225 | 0.7388 | 0.0128 | 0.0009 | 0.0478 |
| Clearly out-of-scope | 8 | 0.5121 | 0.4652 | 0.5547 | 0.0203 | 0.0027 | 0.0409 |

Notable unsupported patterns:

- Near-domain unsupported rank-1 scores overlap with supported scores and often have very small margins, especially CAL035, CAL038, CAL039, and CAL040.
- Clearly out-of-scope questions have lower rank-1 scores overall, but margins are not consistently smaller than near-domain margins.
- Score alone appears more informative for broad out-of-scope separation than for near-domain abstention. No threshold is chosen in this document.

## Unsupported Retrieval Signals

| Query | Category | Rank 1 | Rank 1 Score | Rank 2 | Rank 2 Score | Margin | Top 5 |
| --- | --- | --- | ---: | --- | ---: | ---: | --- |
| CAL033 | unsupported_near_domain | DOC006 | 0.6860 | DOC005 | 0.6808 | 0.0052 | DOC006;DOC005;DOC003;DOC002;DOC022 |
| CAL034 | unsupported_near_domain | DOC017 | 0.7316 | DOC022 | 0.7067 | 0.0249 | DOC017;DOC022;DOC003;DOC018;DOC002 |
| CAL035 | unsupported_near_domain | DOC002 | 0.6409 | DOC017 | 0.6400 | 0.0009 | DOC002;DOC017;DOC022;DOC019;DOC013 |
| CAL036 | unsupported_near_domain | DOC022 | 0.7388 | DOC006 | 0.6910 | 0.0478 | DOC022;DOC006;DOC002;DOC021;DOC018 |
| CAL037 | unsupported_near_domain | DOC003 | 0.7286 | DOC002 | 0.7167 | 0.0119 | DOC003;DOC002;DOC016;DOC001;DOC017 |
| CAL038 | unsupported_near_domain | DOC020 | 0.7086 | DOC023 | 0.7037 | 0.0049 | DOC020;DOC023;DOC018;DOC014;DOC019 |
| CAL039 | unsupported_near_domain | DOC005 | 0.6225 | DOC016 | 0.6202 | 0.0023 | DOC005;DOC016;DOC007;DOC021;DOC002 |
| CAL040 | unsupported_near_domain | DOC019 | 0.7341 | DOC022 | 0.7298 | 0.0043 | DOC019;DOC022;DOC018;DOC005;DOC013 |
| CAL041 | unsupported_out_of_scope | DOC005 | 0.4892 | DOC002 | 0.4726 | 0.0165 | DOC005;DOC002;DOC009;DOC007;DOC011 |
| CAL042 | unsupported_out_of_scope | DOC017 | 0.5096 | DOC015 | 0.4687 | 0.0409 | DOC017;DOC015;DOC022;DOC005;DOC013 |
| CAL043 | unsupported_out_of_scope | DOC016 | 0.5380 | DOC020 | 0.5124 | 0.0256 | DOC016;DOC020;DOC007;DOC023;DOC019 |
| CAL044 | unsupported_out_of_scope | DOC012 | 0.4895 | DOC009 | 0.4568 | 0.0327 | DOC012;DOC009;DOC015;DOC019;DOC010 |
| CAL045 | unsupported_out_of_scope | DOC023 | 0.5071 | DOC024 | 0.4828 | 0.0243 | DOC023;DOC024;DOC020;DOC019;DOC014 |
| CAL046 | unsupported_out_of_scope | DOC019 | 0.5547 | DOC020 | 0.5510 | 0.0038 | DOC019;DOC020;DOC018;DOC023;DOC021 |
| CAL047 | unsupported_out_of_scope | DOC023 | 0.4652 | DOC021 | 0.4625 | 0.0027 | DOC023;DOC021;DOC015;DOC017;DOC019 |
| CAL048 | unsupported_out_of_scope | DOC006 | 0.5434 | DOC003 | 0.5271 | 0.0162 | DOC006;DOC003;DOC002;DOC015;DOC009 |

## Full Detailed Output

```csv
QUERY_ID,EXPECTED_SUPPORTED,EXPECTED_DOCUMENT_ID,CATEGORY,EXPECTED_RANK,RANK1_DOCUMENT_ID,RANK1_SCORE,RANK2_DOCUMENT_ID,RANK2_SCORE,RANK1_RANK2_MARGIN,TOP5_DOCUMENTS,TOP1_CORRECT,TOP3_CORRECT,TOP5_CORRECT,RECIPROCAL_RANK,EMBEDDING_MS,HANA_QUERY_MS
CAL001,1,DOC001,supported_cloud_foundry_concepts,3,DOC002,0.8711,DOC022,0.8412,0.0299,DOC002;DOC022;DOC001;DOC018;DOC003,0,1,1,0.3333,43.87,13.22
CAL002,1,DOC002,supported_cloud_foundry_development,1,DOC002,0.8115,DOC003,0.8008,0.0107,DOC002;DOC003;DOC005;DOC004;DOC006,1,1,1,1.0,40.05,8.91
CAL003,1,DOC003,supported_deployment,1,DOC003,0.8631,DOC002,0.8508,0.0123,DOC003;DOC002;DOC001;DOC005;DOC004,1,1,1,1.0,32.73,9.66
CAL004,1,DOC004,supported_services,2,DOC005,0.7284,DOC004,0.7182,0.0102,DOC005;DOC004;DOC013;DOC016;DOC007,0,1,1,0.5,38.32,10.13
CAL005,1,DOC005,supported_service_bindings,1,DOC005,0.7104,DOC004,0.6735,0.0369,DOC005;DOC004;DOC013;DOC006;DOC016,1,1,1,1.0,29.4,11.32
CAL006,1,DOC006,supported_environment_variables,8,DOC021,0.759,DOC010,0.7119,0.0471,DOC021;DOC010;DOC007;DOC002;DOC004,0,0,0,0.125,43.06,10.63
CAL007,1,DOC007,supported_routes,2,DOC016,0.7186,DOC007,0.7119,0.0066,DOC016;DOC007;DOC015;DOC021;DOC005,0,1,1,0.5,34.27,9.67
CAL008,1,DOC009,supported_spaces,3,DOC002,0.7861,DOC019,0.7833,0.0028,DOC002;DOC019;DOC009;DOC007;DOC010,0,1,1,0.3333,33.36,9.56
CAL009,1,DOC010,supported_roles,2,DOC002,0.7444,DOC010,0.735,0.0094,DOC002;DOC010;DOC004;DOC005;DOC007,0,1,1,0.5,37.54,10.41
CAL010,1,DOC011,supported_application_logs,1,DOC011,0.6448,DOC012,0.6276,0.0172,DOC011;DOC012;DOC022;DOC002;DOC023,1,1,1,1.0,40.32,8.78
CAL011,1,DOC012,supported_application_events,1,DOC012,0.6863,DOC011,0.6652,0.0211,DOC012;DOC011;DOC013;DOC016;DOC023,1,1,1,1.0,38.63,10.72
CAL012,1,DOC013,supported_service_keys,1,DOC013,0.7457,DOC005,0.7014,0.0443,DOC013;DOC005;DOC004;DOC006;DOC016,1,1,1,1.0,32.79,8.2
CAL013,1,DOC014,supported_space_quotas,1,DOC014,0.8341,DOC009,0.7863,0.0478,DOC014;DOC009;DOC020;DOC023;DOC019,1,1,1,1.0,50.99,9.94
CAL014,1,DOC015,supported_security_groups,1,DOC015,0.7754,DOC007,0.7304,0.045,DOC015;DOC007;DOC016;DOC002;DOC005,1,1,1,1.0,38.34,9.27
CAL015,1,DOC016,supported_routes_destinations,1,DOC016,0.7934,DOC007,0.7522,0.0412,DOC016;DOC007;DOC002;DOC019;DOC021,1,1,1,1.0,40.72,7.99
CAL016,1,DOC017,supported_platform_overview,1,DOC017,0.8305,DOC022,0.7727,0.0578,DOC017;DOC022;DOC018;DOC002;DOC003,1,1,1,1.0,35.59,8.51
CAL017,1,DOC018,supported_basic_concepts,1,DOC018,0.867,DOC019,0.8348,0.0323,DOC018;DOC019;DOC020;DOC021;DOC017,1,1,1,1.0,31.14,8.02
CAL018,1,DOC019,supported_account_model,1,DOC019,0.8162,DOC018,0.7961,0.0201,DOC019;DOC018;DOC020;DOC021;DOC023,1,1,1,1.0,22.75,8.38
CAL019,1,DOC020,supported_entitlements_quotas,1,DOC020,0.7516,DOC005,0.7393,0.0123,DOC020;DOC005;DOC009;DOC014;DOC019,1,1,1,1.0,48.18,9.32
CAL020,1,DOC021,supported_regions,2,DOC019,0.8532,DOC021,0.8117,0.0415,DOC019;DOC021;DOC018;DOC022;DOC020,0,1,1,0.5,34.37,10.11
CAL021,1,DOC022,supported_tools,1,DOC022,0.8307,DOC003,0.7826,0.0481,DOC022;DOC003;DOC018;DOC017;DOC006,1,1,1,1.0,29.49,9.45
CAL022,1,DOC023,supported_trial_free_tier,1,DOC023,0.8705,DOC024,0.8365,0.034,DOC023;DOC024;DOC018;DOC020;DOC022,1,1,1,1.0,30.31,12.14
CAL023,1,DOC024,supported_getting_started,1,DOC024,0.806,DOC017,0.7663,0.0396,DOC024;DOC017;DOC002;DOC022;DOC018,1,1,1,1.0,37.46,9.55
CAL024,1,DOC004,supported_services_confusable,3,DOC005,0.8066,DOC007,0.7144,0.0921,DOC005;DOC007;DOC004;DOC013;DOC018,0,1,1,0.3333,36.33,9.95
CAL025,1,DOC005,supported_service_bindings_confusable,2,DOC013,0.7411,DOC005,0.7175,0.0235,DOC013;DOC005;DOC004;DOC016;DOC007,0,1,1,0.5,33.14,9.8
CAL026,1,DOC013,supported_service_keys_confusable,2,DOC005,0.7018,DOC013,0.6905,0.0113,DOC005;DOC013;DOC004;DOC016;DOC010,0,1,1,0.5,43.72,8.98
CAL027,1,DOC007,supported_routes_confusable,1,DOC007,0.7955,DOC016,0.7425,0.053,DOC007;DOC016;DOC015;DOC021;DOC005,1,1,1,1.0,32.92,9.59
CAL028,1,DOC016,supported_routes_destinations_confusable,1,DOC016,0.7673,DOC007,0.7084,0.0589,DOC016;DOC007;DOC015;DOC019;DOC021,1,1,1,1.0,44.25,10.26
CAL029,1,DOC011,supported_monitoring_confusable,2,DOC012,0.6653,DOC011,0.6607,0.0047,DOC012;DOC011;DOC015;DOC016;DOC005,0,1,1,0.5,30.21,10.02
CAL030,1,DOC012,supported_monitoring_confusable,1,DOC012,0.7488,DOC011,0.6718,0.077,DOC012;DOC011;DOC015;DOC013;DOC016,1,1,1,1.0,34.08,11.67
CAL031,1,DOC009,supported_account_quota_confusable,12,DOC002,0.7694,DOC004,0.7506,0.0188,DOC002;DOC004;DOC003;DOC020;DOC007,0,0,0,0.0833,50.56,9.89
CAL032,1,DOC014,supported_account_quota_confusable,6,DOC020,0.8674,DOC018,0.8311,0.0363,DOC020;DOC018;DOC019;DOC009;DOC021,0,0,0,0.1667,39.07,8.95
CAL033,0,,unsupported_near_domain,0,DOC006,0.686,DOC005,0.6808,0.0052,DOC006;DOC005;DOC003;DOC002;DOC022,0,0,0,0.0,31.04,8.06
CAL034,0,,unsupported_near_domain,0,DOC017,0.7316,DOC022,0.7067,0.0249,DOC017;DOC022;DOC003;DOC018;DOC002,0,0,0,0.0,27.25,8.0
CAL035,0,,unsupported_near_domain,0,DOC002,0.6409,DOC017,0.64,0.0009,DOC002;DOC017;DOC022;DOC019;DOC013,0,0,0,0.0,43.33,8.42
CAL036,0,,unsupported_near_domain,0,DOC022,0.7388,DOC006,0.691,0.0478,DOC022;DOC006;DOC002;DOC021;DOC018,0,0,0,0.0,16.59,9.52
CAL037,0,,unsupported_near_domain,0,DOC003,0.7286,DOC002,0.7167,0.0119,DOC003;DOC002;DOC016;DOC001;DOC017,0,0,0,0.0,27.21,8.38
CAL038,0,,unsupported_near_domain,0,DOC020,0.7086,DOC023,0.7037,0.0049,DOC020;DOC023;DOC018;DOC014;DOC019,0,0,0,0.0,42.05,9.9
CAL039,0,,unsupported_near_domain,0,DOC005,0.6225,DOC016,0.6202,0.0023,DOC005;DOC016;DOC007;DOC021;DOC002,0,0,0,0.0,35.74,9.42
CAL040,0,,unsupported_near_domain,0,DOC019,0.7341,DOC022,0.7298,0.0043,DOC019;DOC022;DOC018;DOC005;DOC013,0,0,0,0.0,58.05,8.0
CAL041,0,,unsupported_out_of_scope,0,DOC005,0.4892,DOC002,0.4726,0.0165,DOC005;DOC002;DOC009;DOC007;DOC011,0,0,0,0.0,15.9,8.85
CAL042,0,,unsupported_out_of_scope,0,DOC017,0.5096,DOC015,0.4687,0.0409,DOC017;DOC015;DOC022;DOC005;DOC013,0,0,0,0.0,34.15,9.02
CAL043,0,,unsupported_out_of_scope,0,DOC016,0.538,DOC020,0.5124,0.0256,DOC016;DOC020;DOC007;DOC023;DOC019,0,0,0,0.0,26.13,10.45
CAL044,0,,unsupported_out_of_scope,0,DOC012,0.4895,DOC009,0.4568,0.0327,DOC012;DOC009;DOC015;DOC019;DOC010,0,0,0,0.0,23.8,9.33
CAL045,0,,unsupported_out_of_scope,0,DOC023,0.5071,DOC024,0.4828,0.0243,DOC023;DOC024;DOC020;DOC019;DOC014,0,0,0,0.0,26.73,9.94
CAL046,0,,unsupported_out_of_scope,0,DOC019,0.5547,DOC020,0.551,0.0038,DOC019;DOC020;DOC018;DOC023;DOC021,0,0,0,0.0,28.41,10.0
CAL047,0,,unsupported_out_of_scope,0,DOC023,0.4652,DOC021,0.4625,0.0027,DOC023;DOC021;DOC015;DOC017;DOC019,0,0,0,0.0,33.83,9.35
CAL048,0,,unsupported_out_of_scope,0,DOC006,0.5434,DOC003,0.5271,0.0162,DOC006;DOC003;DOC002;DOC015;DOC009,0,0,0,0.0,35.22,8.46
```

## Warnings And Notes

- Cloud Foundry app staging reported that stack `cflinuxfs4` is deprecated and scheduled for future retirement. This did not block the run.
- The Cloud Foundry task completed with `Exit status 0`.
- No abstention threshold was chosen or implemented.
- No reranking, hybrid retrieval, LLM, or RAG changes were implemented.
