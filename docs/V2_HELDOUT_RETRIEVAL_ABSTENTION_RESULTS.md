# Version 2 Fresh Held-Out Retrieval And Abstention Results

## Task Evidence

Frozen pre-execution commit:

- Commit: `4390d3b09d2b4824c58519e4c2723807afe613d1`
- Tag: `v2-heldout-preexecution`

Deployment:

- Command: `cf push btp-doc-assistant-app`
- Status: succeeded
- App route: `btp-doc-assistant-app.cfapps.eu01.hana.ondemand.com`
- Last uploaded: Wed 02 Sep 13:40:37 CEST 2026
- Runtime state after deployment: `running`, `1/1`

Cloud Foundry task:

- Task ID: `19`
- Task name: `evaluate-v2-heldout-retrieval-abstention`
- Command: `python scripts/evaluate_retrieval_abstention_heldout_v2.py`
- State: `SUCCEEDED`
- Exit status: `0`
- Start time: Wed, 02 Sep 2026 11:41:11 UTC

Warnings:

- Cloud Foundry reported that stack `cflinuxfs4` is deprecated and recommends migration to `cflinuxfs5`.
- FastEmbed/Hugging Face emitted an unauthenticated Hub request warning. No model, threshold, retrieval, corpus, or evaluator parameter was changed.

## Dataset

- Dataset: `data/retrieval_abstention_heldout_v2.csv`
- Total questions: 40
- Supported questions: 24
- Unsupported near-domain questions: 8
- Unsupported clearly out-of-scope questions: 8

The held-out set is final test evidence and will not be used for retrieval or abstention tuning.

## Frozen Configuration

- Dense model: `BAAI/bge-small-en-v1.5`
- HANA table: `DOCUMENT_CHUNKS_V2`
- Corpus chunks loaded: 138
- Corpus read time: 15.32 ms
- Lexical retrieval: existing BM25-style implementation over `TITLE`, `TOPIC`, and `CHUNK_TEXT`
- Dense ranking: full chunk ranking
- Lexical ranking: full chunk ranking
- Fusion: full dense plus full lexical Reciprocal Rank Fusion
- `RRF k`: `60`
- Reranker: none
- Candidate abstention gate: dense document-level top-1 cosine score `>= 0.75`
- Below `0.75`: abstain

No production abstention, LLM, or RAG behavior was implemented.

## Retrieval Metrics

Supported-query Hybrid RRF retrieval:

| Metric | Result |
| --- | ---: |
| Top-1 | 13/24 = 0.5417 |
| Top-3 | 19/24 = 0.7917 |
| Top-5 | 22/24 = 0.9167 |
| MRR | 0.6788 |

## Abstention Scope Metrics

| Metric | Result |
| --- | ---: |
| True accepts | 19 |
| False accepts | 2 |
| True abstentions | 14 |
| False rejects | 5 |
| Accept precision | 0.9048 |
| Supported accept recall | 0.7917 |
| Unsupported abstain rate | 0.8750 |
| Near-domain abstain rate | 0.7500 |
| Out-of-scope abstain rate | 1.0000 |

False accepts:

- `HOUT025`
- `HOUT028`

False rejects:

- `HOUT004`
- `HOUT005`
- `HOUT011`
- `HOUT017`
- `HOUT024`

## Top-3 Safety Metrics

| Metric | Result |
| --- | ---: |
| Safe accepts | 15 |
| Unsafe accepts | 6 |
| False rejects of otherwise safe questions | 4 |
| Accepted-answer precision | 0.7143 |
| Safe-answer recall | 0.7895 |
| Coverage | 0.5250 |

Top-3 unsafe accepts:

- `HOUT006`
- `HOUT008`
- `HOUT013`
- `HOUT020`
- `HOUT025`
- `HOUT028`

Top-3 safe-query false rejects:

- `HOUT004`
- `HOUT005`
- `HOUT017`
- `HOUT024`

## Top-5 Safety Metrics

| Metric | Result |
| --- | ---: |
| Safe accepts | 17 |
| Unsafe accepts | 4 |
| False rejects of otherwise safe questions | 5 |
| Accepted-answer precision | 0.8095 |
| Safe-answer recall | 0.7727 |
| Coverage | 0.5250 |

Top-5 unsafe accepts:

- `HOUT006`
- `HOUT008`
- `HOUT025`
- `HOUT028`

Top-5 safe-query false rejects:

- `HOUT004`
- `HOUT005`
- `HOUT011`
- `HOUT017`
- `HOUT024`

## Latency Metrics

Across all 40 held-out queries:

| Metric | Result |
| --- | ---: |
| Mean total retrieval latency | 53.77 ms |
| Median total retrieval latency | 51.94 ms |
| Minimum total retrieval latency | 37.22 ms |
| Maximum total retrieval latency | 87.53 ms |
| Mean embedding latency | 32.55 ms |
| Mean dense HANA latency | 16.56 ms |
| Mean lexical latency | 3.86 ms |
| Mean RRF fusion latency | 0.80 ms |

## Per-Query Results

```csv
QUERY_ID,EXPECTED_SUPPORTED,EXPECTED_DOCUMENT_ID,CATEGORY,EXPECTED_RANK,DENSE_RANK1_DOCUMENT_ID,DENSE_RANK1_SCORE,DENSE_RANK2_DOCUMENT_ID,DENSE_RANK2_SCORE,DENSE_RANK1_RANK2_MARGIN,HYBRID_RANK1_DOCUMENT_ID,HYBRID_RANK1_SCORE,HYBRID_RANK2_DOCUMENT_ID,HYBRID_RANK2_SCORE,HYBRID_RANK1_RANK2_MARGIN,HYBRID_TOP5_DOCUMENTS,DENSE_HYBRID_RANK1_AGREE,ACCEPT_DECISION,HYBRID_TOP1_CORRECT,HYBRID_TOP3_CORRECT,HYBRID_TOP5_CORRECT,SAFE_TO_ANSWER_TOP3,SAFE_TO_ANSWER_TOP5,EMBEDDING_MS,DENSE_HANA_MS,LEXICAL_MS,HYBRID_FUSION_MS,TOTAL_RETRIEVAL_MS
HOUT001,1,DOC001,supported_cloud_foundry_concepts,3,DOC001,0.9207,DOC002,0.9089,0.0118,DOC018,0.0323,DOC002,0.0306,0.0016,DOC018;DOC002;DOC001;DOC022;DOC004,0,ACCEPT,0,1,1,1,1,17.56,37.59,4.09,0.96,60.20
HOUT002,1,DOC002,supported_cloud_foundry_development,2,DOC002,0.8752,DOC003,0.8594,0.0158,DOC003,0.0317,DOC002,0.0299,0.0018,DOC003;DOC002;DOC022;DOC018;DOC004,0,ACCEPT,0,1,1,1,1,10.74,31.45,4.39,0.77,47.36
HOUT003,1,DOC003,supported_deployment,3,DOC002,0.7937,DOC004,0.7853,0.0083,DOC004,0.0323,DOC005,0.0308,0.0015,DOC004;DOC005;DOC003;DOC002;DOC012,0,ACCEPT,0,1,1,1,1,20.64,16.03,3.48,0.80,40.95
HOUT004,1,DOC004,supported_services,1,DOC004,0.7139,DOC013,0.6829,0.0310,DOC004,0.0328,DOC013,0.0323,0.0005,DOC004;DOC013;DOC005;DOC020;DOC018,1,ABSTAIN,1,1,1,1,1,34.84,10.93,3.38,0.67,49.82
HOUT005,1,DOC005,supported_service_bindings,1,DOC005,0.7427,DOC016,0.7010,0.0417,DOC005,0.0323,DOC016,0.0303,0.0020,DOC005;DOC016;DOC013;DOC009;DOC007,1,ABSTAIN,1,1,1,1,1,28.86,9.75,4.66,0.76,44.03
HOUT006,1,DOC006,supported_environment_variables,11,DOC016,0.7637,DOC015,0.6795,0.0842,DOC016,0.0296,DOC022,0.0285,0.0011,DOC016;DOC022;DOC019;DOC012;DOC015,1,ACCEPT,0,0,0,0,0,57.09,12.56,3.66,0.73,74.05
HOUT007,1,DOC007,supported_routes,1,DOC007,0.7946,DOC002,0.7362,0.0585,DOC007,0.0325,DOC021,0.0301,0.0024,DOC007;DOC021;DOC003;DOC016;DOC002,1,ACCEPT,1,1,1,1,1,27.06,34.45,3.42,0.71,65.65
HOUT008,1,DOC009,supported_spaces,6,DOC004,0.7682,DOC007,0.7618,0.0064,DOC010,0.0303,DOC002,0.0291,0.0012,DOC010;DOC002;DOC019;DOC007;DOC001,0,ACCEPT,0,0,0,0,0,22.40,11.35,3.93,0.95,38.63
HOUT009,1,DOC010,supported_roles,1,DOC010,0.8309,DOC004,0.8012,0.0298,DOC010,0.0328,DOC004,0.0304,0.0024,DOC010;DOC004;DOC005;DOC018;DOC006,1,ACCEPT,1,1,1,1,1,48.89,10.10,6.40,1.27,66.65
HOUT010,1,DOC011,supported_application_logs,2,DOC002,0.7727,DOC001,0.7620,0.0107,DOC005,0.0313,DOC011,0.0308,0.0005,DOC005;DOC011;DOC001;DOC003;DOC002,0,ACCEPT,0,1,1,1,1,30.03,9.94,3.28,0.69,43.94
HOUT011,1,DOC012,supported_application_events,4,DOC002,0.7352,DOC003,0.7287,0.0065,DOC003,0.0315,DOC001,0.0296,0.0019,DOC003;DOC001;DOC002;DOC012;DOC011,0,ABSTAIN,0,0,1,0,1,40.23,11.33,3.18,0.68,55.43
HOUT012,1,DOC013,supported_service_keys,1,DOC013,0.7685,DOC004,0.6985,0.0700,DOC013,0.0323,DOC022,0.0302,0.0021,DOC013;DOC022;DOC005;DOC010;DOC003,1,ACCEPT,1,1,1,1,1,29.89,10.42,3.43,0.68,44.42
HOUT013,1,DOC014,supported_space_quotas,4,DOC020,0.7681,DOC004,0.7649,0.0032,DOC020,0.0312,DOC018,0.0288,0.0025,DOC020;DOC018;DOC023;DOC014;DOC021,1,ACCEPT,0,0,1,0,1,43.90,10.39,4.81,1.15,60.26
HOUT014,1,DOC015,supported_security_groups,3,DOC016,0.7929,DOC005,0.7665,0.0264,DOC007,0.0318,DOC016,0.0313,0.0005,DOC007;DOC016;DOC015;DOC005;DOC006,0,ACCEPT,0,1,1,1,1,18.14,25.31,3.41,0.75,47.61
HOUT015,1,DOC016,supported_routes_destinations,1,DOC016,0.7822,DOC021,0.7524,0.0298,DOC016,0.0323,DOC007,0.0245,0.0078,DOC016;DOC007;DOC019;DOC018;DOC002,1,ACCEPT,1,1,1,1,1,28.27,13.16,6.03,0.91,48.37
HOUT016,1,DOC017,supported_platform_overview,1,DOC017,0.8353,DOC018,0.7857,0.0496,DOC017,0.0328,DOC018,0.0312,0.0015,DOC017;DOC018;DOC022;DOC021;DOC002,1,ACCEPT,1,1,1,1,1,53.08,14.67,3.70,0.72,72.17
HOUT017,1,DOC018,supported_basic_concepts,1,DOC018,0.7311,DOC020,0.7037,0.0274,DOC018,0.0323,DOC020,0.0300,0.0023,DOC018;DOC020;DOC009;DOC019;DOC021,1,ABSTAIN,1,1,1,1,1,38.73,13.39,3.53,0.68,56.33
HOUT018,1,DOC019,supported_account_model,1,DOC019,0.7981,DOC018,0.7930,0.0052,DOC019,0.0323,DOC020,0.0309,0.0014,DOC019;DOC020;DOC018;DOC021;DOC022,1,ACCEPT,1,1,1,1,1,27.87,13.31,3.47,0.71,45.36
HOUT019,1,DOC020,supported_entitlements_quotas,1,DOC020,0.7951,DOC019,0.7707,0.0244,DOC020,0.0313,DOC018,0.0292,0.0021,DOC020;DOC018;DOC014;DOC023;DOC009,1,ACCEPT,1,1,1,1,1,40.38,10.73,4.08,0.72,55.91
HOUT020,1,DOC021,supported_regions,5,DOC021,0.8238,DOC018,0.8081,0.0157,DOC018,0.0298,DOC017,0.0294,0.0004,DOC018;DOC017;DOC022;DOC019;DOC021,0,ACCEPT,0,0,1,0,1,29.27,19.94,5.03,0.86,55.10
HOUT021,1,DOC022,supported_tools,1,DOC022,0.8325,DOC018,0.8194,0.0130,DOC022,0.0310,DOC003,0.0308,0.0002,DOC022;DOC003;DOC018;DOC024;DOC002,1,ACCEPT,1,1,1,1,1,39.82,13.37,4.86,0.97,59.02
HOUT022,1,DOC023,supported_trial_free_tier,1,DOC023,0.8385,DOC024,0.8149,0.0236,DOC023,0.0325,DOC018,0.0290,0.0035,DOC023;DOC018;DOC024;DOC022;DOC020,1,ACCEPT,1,1,1,1,1,35.07,10.07,4.03,0.67,49.83
HOUT023,1,DOC024,supported_getting_started,1,DOC024,0.8078,DOC018,0.7842,0.0236,DOC024,0.0328,DOC018,0.0301,0.0027,DOC024;DOC018;DOC017;DOC004;DOC023,1,ACCEPT,1,1,1,1,1,27.18,10.83,5.59,0.86,44.46
HOUT024,1,DOC013,supported_service_credentials_confusable,3,DOC013,0.7356,DOC004,0.6682,0.0674,DOC016,0.0294,DOC005,0.0292,0.0002,DOC016;DOC005;DOC013;DOC018;DOC020,0,ABSTAIN,0,1,1,1,1,29.52,10.44,3.62,0.68,44.27
HOUT025,0,,unsupported_near_domain,0,DOC017,0.7614,DOC024,0.7223,0.0391,DOC017,0.0323,DOC024,0.0323,0.0000,DOC017;DOC024;DOC022;DOC018;DOC002,1,ACCEPT,0,0,0,0,0,37.06,13.31,2.99,0.67,54.04
HOUT026,0,,unsupported_near_domain,0,DOC002,0.7116,DOC003,0.7033,0.0083,DOC003,0.0323,DOC018,0.0305,0.0018,DOC003;DOC018;DOC002;DOC005;DOC006,0,ABSTAIN,0,0,0,0,0,32.55,10.30,3.51,1.26,47.63
HOUT027,0,,unsupported_near_domain,0,DOC020,0.6596,DOC005,0.6584,0.0012,DOC004,0.0310,DOC017,0.0310,0.0000,DOC004;DOC017;DOC020;DOC021;DOC016,0,ABSTAIN,0,0,0,0,0,34.03,11.76,3.05,0.66,49.50
HOUT028,0,,unsupported_near_domain,0,DOC016,0.7788,DOC002,0.7417,0.0371,DOC016,0.0294,DOC022,0.0278,0.0016,DOC016;DOC022;DOC007;DOC017;DOC002,1,ACCEPT,0,0,0,0,0,23.78,10.58,3.76,0.73,38.85
HOUT029,0,,unsupported_near_domain,0,DOC002,0.7357,DOC024,0.7171,0.0186,DOC017,0.0318,DOC024,0.0296,0.0021,DOC017;DOC024;DOC004;DOC002;DOC005,0,ABSTAIN,0,0,0,0,0,38.96,12.25,3.17,0.67,55.05
HOUT030,0,,unsupported_near_domain,0,DOC004,0.7397,DOC017,0.7295,0.0102,DOC017,0.0307,DOC012,0.0295,0.0012,DOC017;DOC012;DOC002;DOC022;DOC011,0,ABSTAIN,0,0,0,0,0,42.25,41.34,3.27,0.67,87.53
HOUT031,0,,unsupported_near_domain,0,DOC012,0.6630,DOC005,0.6484,0.0146,DOC004,0.0310,DOC005,0.0294,0.0016,DOC004;DOC005;DOC012;DOC022;DOC006,0,ABSTAIN,0,0,0,0,0,22.71,18.70,3.28,0.76,45.45
HOUT032,0,,unsupported_near_domain,0,DOC017,0.7296,DOC004,0.7142,0.0154,DOC017,0.0320,DOC018,0.0315,0.0005,DOC017;DOC018;DOC003;DOC005;DOC010,1,ABSTAIN,0,0,0,0,0,29.70,22.34,4.23,0.84,57.11
HOUT033,0,,unsupported_out_of_scope,0,DOC020,0.5679,DOC021,0.5499,0.0180,DOC020,0.0325,DOC021,0.0285,0.0040,DOC020;DOC021;DOC018;DOC014;DOC006,1,ABSTAIN,0,0,0,0,0,35.21,37.00,3.51,0.77,76.49
HOUT034,0,,unsupported_out_of_scope,0,DOC024,0.4900,DOC017,0.4680,0.0220,DOC024,0.0328,DOC015,0.0289,0.0039,DOC024;DOC015;DOC002;DOC017;DOC007,1,ABSTAIN,0,0,0,0,0,40.92,10.86,3.59,0.98,56.35
HOUT035,0,,unsupported_out_of_scope,0,DOC015,0.5301,DOC011,0.5048,0.0252,DOC015,0.0317,DOC004,0.0277,0.0041,DOC015;DOC004;DOC017;DOC011;DOC016,1,ABSTAIN,0,0,0,0,0,34.06,10.46,4.10,0.69,49.31
HOUT036,0,,unsupported_out_of_scope,0,DOC014,0.5433,DOC023,0.5305,0.0129,DOC019,0.0312,DOC021,0.0311,0.0002,DOC019;DOC021;DOC014;DOC020;DOC009,0,ABSTAIN,0,0,0,0,0,30.66,35.44,3.12,0.75,69.97
HOUT037,0,,unsupported_out_of_scope,0,DOC007,0.5415,DOC020,0.5334,0.0081,DOC020,0.0282,DOC014,0.0269,0.0013,DOC020;DOC014;DOC005;DOC021;DOC007,0,ABSTAIN,0,0,0,0,0,40.66,12.20,2.91,0.70,56.47
HOUT038,0,,unsupported_out_of_scope,0,DOC022,0.4043,DOC017,0.4028,0.0015,DOC009,0.0263,DOC010,0.0255,0.0008,DOC009;DOC010;DOC020;DOC015;DOC018,0,ABSTAIN,0,0,0,0,0,19.13,15.42,3.64,0.70,38.89
HOUT039,0,,unsupported_out_of_scope,0,DOC019,0.6027,DOC021,0.5631,0.0397,DOC019,0.0323,DOC009,0.0280,0.0042,DOC019;DOC009;DOC014;DOC017;DOC021,1,ABSTAIN,0,0,0,0,0,39.18,16.94,3.84,1.12,61.08
HOUT040,0,,unsupported_out_of_scope,0,DOC023,0.4560,DOC009,0.4128,0.0432,DOC009,0.0313,DOC023,0.0296,0.0017,DOC009;DOC023;DOC014;DOC015;DOC021,0,ABSTAIN,0,0,0,0,0,21.70,11.93,2.82,0.77,37.22
```

## Comparison With Calibration

Calibration behavior for the frozen `DENSE_SCORE_GE_0.75` candidate gate:

| Metric | Calibration | Held-Out |
| --- | ---: | ---: |
| Scope precision | 1.0000 | 0.9048 |
| Unsupported abstain rate | 1.0000 | 0.8750 |
| Near-domain abstain rate | 1.0000 | 0.7500 |
| Out-of-scope abstain rate | 1.0000 | 1.0000 |
| Supported accept recall | 0.6562 | 0.7917 |
| Top-3 accepted-answer precision | 0.9524 | 0.7143 |
| Top-3 safe-answer recall | 0.6452 | 0.7895 |
| Coverage | 0.4375 | 0.5250 |

Descriptive observations:

- Held-out supported accept recall improved relative to calibration.
- Held-out coverage increased relative to calibration.
- Held-out scope precision and unsupported abstain rate decreased because two near-domain unsupported questions were accepted: `HOUT025` and `HOUT028`.
- Held-out out-of-scope abstention remained perfect at 1.0000.
- Held-out answer-safety precision at Top-3 dropped because the accepted set included unsupported false accepts and supported retrievals whose expected document was outside Top-3.

This comparison is descriptive only. The threshold remains frozen at `0.75`; no retrieval or abstention tuning was performed from these held-out results.

## Final Evidence Boundary

The held-out set is final test evidence and will not be used for retrieval or abstention tuning.

No production abstention behavior, LLM behavior, or RAG behavior was implemented or modified.
