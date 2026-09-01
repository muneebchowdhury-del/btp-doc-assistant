# V2 BGE Reranker Experiment Results

## Task Status

- Failed infrastructure attempt: task `16`, `FAILED`, started `Tue, 01 Sep 2026 16:06:11 UTC`.
- Task 16 command: `cf run-task btp-doc-assistant-app --command "V2_RERANKER_MODEL_NAME=BAAI/bge-reranker-base python scripts/evaluate_retrieval_variants_v2.py" --name evaluate-v2-bge-reranker-experiment -m 3G`
- Task 16 failure: `RuntimeError: Task error: File reconstruction error: IO Error: No space left on device (os error 28)` while downloading/reconstructing `BAAI/bge-reranker-base`.
- Successful rerun: task `17`, `SUCCEEDED`, started `Tue, 01 Sep 2026 16:10:57 UTC`.
- Successful rerun command: `cf run-task btp-doc-assistant-app --command "V2_RERANKER_MODEL_NAME=BAAI/bge-reranker-base python scripts/evaluate_retrieval_variants_v2.py" --name evaluate-v2-bge-reranker-experiment -m 3G -k 4G`
- Successful rerun exit status: `0`.
- Corpus chunks loaded: `138`.

## Exact Configuration

- Calibration file: `data/retrieval_calibration_v2.csv`
- Target table: `DOCUMENT_CHUNKS_V2`
- Dense embedding model: `BAAI/bge-small-en-v1.5`
- Cross-encoder reranker: `BAAI/bge-reranker-base`
- Dense candidate chunks: `50`
- Lexical candidate chunks: `50`
- RRF k: `60`
- Questions: `48` (`32` supported, `16` unsupported)
- Task memory: `3G`
- Task disk: `4G` for the successful rerun only
- Production app memory/disk and production `app.py` were not changed.

## Runtime Warnings

- Task 16 failed before evaluation because the default task disk did not have enough free space for the BGE reranker download/reconstruction.
- Task 17 emitted the FastEmbed / Hugging Face unauthenticated Hub request warning and suggested setting `HF_TOKEN` for higher rate limits and faster downloads.
- The successful rerun downloaded the BGE model files and completed the full 48-query evaluation.

## Aggregate Supported Metrics

| Variant | Label | Top-1 | Top-3 | Top-5 | MRR | Mean latency ms | Mean rerank ms |
|---|---|---:|---:|---:|---:|---:|---:|
| A | Dense baseline | 0.5938 (19/32) | 0.9062 (29/32) | 0.9062 (29/32) | 0.7461 | 44.62 | 0.00 |
| B | Hybrid RRF | 0.5625 (18/32) | 0.9688 (31/32) | 0.9688 (31/32) | 0.7424 | 48.47 | 0.00 |
| C | Dense + cross-encoder reranking | 0.6562 (21/32) | 0.9062 (29/32) | 0.9375 (30/32) | 0.7847 | 2197.04 | 2152.43 |
| D | Hybrid RRF + cross-encoder reranking | 0.6562 (21/32) | 0.8750 (28/32) | 0.9375 (30/32) | 0.7769 | 3008.48 | 2960.00 |

## Candidate Recall Before Reranking

```csv
VARIANT,SUPPORTED_TOTAL,EXPECTED_PRESENT_COUNT,EXPECTED_PRESENT_RATE
C,32,32,1.0000
D,32,32,1.0000
```

All supported expected documents were present in the C and D candidate pools before reranking.

## Improvements And Regressions Vs A

| Variant | Improved | Regressed | Unchanged | Largest improvements | Largest regressions |
|---|---:|---:|---:|---|---|
| B | 7 | 6 | 19 | CAL006 8->2 (+6); CAL032 6->2 (+4); CAL008 3->1 (+2); CAL009 2->1 (+1); CAL020 2->1 (+1) | CAL010 1->3 (-2); CAL019 1->3 (-2); CAL002 1->2 (-1); CAL004 2->3 (-1); CAL012 1->2 (-1) |
| C | 9 | 6 | 17 | CAL006 8->1 (+7); CAL031 12->7 (+5); CAL001 3->1 (+2); CAL008 3->1 (+2); CAL007 2->1 (+1) | CAL004 2->10 (-8); CAL017 1->3 (-2); CAL002 1->2 (-1); CAL010 1->2 (-1); CAL018 1->2 (-1) |
| D | 9 | 6 | 17 | CAL006 8->1 (+7); CAL031 12->7 (+5); CAL001 3->1 (+2); CAL008 3->1 (+2); CAL007 2->1 (+1) | CAL004 2->10 (-8); CAL010 1->4 (-3); CAL017 1->3 (-2); CAL002 1->2 (-1); CAL018 1->2 (-1) |

## Major Supported Failure Cases

- Variant A: CAL006 expected DOC006 rank 8 top5 DOC021;DOC010;DOC007;DOC002;DOC004, CAL031 expected DOC009 rank 12 top5 DOC002;DOC004;DOC003;DOC020;DOC007, CAL032 expected DOC014 rank 6 top5 DOC020;DOC018;DOC019;DOC009;DOC021
- Variant B: CAL031 expected DOC009 rank 11 top5 DOC002;DOC020;DOC019;DOC007;DOC022
- Variant C: CAL004 expected DOC004 rank 10 top5 DOC013;DOC005;DOC002;DOC016;DOC009, CAL031 expected DOC009 rank 7 top5 DOC002;DOC019;DOC022;DOC001;DOC018
- Variant D: CAL004 expected DOC004 rank 10 top5 DOC013;DOC005;DOC002;DOC016;DOC009, CAL031 expected DOC009 rank 7 top5 DOC002;DOC019;DOC014;DOC013;DOC022

## Unsupported Query Behavior

### unsupported_near_domain

| Variant | Mean rank-1 score | Mean margin | Rank-1 documents |
|---|---:|---:|---|
| A | 0.6989 | 0.0128 | CAL033:DOC006(0.686,m=0.0052); CAL034:DOC017(0.7316,m=0.0249); CAL035:DOC002(0.6409,m=0.0009); CAL036:DOC022(0.7388,m=0.0478); CAL037:DOC003(0.7286,m=0.0119); CAL038:DOC020(0.7086,m=0.0049); CAL039:DOC005(0.6225,m=0.0023); CAL040:DOC019(0.7341,m=0.0043) |
| B | 0.0317 | 0.0016 | CAL033:DOC022(0.0291,m=0.0004); CAL034:DOC017(0.0323,m=0.0028); CAL035:DOC002(0.0325,m=0.0003); CAL036:DOC022(0.0325,m=0.0017); CAL037:DOC016(0.0318,m=0.0014); CAL038:DOC020(0.0325,m=0.0028); CAL039:DOC012(0.0308,m=0.0025); CAL040:DOC022(0.032,m=0.001) |
| C | -4.2318 | 1.9594 | CAL033:DOC006(-5.3268,m=0.7213); CAL034:DOC017(-5.0523,m=2.8211); CAL035:DOC002(-6.6636,m=0.1073); CAL036:DOC022(-2.8081,m=1.031); CAL037:DOC016(1.7113,m=7.4232); CAL038:DOC004(-6.306,m=1.5237); CAL039:DOC005(-5.4238,m=2.0109); CAL040:DOC002(-3.985,m=0.0368) |
| D | -4.1027 | 1.9749 | CAL033:DOC018(-4.2941,m=1.0327); CAL034:DOC017(-5.0523,m=2.8211); CAL035:DOC002(-6.6636,m=0.1073); CAL036:DOC022(-2.8081,m=1.031); CAL037:DOC016(1.7113,m=7.4232); CAL038:DOC004(-6.306,m=1.5237); CAL039:DOC005(-5.4238,m=1.8232); CAL040:DOC002(-3.985,m=0.0368) |

### unsupported_out_of_scope

| Variant | Mean rank-1 score | Mean margin | Rank-1 documents |
|---|---:|---:|---|
| A | 0.5121 | 0.0203 | CAL041:DOC005(0.4892,m=0.0165); CAL042:DOC017(0.5096,m=0.0409); CAL043:DOC016(0.538,m=0.0256); CAL044:DOC012(0.4895,m=0.0327); CAL045:DOC023(0.5071,m=0.0243); CAL046:DOC019(0.5547,m=0.0038); CAL047:DOC023(0.4652,m=0.0027); CAL048:DOC006(0.5434,m=0.0162) |
| B | 0.0301 | 0.0019 | CAL041:DOC002(0.0278,m=0.002); CAL042:DOC022(0.0313,m=0.0024); CAL043:DOC020(0.0296,m=0.0015); CAL044:DOC015(0.0313,m=0.0031); CAL045:DOC014(0.0296,m=0.0004); CAL046:DOC020(0.0298,m=0.0012); CAL047:DOC020(0.0313,m=0.0016); CAL048:DOC009(0.0303,m=0.0029) |
| C | -8.9007 | 0.7550 | CAL041:DOC003(-10.1919,m=0.0003); CAL042:DOC005(-8.1744,m=0.874); CAL043:DOC016(-7.663,m=1.7386); CAL044:DOC005(-7.9647,m=1.0003); CAL045:DOC023(-9.555,m=0.6345); CAL046:DOC020(-8.2965,m=1.5152); CAL047:DOC016(-10.1924,m=0.0); CAL048:DOC009(-9.1678,m=0.2775) |
| D | -8.8906 | 0.7261 | CAL041:DOC003(-10.1919,m=0.0003); CAL042:DOC005(-8.0941,m=0.9543); CAL043:DOC016(-7.663,m=1.7386); CAL044:DOC005(-7.9647,m=0.6884); CAL045:DOC023(-9.555,m=0.6345); CAL046:DOC020(-8.2965,m=1.5152); CAL047:DOC003(-10.192,m=0.0003); CAL048:DOC009(-9.1678,m=0.2775) |

Near-domain unsupported questions kept dense rank-1 scores in the same broad range as several supported misses. Clearly out-of-scope questions had lower dense rank-1 scores on average. BGE cross-encoder scores varied by candidate set and query type, but no abstention threshold was selected or implemented.

## Direct Comparison With MiniLM Experiment

The MiniLM comparison source is `docs/V2_RANKING_EXPERIMENT_RESULTS.md` from commit `1c23d6f`, tagged `v2-ranking-minilm-results`.

| Variant | MiniLM Top-1 | BGE Top-1 | Delta | MiniLM Top-3 | BGE Top-3 | Delta | MiniLM Top-5 | BGE Top-5 | Delta | MiniLM MRR | BGE MRR | Delta | MiniLM latency ms | BGE latency ms | Delta ms |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| A | 0.5938 | 0.5938 | +0.0000 | 0.9062 | 0.9062 | +0.0000 | 0.9062 | 0.9062 | +0.0000 | 0.7461 | 0.7461 | +0.0000 | 33.11 | 44.62 | +11.51 |
| B | 0.5625 | 0.5625 | +0.0000 | 0.9688 | 0.9688 | +0.0000 | 0.9688 | 0.9688 | +0.0000 | 0.7424 | 0.7424 | +0.0000 | 36.86 | 48.47 | +11.61 |
| C | 0.5625 | 0.6562 | +0.0937 | 0.8125 | 0.9062 | +0.0937 | 0.9688 | 0.9375 | -0.0313 | 0.7175 | 0.7847 | +0.0672 | 590.59 | 2197.04 | +1606.45 |
| D | 0.5625 | 0.6562 | +0.0937 | 0.8125 | 0.8750 | +0.0625 | 0.9375 | 0.9375 | +0.0000 | 0.7143 | 0.7769 | +0.0626 | 817.86 | 3008.48 | +2190.62 |

BGE improved aggregate C/D Top-1, Top-3, and MRR compared with MiniLM. Top-5 was lower for C and unchanged for D. The BGE reranker was substantially slower than MiniLM in this Cloud Foundry task run.

## Complete Per-Query Variant Output

Scores are only meaningful within the same variant family: cosine, RRF, and cross-encoder scores are on different scales and must not be compared numerically across variants.

| Variant | Query | Supported | Expected | Category | Expected rank | Rank 1 score | Rank 2 score | Margin | Top 5 documents | Latency ms | Rerank ms | Candidate expected present |
|---|---|---:|---|---|---:|---|---|---:|---|---:|---:|---|
| A | CAL001 | 1 | DOC001 | supported_cloud_foundry_concepts | 3 | DOC002 0.8711 | DOC022 0.8412 | 0.0299 | DOC002;DOC022;DOC001;DOC018;DOC003 | 67.58 | 0.0 | 0 |
| B | CAL001 | 1 | DOC001 | supported_cloud_foundry_concepts | 3 | DOC002 0.0328 | DOC022 0.0315 | 0.0013 | DOC002;DOC022;DOC001;DOC018;DOC003 | 72.22 | 0.0 | 0 |
| C | CAL001 | 1 | DOC001 | supported_cloud_foundry_concepts | 1 | DOC001 2.4984 | DOC002 2.2029 | 0.2954 | DOC001;DOC002;DOC018;DOC004;DOC022 | 3586.18 | 3518.6 | 1 |
| D | CAL001 | 1 | DOC001 | supported_cloud_foundry_concepts | 1 | DOC001 2.4984 | DOC002 2.2029 | 0.2954 | DOC001;DOC002;DOC018;DOC004;DOC022 | 3544.78 | 3472.56 | 1 |
| A | CAL002 | 1 | DOC002 | supported_cloud_foundry_development | 1 | DOC002 0.8115 | DOC003 0.8008 | 0.0107 | DOC002;DOC003;DOC005;DOC004;DOC006 | 23.93 | 0.0 | 0 |
| B | CAL002 | 1 | DOC002 | supported_cloud_foundry_development | 2 | DOC003 0.0323 | DOC002 0.0303 | 0.002 | DOC003;DOC002;DOC005;DOC018;DOC022 | 27.7 | 0.0 | 0 |
| C | CAL002 | 1 | DOC002 | supported_cloud_foundry_development | 2 | DOC003 1.3263 | DOC002 0.8956 | 0.4307 | DOC003;DOC002;DOC022;DOC006;DOC013 | 2716.09 | 2692.17 | 1 |
| D | CAL002 | 1 | DOC002 | supported_cloud_foundry_development | 2 | DOC003 1.3263 | DOC002 0.8956 | 0.4307 | DOC003;DOC002;DOC024;DOC022;DOC006 | 2584.44 | 2556.74 | 1 |
| A | CAL003 | 1 | DOC003 | supported_deployment | 1 | DOC003 0.8631 | DOC002 0.8508 | 0.0123 | DOC003;DOC002;DOC001;DOC005;DOC004 | 20.78 | 0.0 | 0 |
| B | CAL003 | 1 | DOC003 | supported_deployment | 1 | DOC003 0.0325 | DOC002 0.0308 | 0.0018 | DOC003;DOC002;DOC005;DOC006;DOC001 | 25.72 | 0.0 | 0 |
| C | CAL003 | 1 | DOC003 | supported_deployment | 1 | DOC003 4.9469 | DOC002 3.0469 | 1.8999 | DOC003;DOC002;DOC006;DOC022;DOC021 | 2088.62 | 2067.84 | 1 |
| D | CAL003 | 1 | DOC003 | supported_deployment | 1 | DOC003 4.9469 | DOC002 3.0469 | 1.8999 | DOC003;DOC002;DOC006;DOC022;DOC021 | 3435.6 | 3409.88 | 1 |
| A | CAL004 | 1 | DOC004 | supported_services | 2 | DOC005 0.7284 | DOC004 0.7182 | 0.0102 | DOC005;DOC004;DOC013;DOC016;DOC007 | 22.2 | 0.0 | 0 |
| B | CAL004 | 1 | DOC004 | supported_services | 3 | DOC013 0.0318 | DOC005 0.0318 | 0.0 | DOC013;DOC005;DOC004;DOC002;DOC001 | 26.71 | 0.0 | 0 |
| C | CAL004 | 1 | DOC004 | supported_services | 10 | DOC013 -2.8898 | DOC005 -2.9975 | 0.1078 | DOC013;DOC005;DOC002;DOC016;DOC009 | 2833.39 | 2811.19 | 1 |
| D | CAL004 | 1 | DOC004 | supported_services | 10 | DOC013 -2.8898 | DOC005 -2.9975 | 0.1078 | DOC013;DOC005;DOC002;DOC016;DOC009 | 3296.33 | 3269.62 | 1 |
| A | CAL005 | 1 | DOC005 | supported_service_bindings | 1 | DOC005 0.7104 | DOC004 0.6735 | 0.0369 | DOC005;DOC004;DOC013;DOC006;DOC016 | 66.28 | 0.0 | 0 |
| B | CAL005 | 1 | DOC005 | supported_service_bindings | 1 | DOC005 0.0325 | DOC013 0.0311 | 0.0014 | DOC005;DOC013;DOC007;DOC016;DOC004 | 71.58 | 0.0 | 0 |
| C | CAL005 | 1 | DOC005 | supported_service_bindings | 1 | DOC005 0.6309 | DOC013 -1.5657 | 2.1967 | DOC005;DOC013;DOC007;DOC004;DOC006 | 2290.31 | 2224.03 | 1 |
| D | CAL005 | 1 | DOC005 | supported_service_bindings | 1 | DOC005 0.6309 | DOC013 -1.5657 | 2.1967 | DOC005;DOC013;DOC007;DOC004;DOC006 | 4369.92 | 4298.33 | 1 |
| A | CAL006 | 1 | DOC006 | supported_environment_variables | 8 | DOC021 0.759 | DOC010 0.7119 | 0.0471 | DOC021;DOC010;DOC007;DOC002;DOC004 | 89.06 | 0.0 | 0 |
| B | CAL006 | 1 | DOC006 | supported_environment_variables | 2 | DOC021 0.032 | DOC006 0.029 | 0.003 | DOC021;DOC006;DOC013;DOC002;DOC016 | 92.95 | 0.0 | 0 |
| C | CAL006 | 1 | DOC006 | supported_environment_variables | 1 | DOC006 -2.5565 | DOC013 -3.5134 | 0.9569 | DOC006;DOC013;DOC022;DOC021;DOC002 | 1952.69 | 1863.63 | 1 |
| D | CAL006 | 1 | DOC006 | supported_environment_variables | 1 | DOC006 -2.5565 | DOC013 -3.5134 | 0.9569 | DOC006;DOC013;DOC022;DOC021;DOC002 | 3080.93 | 2987.98 | 1 |
| A | CAL007 | 1 | DOC007 | supported_routes | 2 | DOC016 0.7186 | DOC007 0.7119 | 0.0066 | DOC016;DOC007;DOC015;DOC021;DOC005 | 35.13 | 0.0 | 0 |
| B | CAL007 | 1 | DOC007 | supported_routes | 2 | DOC016 0.032 | DOC007 0.0315 | 0.0005 | DOC016;DOC007;DOC015;DOC021;DOC005 | 38.81 | 0.0 | 0 |
| C | CAL007 | 1 | DOC007 | supported_routes | 1 | DOC007 -4.7893 | DOC016 -4.8242 | 0.0349 | DOC007;DOC016;DOC005;DOC013;DOC015 | 2335.53 | 2300.41 | 1 |
| D | CAL007 | 1 | DOC007 | supported_routes | 1 | DOC007 -4.7893 | DOC016 -4.8242 | 0.0349 | DOC007;DOC016;DOC005;DOC013;DOC015 | 2900.11 | 2861.3 | 1 |
| A | CAL008 | 1 | DOC009 | supported_spaces | 3 | DOC002 0.7861 | DOC019 0.7833 | 0.0028 | DOC002;DOC019;DOC009;DOC007;DOC010 | 27.27 | 0.0 | 0 |
| B | CAL008 | 1 | DOC009 | supported_spaces | 1 | DOC009 0.0313 | DOC002 0.0306 | 0.0006 | DOC009;DOC002;DOC019;DOC003;DOC010 | 30.73 | 0.0 | 0 |
| C | CAL008 | 1 | DOC009 | supported_spaces | 1 | DOC009 5.1415 | DOC002 2.5099 | 2.6316 | DOC009;DOC002;DOC010;DOC006;DOC014 | 2299.84 | 2272.57 | 1 |
| D | CAL008 | 1 | DOC009 | supported_spaces | 1 | DOC009 5.1415 | DOC002 2.5099 | 2.6316 | DOC009;DOC002;DOC010;DOC006;DOC014 | 3581.0 | 3550.27 | 1 |
| A | CAL009 | 1 | DOC010 | supported_roles | 2 | DOC002 0.7444 | DOC010 0.735 | 0.0094 | DOC002;DOC010;DOC004;DOC005;DOC007 | 46.65 | 0.0 | 0 |
| B | CAL009 | 1 | DOC010 | supported_roles | 1 | DOC010 0.0306 | DOC007 0.0303 | 0.0003 | DOC010;DOC007;DOC005;DOC006;DOC001 | 50.8 | 0.0 | 0 |
| C | CAL009 | 1 | DOC010 | supported_roles | 1 | DOC010 0.02 | DOC009 -1.0259 | 1.0458 | DOC010;DOC009;DOC002;DOC007;DOC019 | 1605.84 | 1559.19 | 1 |
| D | CAL009 | 1 | DOC010 | supported_roles | 1 | DOC010 0.02 | DOC009 -1.0259 | 1.0458 | DOC010;DOC009;DOC002;DOC007;DOC019 | 2410.46 | 2359.66 | 1 |
| A | CAL010 | 1 | DOC011 | supported_application_logs | 1 | DOC011 0.6448 | DOC012 0.6276 | 0.0172 | DOC011;DOC012;DOC022;DOC002;DOC023 | 49.53 | 0.0 | 0 |
| B | CAL010 | 1 | DOC011 | supported_application_logs | 3 | DOC012 0.032 | DOC023 0.031 | 0.001 | DOC012;DOC023;DOC011;DOC018;DOC022 | 53.03 | 0.0 | 0 |
| C | CAL010 | 1 | DOC011 | supported_application_logs | 2 | DOC006 -6.6091 | DOC011 -7.0697 | 0.4606 | DOC006;DOC011;DOC002;DOC022;DOC004 | 2739.83 | 2690.3 | 1 |
| D | CAL010 | 1 | DOC011 | supported_application_logs | 4 | DOC013 -6.5409 | DOC006 -6.6091 | 0.0682 | DOC013;DOC006;DOC016;DOC011;DOC002 | 3300.0 | 3246.97 | 1 |
| A | CAL011 | 1 | DOC012 | supported_application_events | 1 | DOC012 0.6863 | DOC011 0.6652 | 0.0211 | DOC012;DOC011;DOC013;DOC016;DOC023 | 22.74 | 0.0 | 0 |
| B | CAL011 | 1 | DOC012 | supported_application_events | 1 | DOC012 0.0328 | DOC011 0.0318 | 0.001 | DOC012;DOC011;DOC023;DOC016;DOC009 | 26.54 | 0.0 | 0 |
| C | CAL011 | 1 | DOC012 | supported_application_events | 1 | DOC012 -4.3436 | DOC011 -5.8805 | 1.5369 | DOC012;DOC011;DOC002;DOC023;DOC015 | 2778.87 | 2756.13 | 1 |
| D | CAL011 | 1 | DOC012 | supported_application_events | 1 | DOC012 -4.3436 | DOC011 -5.8805 | 1.5369 | DOC012;DOC011;DOC002;DOC023;DOC015 | 3868.83 | 3842.28 | 1 |
| A | CAL012 | 1 | DOC013 | supported_service_keys | 1 | DOC013 0.7457 | DOC005 0.7014 | 0.0443 | DOC013;DOC005;DOC004;DOC006;DOC016 | 32.89 | 0.0 | 0 |
| B | CAL012 | 1 | DOC013 | supported_service_keys | 2 | DOC005 0.032 | DOC013 0.0311 | 0.001 | DOC005;DOC013;DOC016;DOC004;DOC018 | 36.73 | 0.0 | 0 |
| C | CAL012 | 1 | DOC013 | supported_service_keys | 1 | DOC013 -1.0674 | DOC005 -1.65 | 0.5826 | DOC013;DOC005;DOC016;DOC004;DOC010 | 2193.32 | 2160.43 | 1 |
| D | CAL012 | 1 | DOC013 | supported_service_keys | 1 | DOC013 -1.0674 | DOC005 -1.65 | 0.5826 | DOC013;DOC005;DOC016;DOC007;DOC004 | 3387.86 | 3351.13 | 1 |
| A | CAL013 | 1 | DOC014 | supported_space_quotas | 1 | DOC014 0.8341 | DOC009 0.7863 | 0.0478 | DOC014;DOC009;DOC020;DOC023;DOC019 | 32.01 | 0.0 | 0 |
| B | CAL013 | 1 | DOC014 | supported_space_quotas | 1 | DOC014 0.0325 | DOC009 0.0294 | 0.0031 | DOC014;DOC009;DOC020;DOC007;DOC006 | 35.59 | 0.0 | 0 |
| C | CAL013 | 1 | DOC014 | supported_space_quotas | 1 | DOC014 -2.0727 | DOC009 -3.4556 | 1.3829 | DOC014;DOC009;DOC020;DOC023;DOC002 | 1864.34 | 1832.34 | 1 |
| D | CAL013 | 1 | DOC014 | supported_space_quotas | 1 | DOC014 -2.0727 | DOC009 -3.4556 | 1.3829 | DOC014;DOC009;DOC020;DOC023;DOC002 | 2139.28 | 2103.69 | 1 |
| A | CAL014 | 1 | DOC015 | supported_security_groups | 1 | DOC015 0.7754 | DOC007 0.7304 | 0.045 | DOC015;DOC007;DOC016;DOC002;DOC005 | 70.57 | 0.0 | 0 |
| B | CAL014 | 1 | DOC015 | supported_security_groups | 1 | DOC015 0.0328 | DOC016 0.0298 | 0.003 | DOC015;DOC016;DOC002;DOC007;DOC005 | 74.96 | 0.0 | 0 |
| C | CAL014 | 1 | DOC015 | supported_security_groups | 1 | DOC015 -0.3269 | DOC022 -1.7334 | 1.4064 | DOC015;DOC022;DOC010;DOC001;DOC016 | 2920.34 | 2849.77 | 1 |
| D | CAL014 | 1 | DOC015 | supported_security_groups | 1 | DOC015 -0.3269 | DOC022 -1.7334 | 1.4064 | DOC015;DOC022;DOC013;DOC010;DOC001 | 2601.44 | 2526.48 | 1 |
| A | CAL015 | 1 | DOC016 | supported_routes_destinations | 1 | DOC016 0.7934 | DOC007 0.7522 | 0.0412 | DOC016;DOC007;DOC002;DOC019;DOC021 | 64.91 | 0.0 | 0 |
| B | CAL015 | 1 | DOC016 | supported_routes_destinations | 1 | DOC016 0.0328 | DOC007 0.0289 | 0.0039 | DOC016;DOC007;DOC013;DOC014;DOC022 | 71.69 | 0.0 | 0 |
| C | CAL015 | 1 | DOC016 | supported_routes_destinations | 1 | DOC016 0.0019 | DOC007 -5.3508 | 5.3527 | DOC016;DOC007;DOC002;DOC013;DOC005 | 2109.03 | 2044.13 | 1 |
| D | CAL015 | 1 | DOC016 | supported_routes_destinations | 1 | DOC016 0.0019 | DOC007 -5.3508 | 5.3527 | DOC016;DOC007;DOC013;DOC002;DOC005 | 3209.37 | 3137.67 | 1 |
| A | CAL016 | 1 | DOC017 | supported_platform_overview | 1 | DOC017 0.8305 | DOC022 0.7727 | 0.0578 | DOC017;DOC022;DOC018;DOC002;DOC003 | 73.31 | 0.0 | 0 |
| B | CAL016 | 1 | DOC017 | supported_platform_overview | 1 | DOC017 0.0328 | DOC018 0.0299 | 0.0029 | DOC017;DOC018;DOC002;DOC022;DOC003 | 78.14 | 0.0 | 0 |
| C | CAL016 | 1 | DOC017 | supported_platform_overview | 1 | DOC017 3.242 | DOC018 -0.2058 | 3.4478 | DOC017;DOC018;DOC002;DOC001;DOC023 | 1895.7 | 1822.39 | 1 |
| D | CAL016 | 1 | DOC017 | supported_platform_overview | 1 | DOC017 3.242 | DOC018 -0.2058 | 3.4478 | DOC017;DOC018;DOC002;DOC001;DOC023 | 2906.88 | 2828.74 | 1 |
| A | CAL017 | 1 | DOC018 | supported_basic_concepts | 1 | DOC018 0.867 | DOC019 0.8348 | 0.0323 | DOC018;DOC019;DOC020;DOC021;DOC017 | 78.1 | 0.0 | 0 |
| B | CAL017 | 1 | DOC018 | supported_basic_concepts | 1 | DOC018 0.0325 | DOC020 0.0295 | 0.0031 | DOC018;DOC020;DOC019;DOC021;DOC014 | 81.61 | 0.0 | 0 |
| C | CAL017 | 1 | DOC018 | supported_basic_concepts | 3 | DOC020 3.2953 | DOC019 2.5425 | 0.7528 | DOC020;DOC019;DOC018;DOC021;DOC022 | 2732.56 | 2654.46 | 1 |
| D | CAL017 | 1 | DOC018 | supported_basic_concepts | 3 | DOC020 3.2953 | DOC019 2.5425 | 0.7528 | DOC020;DOC019;DOC018;DOC021;DOC022 | 2427.95 | 2346.34 | 1 |
| A | CAL018 | 1 | DOC019 | supported_account_model | 1 | DOC019 0.8162 | DOC018 0.7961 | 0.0201 | DOC019;DOC018;DOC020;DOC021;DOC023 | 24.97 | 0.0 | 0 |
| B | CAL018 | 1 | DOC019 | supported_account_model | 2 | DOC018 0.0323 | DOC019 0.0311 | 0.0012 | DOC018;DOC019;DOC020;DOC022;DOC021 | 28.7 | 0.0 | 0 |
| C | CAL018 | 1 | DOC019 | supported_account_model | 2 | DOC018 2.4821 | DOC019 1.632 | 0.8502 | DOC018;DOC019;DOC022;DOC020;DOC021 | 1922.68 | 1897.71 | 1 |
| D | CAL018 | 1 | DOC019 | supported_account_model | 2 | DOC018 2.4821 | DOC019 1.632 | 0.8502 | DOC018;DOC019;DOC022;DOC020;DOC021 | 2847.87 | 2819.17 | 1 |
| A | CAL019 | 1 | DOC020 | supported_entitlements_quotas | 1 | DOC020 0.7516 | DOC005 0.7393 | 0.0123 | DOC020;DOC005;DOC009;DOC014;DOC019 | 52.16 | 0.0 | 0 |
| B | CAL019 | 1 | DOC020 | supported_entitlements_quotas | 3 | DOC014 0.0313 | DOC009 0.031 | 0.0003 | DOC014;DOC009;DOC020;DOC005;DOC018 | 55.96 | 0.0 | 0 |
| C | CAL019 | 1 | DOC020 | supported_entitlements_quotas | 2 | DOC018 -1.0724 | DOC020 -1.6837 | 0.6113 | DOC018;DOC020;DOC019;DOC009;DOC021 | 1859.06 | 1806.9 | 1 |
| D | CAL019 | 1 | DOC020 | supported_entitlements_quotas | 2 | DOC018 -1.0724 | DOC020 -1.6837 | 0.6113 | DOC018;DOC020;DOC019;DOC009;DOC021 | 2362.35 | 2306.4 | 1 |
| A | CAL020 | 1 | DOC021 | supported_regions | 2 | DOC019 0.8532 | DOC021 0.8117 | 0.0415 | DOC019;DOC021;DOC018;DOC022;DOC020 | 63.07 | 0.0 | 0 |
| B | CAL020 | 1 | DOC021 | supported_regions | 1 | DOC021 0.0325 | DOC019 0.032 | 0.0005 | DOC021;DOC019;DOC018;DOC023;DOC017 | 67.05 | 0.0 | 0 |
| C | CAL020 | 1 | DOC021 | supported_regions | 1 | DOC021 2.1917 | DOC019 2.1413 | 0.0504 | DOC021;DOC019;DOC018;DOC017;DOC022 | 2711.12 | 2648.05 | 1 |
| D | CAL020 | 1 | DOC021 | supported_regions | 1 | DOC021 2.1917 | DOC019 2.1413 | 0.0504 | DOC021;DOC019;DOC018;DOC017;DOC022 | 2560.01 | 2492.96 | 1 |
| A | CAL021 | 1 | DOC022 | supported_tools | 1 | DOC022 0.8307 | DOC003 0.7826 | 0.0481 | DOC022;DOC003;DOC018;DOC017;DOC006 | 22.48 | 0.0 | 0 |
| B | CAL021 | 1 | DOC022 | supported_tools | 1 | DOC022 0.0323 | DOC003 0.0317 | 0.0005 | DOC022;DOC003;DOC002;DOC006;DOC017 | 26.63 | 0.0 | 0 |
| C | CAL021 | 1 | DOC022 | supported_tools | 1 | DOC022 2.2264 | DOC006 1.3753 | 0.8511 | DOC022;DOC006;DOC002;DOC023;DOC005 | 1675.4 | 1652.92 | 1 |
| D | CAL021 | 1 | DOC022 | supported_tools | 1 | DOC022 2.2264 | DOC006 1.3753 | 0.8511 | DOC022;DOC006;DOC002;DOC023;DOC005 | 2956.73 | 2930.11 | 1 |
| A | CAL022 | 1 | DOC023 | supported_trial_free_tier | 1 | DOC023 0.8705 | DOC024 0.8365 | 0.034 | DOC023;DOC024;DOC018;DOC020;DOC022 | 93.91 | 0.0 | 0 |
| B | CAL022 | 1 | DOC023 | supported_trial_free_tier | 1 | DOC023 0.0328 | DOC024 0.0308 | 0.002 | DOC023;DOC024;DOC018;DOC019;DOC020 | 97.32 | 0.0 | 0 |
| C | CAL022 | 1 | DOC023 | supported_trial_free_tier | 1 | DOC023 5.9757 | DOC024 4.8426 | 1.1331 | DOC023;DOC024;DOC018;DOC017;DOC002 | 1862.32 | 1768.41 | 1 |
| D | CAL022 | 1 | DOC023 | supported_trial_free_tier | 1 | DOC023 5.9757 | DOC024 4.8426 | 1.1331 | DOC023;DOC024;DOC018;DOC017;DOC002 | 2579.14 | 2481.82 | 1 |
| A | CAL023 | 1 | DOC024 | supported_getting_started | 1 | DOC024 0.806 | DOC017 0.7663 | 0.0396 | DOC024;DOC017;DOC002;DOC022;DOC018 | 21.42 | 0.0 | 0 |
| B | CAL023 | 1 | DOC024 | supported_getting_started | 1 | DOC024 0.0318 | DOC017 0.0305 | 0.0013 | DOC024;DOC017;DOC005;DOC023;DOC018 | 25.4 | 0.0 | 0 |
| C | CAL023 | 1 | DOC024 | supported_getting_started | 1 | DOC024 -0.0181 | DOC017 -1.8017 | 1.7836 | DOC024;DOC017;DOC018;DOC002;DOC006 | 2499.21 | 2477.79 | 1 |
| D | CAL023 | 1 | DOC024 | supported_getting_started | 1 | DOC024 -0.0181 | DOC001 -1.6087 | 1.5906 | DOC024;DOC001;DOC017;DOC018;DOC002 | 2504.13 | 2478.73 | 1 |
| A | CAL024 | 1 | DOC004 | supported_services_confusable | 3 | DOC005 0.8066 | DOC007 0.7144 | 0.0921 | DOC005;DOC007;DOC004;DOC013;DOC018 | 66.92 | 0.0 | 0 |
| B | CAL024 | 1 | DOC004 | supported_services_confusable | 3 | DOC005 0.0328 | DOC016 0.03 | 0.0028 | DOC005;DOC016;DOC004;DOC013;DOC020 | 71.09 | 0.0 | 0 |
| C | CAL024 | 1 | DOC004 | supported_services_confusable | 3 | DOC005 -2.1605 | DOC013 -4.4475 | 2.287 | DOC005;DOC013;DOC004;DOC018;DOC010 | 2309.52 | 2242.6 | 1 |
| D | CAL024 | 1 | DOC004 | supported_services_confusable | 3 | DOC005 -2.1605 | DOC013 -4.4475 | 2.287 | DOC005;DOC013;DOC004;DOC018;DOC010 | 2674.61 | 2603.52 | 1 |
| A | CAL025 | 1 | DOC005 | supported_service_bindings_confusable | 2 | DOC013 0.7411 | DOC005 0.7175 | 0.0235 | DOC013;DOC005;DOC004;DOC016;DOC007 | 38.03 | 0.0 | 0 |
| B | CAL025 | 1 | DOC005 | supported_service_bindings_confusable | 1 | DOC005 0.0325 | DOC013 0.0309 | 0.0016 | DOC005;DOC013;DOC016;DOC004;DOC007 | 41.54 | 0.0 | 0 |
| C | CAL025 | 1 | DOC005 | supported_service_bindings_confusable | 2 | DOC013 -1.8062 | DOC005 -1.9912 | 0.1849 | DOC013;DOC005;DOC004;DOC007;DOC016 | 3017.77 | 2979.74 | 1 |
| D | CAL025 | 1 | DOC005 | supported_service_bindings_confusable | 2 | DOC013 -1.8062 | DOC005 -1.9912 | 0.1849 | DOC013;DOC005;DOC004;DOC007;DOC016 | 3551.65 | 3510.11 | 1 |
| A | CAL026 | 1 | DOC013 | supported_service_keys_confusable | 2 | DOC005 0.7018 | DOC013 0.6905 | 0.0113 | DOC005;DOC013;DOC004;DOC016;DOC010 | 72.47 | 0.0 | 0 |
| B | CAL026 | 1 | DOC013 | supported_service_keys_confusable | 2 | DOC005 0.0325 | DOC013 0.0306 | 0.002 | DOC005;DOC013;DOC003;DOC016;DOC004 | 76.56 | 0.0 | 0 |
| C | CAL026 | 1 | DOC013 | supported_service_keys_confusable | 2 | DOC005 -4.395 | DOC013 -5.6374 | 1.2424 | DOC005;DOC013;DOC010;DOC016;DOC004 | 2512.31 | 2439.83 | 1 |
| D | CAL026 | 1 | DOC013 | supported_service_keys_confusable | 2 | DOC005 -4.395 | DOC013 -5.6374 | 1.2424 | DOC005;DOC013;DOC010;DOC007;DOC016 | 2556.26 | 2479.7 | 1 |
| A | CAL027 | 1 | DOC007 | supported_routes_confusable | 1 | DOC007 0.7955 | DOC016 0.7425 | 0.053 | DOC007;DOC016;DOC015;DOC021;DOC005 | 23.2 | 0.0 | 0 |
| B | CAL027 | 1 | DOC007 | supported_routes_confusable | 1 | DOC007 0.0325 | DOC016 0.0306 | 0.0019 | DOC007;DOC016;DOC015;DOC019;DOC014 | 26.63 | 0.0 | 0 |
| C | CAL027 | 1 | DOC007 | supported_routes_confusable | 1 | DOC007 -4.2001 | DOC015 -6.1927 | 1.9926 | DOC007;DOC015;DOC016;DOC019;DOC021 | 2056.89 | 2033.68 | 1 |
| D | CAL027 | 1 | DOC007 | supported_routes_confusable | 1 | DOC007 -4.2001 | DOC015 -6.1927 | 1.9926 | DOC007;DOC015;DOC016;DOC019;DOC021 | 3113.02 | 3086.39 | 1 |
| A | CAL028 | 1 | DOC016 | supported_routes_destinations_confusable | 1 | DOC016 0.7673 | DOC007 0.7084 | 0.0589 | DOC016;DOC007;DOC015;DOC019;DOC021 | 31.71 | 0.0 | 0 |
| B | CAL028 | 1 | DOC016 | supported_routes_destinations_confusable | 1 | DOC016 0.0328 | DOC007 0.0272 | 0.0056 | DOC016;DOC007;DOC013;DOC019;DOC014 | 35.41 | 0.0 | 0 |
| C | CAL028 | 1 | DOC016 | supported_routes_destinations_confusable | 1 | DOC016 0.4969 | DOC007 -6.9055 | 7.4024 | DOC016;DOC007;DOC013;DOC015;DOC021 | 2597.72 | 2566.01 | 1 |
| D | CAL028 | 1 | DOC016 | supported_routes_destinations_confusable | 1 | DOC016 0.4969 | DOC007 -6.9055 | 7.4024 | DOC016;DOC007;DOC013;DOC015;DOC020 | 3533.7 | 3498.29 | 1 |
| A | CAL029 | 1 | DOC011 | supported_monitoring_confusable | 2 | DOC012 0.6653 | DOC011 0.6607 | 0.0047 | DOC012;DOC011;DOC015;DOC016;DOC005 | 66.49 | 0.0 | 0 |
| B | CAL029 | 1 | DOC011 | supported_monitoring_confusable | 2 | DOC012 0.0328 | DOC011 0.0323 | 0.0005 | DOC012;DOC011;DOC023;DOC005;DOC017 | 70.19 | 0.0 | 0 |
| C | CAL029 | 1 | DOC011 | supported_monitoring_confusable | 1 | DOC011 -5.9812 | DOC012 -7.5219 | 1.5407 | DOC011;DOC012;DOC005;DOC016;DOC022 | 2174.24 | 2107.74 | 1 |
| D | CAL029 | 1 | DOC011 | supported_monitoring_confusable | 1 | DOC011 -5.9812 | DOC012 -7.5219 | 1.5407 | DOC011;DOC012;DOC005;DOC016;DOC022 | 3147.96 | 3077.77 | 1 |
| A | CAL030 | 1 | DOC012 | supported_monitoring_confusable | 1 | DOC012 0.7488 | DOC011 0.6718 | 0.077 | DOC012;DOC011;DOC015;DOC013;DOC016 | 78.41 | 0.0 | 0 |
| B | CAL030 | 1 | DOC012 | supported_monitoring_confusable | 1 | DOC012 0.0328 | DOC011 0.0323 | 0.0005 | DOC012;DOC011;DOC018;DOC016;DOC017 | 82.4 | 0.0 | 0 |
| C | CAL030 | 1 | DOC012 | supported_monitoring_confusable | 1 | DOC012 -0.2203 | DOC011 -5.4723 | 5.252 | DOC012;DOC011;DOC018;DOC013;DOC015 | 2399.7 | 2321.28 | 1 |
| D | CAL030 | 1 | DOC012 | supported_monitoring_confusable | 1 | DOC012 -0.2203 | DOC011 -5.4723 | 5.252 | DOC012;DOC011;DOC018;DOC013;DOC015 | 3094.57 | 3012.17 | 1 |
| A | CAL031 | 1 | DOC009 | supported_account_quota_confusable | 12 | DOC002 0.7694 | DOC004 0.7506 | 0.0188 | DOC002;DOC004;DOC003;DOC020;DOC007 | 79.28 | 0.0 | 0 |
| B | CAL031 | 1 | DOC009 | supported_account_quota_confusable | 11 | DOC002 0.0296 | DOC020 0.0293 | 0.0004 | DOC002;DOC020;DOC019;DOC007;DOC022 | 83.29 | 0.0 | 0 |
| C | CAL031 | 1 | DOC009 | supported_account_quota_confusable | 7 | DOC002 -1.4083 | DOC019 -3.5873 | 2.179 | DOC002;DOC019;DOC022;DOC001;DOC018 | 2543.48 | 2464.2 | 1 |
| D | CAL031 | 1 | DOC009 | supported_account_quota_confusable | 7 | DOC002 -1.4083 | DOC019 -3.5873 | 2.179 | DOC002;DOC019;DOC014;DOC013;DOC022 | 3223.0 | 3139.71 | 1 |
| A | CAL032 | 1 | DOC014 | supported_account_quota_confusable | 6 | DOC020 0.8674 | DOC018 0.8311 | 0.0363 | DOC020;DOC018;DOC019;DOC009;DOC021 | 25.02 | 0.0 | 0 |
| B | CAL032 | 1 | DOC014 | supported_account_quota_confusable | 2 | DOC020 0.0308 | DOC014 0.0291 | 0.0018 | DOC020;DOC014;DOC018;DOC009;DOC019 | 28.99 | 0.0 | 0 |
| C | CAL032 | 1 | DOC014 | supported_account_quota_confusable | 5 | DOC020 2.5281 | DOC018 0.9454 | 1.5827 | DOC020;DOC018;DOC009;DOC019;DOC014 | 1886.02 | 1861.01 | 1 |
| D | CAL032 | 1 | DOC014 | supported_account_quota_confusable | 5 | DOC020 2.5281 | DOC018 0.9454 | 1.5827 | DOC020;DOC018;DOC009;DOC019;DOC014 | 2708.07 | 2679.07 | 1 |
| A | CAL033 | 0 | - | unsupported_near_domain | 0 | DOC006 0.686 | DOC005 0.6808 | 0.0052 | DOC006;DOC005;DOC003;DOC002;DOC022 | 31.48 | 0.0 | - |
| B | CAL033 | 0 | - | unsupported_near_domain | 0 | DOC022 0.0291 | DOC002 0.0287 | 0.0004 | DOC022;DOC002;DOC006;DOC005;DOC004 | 35.05 | 0.0 | - |
| C | CAL033 | 0 | - | unsupported_near_domain | 0 | DOC006 -5.3268 | DOC007 -6.0481 | 0.7213 | DOC006;DOC007;DOC005;DOC022;DOC002 | 2361.07 | 2329.59 | - |
| D | CAL033 | 0 | - | unsupported_near_domain | 0 | DOC018 -4.2941 | DOC006 -5.3268 | 1.0327 | DOC018;DOC006;DOC007;DOC005;DOC022 | 2323.62 | 2288.57 | - |
| A | CAL034 | 0 | - | unsupported_near_domain | 0 | DOC017 0.7316 | DOC022 0.7067 | 0.0249 | DOC017;DOC022;DOC003;DOC018;DOC002 | 23.46 | 0.0 | - |
| B | CAL034 | 0 | - | unsupported_near_domain | 0 | DOC017 0.0323 | DOC022 0.0295 | 0.0028 | DOC017;DOC022;DOC018;DOC003;DOC016 | 27.31 | 0.0 | - |
| C | CAL034 | 0 | - | unsupported_near_domain | 0 | DOC017 -5.0523 | DOC016 -7.8734 | 2.8211 | DOC017;DOC016;DOC002;DOC022;DOC003 | 2288.08 | 2264.62 | - |
| D | CAL034 | 0 | - | unsupported_near_domain | 0 | DOC017 -5.0523 | DOC016 -7.8734 | 2.8211 | DOC017;DOC016;DOC002;DOC022;DOC021 | 3244.26 | 3216.94 | - |
| A | CAL035 | 0 | - | unsupported_near_domain | 0 | DOC002 0.6409 | DOC017 0.64 | 0.0009 | DOC002;DOC017;DOC022;DOC019;DOC013 | 20.7 | 0.0 | - |
| B | CAL035 | 0 | - | unsupported_near_domain | 0 | DOC002 0.0325 | DOC022 0.0323 | 0.0003 | DOC002;DOC022;DOC017;DOC020;DOC019 | 24.4 | 0.0 | - |
| C | CAL035 | 0 | - | unsupported_near_domain | 0 | DOC002 -6.6636 | DOC013 -6.7709 | 0.1073 | DOC002;DOC013;DOC022;DOC005;DOC020 | 2082.79 | 2062.09 | - |
| D | CAL035 | 0 | - | unsupported_near_domain | 0 | DOC002 -6.6636 | DOC013 -6.7709 | 0.1073 | DOC002;DOC013;DOC022;DOC019;DOC005 | 2409.48 | 2385.08 | - |
| A | CAL036 | 0 | - | unsupported_near_domain | 0 | DOC022 0.7388 | DOC006 0.691 | 0.0478 | DOC022;DOC006;DOC002;DOC021;DOC018 | 23.92 | 0.0 | - |
| B | CAL036 | 0 | - | unsupported_near_domain | 0 | DOC022 0.0325 | DOC006 0.0308 | 0.0017 | DOC022;DOC006;DOC021;DOC018;DOC017 | 27.99 | 0.0 | - |
| C | CAL036 | 0 | - | unsupported_near_domain | 0 | DOC022 -2.8081 | DOC006 -3.8391 | 1.031 | DOC022;DOC006;DOC005;DOC023;DOC001 | 1483.98 | 1460.06 | - |
| D | CAL036 | 0 | - | unsupported_near_domain | 0 | DOC022 -2.8081 | DOC006 -3.8391 | 1.031 | DOC022;DOC006;DOC007;DOC005;DOC023 | 2211.0 | 2183.02 | - |
| A | CAL037 | 0 | - | unsupported_near_domain | 0 | DOC003 0.7286 | DOC002 0.7167 | 0.0119 | DOC003;DOC002;DOC016;DOC001;DOC017 | 26.68 | 0.0 | - |
| B | CAL037 | 0 | - | unsupported_near_domain | 0 | DOC016 0.0318 | DOC004 0.0304 | 0.0014 | DOC016;DOC004;DOC002;DOC022;DOC003 | 30.32 | 0.0 | - |
| C | CAL037 | 0 | - | unsupported_near_domain | 0 | DOC016 1.7113 | DOC022 -5.7119 | 7.4232 | DOC016;DOC022;DOC006;DOC007;DOC005 | 1776.73 | 1750.06 | - |
| D | CAL037 | 0 | - | unsupported_near_domain | 0 | DOC016 1.7113 | DOC022 -5.7119 | 7.4232 | DOC016;DOC022;DOC006;DOC023;DOC007 | 2479.81 | 2449.5 | - |
| A | CAL038 | 0 | - | unsupported_near_domain | 0 | DOC020 0.7086 | DOC023 0.7037 | 0.0049 | DOC020;DOC023;DOC018;DOC014;DOC019 | 60.36 | 0.0 | - |
| B | CAL038 | 0 | - | unsupported_near_domain | 0 | DOC020 0.0325 | DOC014 0.0297 | 0.0028 | DOC020;DOC014;DOC018;DOC004;DOC009 | 63.39 | 0.0 | - |
| C | CAL038 | 0 | - | unsupported_near_domain | 0 | DOC004 -6.306 | DOC018 -7.8297 | 1.5237 | DOC004;DOC018;DOC020;DOC014;DOC019 | 1885.64 | 1825.28 | - |
| D | CAL038 | 0 | - | unsupported_near_domain | 0 | DOC004 -6.306 | DOC018 -7.8297 | 1.5237 | DOC004;DOC018;DOC020;DOC014;DOC009 | 2240.04 | 2176.64 | - |
| A | CAL039 | 0 | - | unsupported_near_domain | 0 | DOC005 0.6225 | DOC016 0.6202 | 0.0023 | DOC005;DOC016;DOC007;DOC021;DOC002 | 27.7 | 0.0 | - |
| B | CAL039 | 0 | - | unsupported_near_domain | 0 | DOC012 0.0308 | DOC005 0.0283 | 0.0025 | DOC012;DOC005;DOC002;DOC021;DOC016 | 31.45 | 0.0 | - |
| C | CAL039 | 0 | - | unsupported_near_domain | 0 | DOC005 -5.4238 | DOC015 -7.4347 | 2.0109 | DOC005;DOC015;DOC016;DOC013;DOC007 | 1576.5 | 1548.81 | - |
| D | CAL039 | 0 | - | unsupported_near_domain | 0 | DOC005 -5.4238 | DOC019 -7.2469 | 1.8232 | DOC005;DOC019;DOC018;DOC015;DOC013 | 3345.73 | 3314.28 | - |
| A | CAL040 | 0 | - | unsupported_near_domain | 0 | DOC019 0.7341 | DOC022 0.7298 | 0.0043 | DOC019;DOC022;DOC018;DOC005;DOC013 | 22.29 | 0.0 | - |
| B | CAL040 | 0 | - | unsupported_near_domain | 0 | DOC022 0.032 | DOC019 0.031 | 0.001 | DOC022;DOC019;DOC018;DOC005;DOC013 | 25.19 | 0.0 | - |
| C | CAL040 | 0 | - | unsupported_near_domain | 0 | DOC002 -3.985 | DOC019 -4.0219 | 0.0368 | DOC002;DOC019;DOC018;DOC022;DOC023 | 1555.84 | 1533.55 | - |
| D | CAL040 | 0 | - | unsupported_near_domain | 0 | DOC002 -3.985 | DOC019 -4.0219 | 0.0368 | DOC002;DOC019;DOC018;DOC022;DOC023 | 2545.91 | 2520.72 | - |
| A | CAL041 | 0 | - | unsupported_out_of_scope | 0 | DOC005 0.4892 | DOC002 0.4726 | 0.0165 | DOC005;DOC002;DOC009;DOC007;DOC011 | 48.85 | 0.0 | - |
| B | CAL041 | 0 | - | unsupported_out_of_scope | 0 | DOC002 0.0278 | DOC017 0.0258 | 0.002 | DOC002;DOC017;DOC009;DOC014;DOC015 | 52.2 | 0.0 | - |
| C | CAL041 | 0 | - | unsupported_out_of_scope | 0 | DOC003 -10.1919 | DOC006 -10.1922 | 0.0003 | DOC003;DOC006;DOC018;DOC020;DOC005 | 2332.73 | 2283.88 | - |
| D | CAL041 | 0 | - | unsupported_out_of_scope | 0 | DOC003 -10.1919 | DOC016 -10.1922 | 0.0003 | DOC003;DOC016;DOC018;DOC006;DOC020 | 3627.25 | 3575.05 | - |
| A | CAL042 | 0 | - | unsupported_out_of_scope | 0 | DOC017 0.5096 | DOC015 0.4687 | 0.0409 | DOC017;DOC015;DOC022;DOC005;DOC013 | 61.8 | 0.0 | - |
| B | CAL042 | 0 | - | unsupported_out_of_scope | 0 | DOC022 0.0313 | DOC013 0.0289 | 0.0024 | DOC022;DOC013;DOC015;DOC021;DOC003 | 64.87 | 0.0 | - |
| C | CAL042 | 0 | - | unsupported_out_of_scope | 0 | DOC005 -8.1744 | DOC013 -9.0485 | 0.874 | DOC005;DOC013;DOC010;DOC015;DOC020 | 2641.4 | 2579.59 | - |
| D | CAL042 | 0 | - | unsupported_out_of_scope | 0 | DOC005 -8.0941 | DOC013 -9.0485 | 0.9543 | DOC005;DOC013;DOC010;DOC019;DOC009 | 3819.62 | 3754.76 | - |
| A | CAL043 | 0 | - | unsupported_out_of_scope | 0 | DOC016 0.538 | DOC020 0.5124 | 0.0256 | DOC016;DOC020;DOC007;DOC023;DOC019 | 29.21 | 0.0 | - |
| B | CAL043 | 0 | - | unsupported_out_of_scope | 0 | DOC020 0.0296 | DOC016 0.0282 | 0.0015 | DOC020;DOC016;DOC023;DOC018;DOC009 | 32.71 | 0.0 | - |
| C | CAL043 | 0 | - | unsupported_out_of_scope | 0 | DOC016 -7.663 | DOC021 -9.4016 | 1.7386 | DOC016;DOC021;DOC020;DOC018;DOC019 | 1608.63 | 1579.42 | - |
| D | CAL043 | 0 | - | unsupported_out_of_scope | 0 | DOC016 -7.663 | DOC021 -9.4016 | 1.7386 | DOC016;DOC021;DOC020;DOC018;DOC005 | 3874.76 | 3842.05 | - |
| A | CAL044 | 0 | - | unsupported_out_of_scope | 0 | DOC012 0.4895 | DOC009 0.4568 | 0.0327 | DOC012;DOC009;DOC015;DOC019;DOC010 | 25.82 | 0.0 | - |
| B | CAL044 | 0 | - | unsupported_out_of_scope | 0 | DOC015 0.0313 | DOC023 0.0282 | 0.0031 | DOC015;DOC023;DOC005;DOC020;DOC002 | 29.4 | 0.0 | - |
| C | CAL044 | 0 | - | unsupported_out_of_scope | 0 | DOC005 -7.9647 | DOC007 -8.9651 | 1.0003 | DOC005;DOC007;DOC015;DOC009;DOC019 | 1488.16 | 1462.34 | - |
| D | CAL044 | 0 | - | unsupported_out_of_scope | 0 | DOC005 -7.9647 | DOC016 -8.6532 | 0.6884 | DOC005;DOC016;DOC007;DOC021;DOC015 | 2332.33 | 2302.92 | - |
| A | CAL045 | 0 | - | unsupported_out_of_scope | 0 | DOC023 0.5071 | DOC024 0.4828 | 0.0243 | DOC023;DOC024;DOC020;DOC019;DOC014 | 20.46 | 0.0 | - |
| B | CAL045 | 0 | - | unsupported_out_of_scope | 0 | DOC014 0.0296 | DOC020 0.0292 | 0.0004 | DOC014;DOC020;DOC024;DOC002;DOC009 | 23.83 | 0.0 | - |
| C | CAL045 | 0 | - | unsupported_out_of_scope | 0 | DOC023 -9.555 | DOC012 -10.1895 | 0.6345 | DOC023;DOC012;DOC009;DOC014;DOC019 | 1676.0 | 1655.54 | - |
| D | CAL045 | 0 | - | unsupported_out_of_scope | 0 | DOC023 -9.555 | DOC012 -10.1895 | 0.6345 | DOC023;DOC012;DOC009;DOC017;DOC019 | 3705.63 | 3681.8 | - |
| A | CAL046 | 0 | - | unsupported_out_of_scope | 0 | DOC019 0.5547 | DOC020 0.551 | 0.0038 | DOC019;DOC020;DOC018;DOC023;DOC021 | 83.67 | 0.0 | - |
| B | CAL046 | 0 | - | unsupported_out_of_scope | 0 | DOC020 0.0298 | DOC019 0.0286 | 0.0012 | DOC020;DOC019;DOC018;DOC014;DOC013 | 86.88 | 0.0 | - |
| C | CAL046 | 0 | - | unsupported_out_of_scope | 0 | DOC020 -8.2965 | DOC018 -9.8117 | 1.5152 | DOC020;DOC018;DOC019;DOC023;DOC016 | 1918.04 | 1834.37 | - |
| D | CAL046 | 0 | - | unsupported_out_of_scope | 0 | DOC020 -8.2965 | DOC018 -9.8117 | 1.5152 | DOC020;DOC018;DOC019;DOC023;DOC016 | 3429.32 | 3342.44 | - |
| A | CAL047 | 0 | - | unsupported_out_of_scope | 0 | DOC023 0.4652 | DOC021 0.4625 | 0.0027 | DOC023;DOC021;DOC015;DOC017;DOC019 | 26.23 | 0.0 | - |
| B | CAL047 | 0 | - | unsupported_out_of_scope | 0 | DOC020 0.0313 | DOC009 0.0296 | 0.0016 | DOC020;DOC009;DOC015;DOC021;DOC013 | 29.36 | 0.0 | - |
| C | CAL047 | 0 | - | unsupported_out_of_scope | 0 | DOC016 -10.1924 | DOC022 -10.1924 | 0.0 | DOC016;DOC022;DOC004;DOC020;DOC013 | 1579.2 | 1552.96 | - |
| D | CAL047 | 0 | - | unsupported_out_of_scope | 0 | DOC003 -10.192 | DOC016 -10.1923 | 0.0003 | DOC003;DOC016;DOC005;DOC022;DOC004 | 2473.19 | 2443.83 | - |
| A | CAL048 | 0 | - | unsupported_out_of_scope | 0 | DOC006 0.5434 | DOC003 0.5271 | 0.0162 | DOC006;DOC003;DOC002;DOC015;DOC009 | 26.43 | 0.0 | - |
| B | CAL048 | 0 | - | unsupported_out_of_scope | 0 | DOC009 0.0303 | DOC006 0.0274 | 0.0029 | DOC009;DOC006;DOC016;DOC023;DOC010 | 29.65 | 0.0 | - |
| C | CAL048 | 0 | - | unsupported_out_of_scope | 0 | DOC009 -9.1678 | DOC003 -9.4452 | 0.2775 | DOC009;DOC003;DOC006;DOC015;DOC016 | 2233.29 | 2206.87 | - |
| D | CAL048 | 0 | - | unsupported_out_of_scope | 0 | DOC009 -9.1678 | DOC003 -9.4452 | 0.2775 | DOC009;DOC003;DOC016;DOC006;DOC015 | 3886.71 | 3857.06 | - |

## Supported Candidate Pool Details

| Variant | Query | Expected document | Present | Candidate pool documents |
|---|---|---|---:|---|
| C | CAL001 | DOC001 | 1 | DOC002;DOC022;DOC001;DOC018;DOC003;DOC004;DOC005;DOC006;DOC021;DOC020;DOC017;DOC024;DOC011;DOC016;DOC023;DOC010;DOC015 |
| D | CAL001 | DOC001 | 1 | DOC002;DOC022;DOC001;DOC018;DOC003;DOC004;DOC021;DOC005;DOC016;DOC010;DOC024;DOC006;DOC011;DOC017;DOC015;DOC023;DOC020;DOC013;DOC009;DOC019;DOC014 |
| C | CAL002 | DOC002 | 1 | DOC002;DOC003;DOC005;DOC004;DOC006;DOC001;DOC007;DOC022;DOC018;DOC009;DOC021;DOC019;DOC010;DOC016;DOC011;DOC024;DOC020;DOC013;DOC017;DOC015;DOC023 |
| D | CAL002 | DOC002 | 1 | DOC003;DOC002;DOC005;DOC018;DOC022;DOC006;DOC001;DOC017;DOC011;DOC007;DOC015;DOC010;DOC024;DOC013;DOC021;DOC004;DOC009;DOC023;DOC014;DOC019;DOC020;DOC016;DOC012 |
| C | CAL003 | DOC003 | 1 | DOC003;DOC002;DOC001;DOC005;DOC004;DOC022;DOC018;DOC006;DOC021;DOC024;DOC020;DOC011;DOC017;DOC016;DOC015;DOC010;DOC023;DOC012 |
| D | CAL003 | DOC003 | 1 | DOC003;DOC002;DOC005;DOC006;DOC001;DOC022;DOC012;DOC021;DOC018;DOC017;DOC024;DOC011;DOC015;DOC013;DOC004;DOC014;DOC009;DOC016;DOC023;DOC010;DOC020 |
| C | CAL004 | DOC004 | 1 | DOC005;DOC004;DOC013;DOC016;DOC007;DOC002;DOC006;DOC022;DOC023;DOC010;DOC018;DOC021;DOC001;DOC017;DOC009;DOC019;DOC003;DOC012 |
| D | CAL004 | DOC004 | 1 | DOC013;DOC005;DOC004;DOC002;DOC001;DOC016;DOC018;DOC006;DOC009;DOC007;DOC003;DOC023;DOC020;DOC022;DOC010;DOC017;DOC021;DOC019;DOC014;DOC012 |
| C | CAL005 | DOC005 | 1 | DOC005;DOC004;DOC013;DOC006;DOC016;DOC007;DOC015;DOC002;DOC021;DOC020;DOC017;DOC023;DOC009;DOC014;DOC003;DOC019;DOC022;DOC024;DOC018 |
| D | CAL005 | DOC005 | 1 | DOC005;DOC013;DOC007;DOC016;DOC004;DOC020;DOC023;DOC015;DOC014;DOC018;DOC006;DOC009;DOC019;DOC002;DOC012;DOC021;DOC017;DOC003;DOC022;DOC024 |
| C | CAL006 | DOC006 | 1 | DOC021;DOC010;DOC007;DOC002;DOC004;DOC016;DOC005;DOC006;DOC001;DOC013;DOC022;DOC009;DOC003;DOC018;DOC011;DOC019;DOC015;DOC020;DOC023 |
| D | CAL006 | DOC006 | 1 | DOC021;DOC006;DOC013;DOC002;DOC016;DOC010;DOC001;DOC005;DOC011;DOC003;DOC018;DOC023;DOC022;DOC015;DOC019;DOC007;DOC004;DOC020;DOC012;DOC014;DOC009;DOC017 |
| C | CAL007 | DOC007 | 1 | DOC016;DOC007;DOC015;DOC021;DOC005;DOC002;DOC006;DOC009;DOC014;DOC013;DOC023;DOC019;DOC003;DOC004;DOC020 |
| D | CAL007 | DOC007 | 1 | DOC016;DOC007;DOC015;DOC021;DOC005;DOC013;DOC014;DOC006;DOC009;DOC010;DOC018;DOC002;DOC017;DOC022;DOC023;DOC020;DOC019;DOC003;DOC004;DOC011;DOC012 |
| C | CAL008 | DOC009 | 1 | DOC002;DOC019;DOC009;DOC007;DOC010;DOC004;DOC003;DOC006;DOC005;DOC001;DOC020;DOC015;DOC021;DOC018;DOC022;DOC016;DOC023;DOC014 |
| D | CAL008 | DOC009 | 1 | DOC009;DOC002;DOC019;DOC003;DOC010;DOC004;DOC020;DOC015;DOC021;DOC014;DOC001;DOC018;DOC022;DOC016;DOC007;DOC006;DOC005;DOC013;DOC023;DOC017;DOC024;DOC011 |
| C | CAL009 | DOC010 | 1 | DOC002;DOC010;DOC004;DOC005;DOC007;DOC001;DOC003;DOC006;DOC015;DOC021;DOC018;DOC009;DOC019;DOC022;DOC023;DOC016;DOC020;DOC012;DOC013;DOC011 |
| D | CAL009 | DOC010 | 1 | DOC010;DOC007;DOC005;DOC006;DOC001;DOC019;DOC018;DOC002;DOC009;DOC012;DOC020;DOC011;DOC023;DOC015;DOC013;DOC004;DOC014;DOC003;DOC021;DOC022;DOC016;DOC024;DOC017 |
| C | CAL010 | DOC011 | 1 | DOC011;DOC012;DOC022;DOC002;DOC023;DOC021;DOC015;DOC009;DOC016;DOC006;DOC005;DOC014;DOC018;DOC024;DOC004;DOC017;DOC001;DOC013 |
| D | CAL010 | DOC011 | 1 | DOC012;DOC023;DOC011;DOC018;DOC022;DOC014;DOC016;DOC005;DOC001;DOC013;DOC020;DOC002;DOC021;DOC010;DOC015;DOC009;DOC006;DOC024;DOC004;DOC017;DOC019 |
| C | CAL011 | DOC012 | 1 | DOC012;DOC011;DOC013;DOC016;DOC023;DOC015;DOC009;DOC021;DOC022;DOC005;DOC018;DOC014;DOC017;DOC010;DOC004;DOC002;DOC006;DOC020 |
| D | CAL011 | DOC012 | 1 | DOC012;DOC011;DOC023;DOC016;DOC009;DOC013;DOC010;DOC020;DOC015;DOC005;DOC002;DOC017;DOC022;DOC021;DOC018;DOC014;DOC019;DOC004;DOC006 |
| C | CAL012 | DOC013 | 1 | DOC013;DOC005;DOC004;DOC006;DOC016;DOC007;DOC015;DOC002;DOC022;DOC018;DOC010;DOC017;DOC003;DOC019;DOC020;DOC023 |
| D | CAL012 | DOC013 | 1 | DOC005;DOC013;DOC016;DOC004;DOC018;DOC010;DOC006;DOC015;DOC003;DOC020;DOC014;DOC023;DOC007;DOC021;DOC002;DOC022;DOC012;DOC017;DOC009;DOC011;DOC019;DOC001 |
| C | CAL013 | DOC014 | 1 | DOC014;DOC009;DOC020;DOC023;DOC019;DOC010;DOC007;DOC006;DOC021;DOC018;DOC016;DOC002;DOC005 |
| D | CAL013 | DOC014 | 1 | DOC014;DOC009;DOC020;DOC007;DOC006;DOC019;DOC021;DOC018;DOC023;DOC016;DOC010;DOC005;DOC013;DOC015;DOC002;DOC011 |
| C | CAL014 | DOC015 | 1 | DOC015;DOC007;DOC016;DOC002;DOC005;DOC001;DOC004;DOC021;DOC003;DOC010;DOC006;DOC020;DOC009;DOC019;DOC018;DOC022;DOC023 |
| D | CAL014 | DOC015 | 1 | DOC015;DOC016;DOC002;DOC005;DOC020;DOC010;DOC022;DOC018;DOC007;DOC001;DOC004;DOC009;DOC021;DOC023;DOC014;DOC003;DOC006;DOC019;DOC011;DOC017;DOC013;DOC012 |
| C | CAL015 | DOC016 | 1 | DOC016;DOC007;DOC002;DOC019;DOC021;DOC015;DOC005;DOC022;DOC020;DOC014;DOC018;DOC004;DOC017;DOC013;DOC006;DOC003 |
| D | CAL015 | DOC016 | 1 | DOC016;DOC007;DOC013;DOC014;DOC022;DOC004;DOC005;DOC020;DOC019;DOC018;DOC002;DOC021;DOC015;DOC023;DOC012;DOC017;DOC011;DOC010;DOC006;DOC003 |
| C | CAL016 | DOC017 | 1 | DOC017;DOC022;DOC018;DOC002;DOC003;DOC020;DOC001;DOC024;DOC023;DOC021;DOC019;DOC006;DOC004 |
| D | CAL016 | DOC017 | 1 | DOC017;DOC018;DOC002;DOC022;DOC003;DOC019;DOC023;DOC021;DOC009;DOC014;DOC020;DOC001;DOC024;DOC013;DOC015;DOC016;DOC006;DOC004 |
| C | CAL017 | DOC018 | 1 | DOC018;DOC019;DOC020;DOC021;DOC017;DOC024;DOC023;DOC022 |
| D | CAL017 | DOC018 | 1 | DOC018;DOC020;DOC019;DOC021;DOC024;DOC017;DOC023;DOC022;DOC014;DOC009;DOC004;DOC002;DOC015 |
| C | CAL018 | DOC019 | 1 | DOC019;DOC018;DOC020;DOC021;DOC023;DOC024;DOC022;DOC016;DOC009;DOC013;DOC007 |
| D | CAL018 | DOC019 | 1 | DOC018;DOC019;DOC020;DOC022;DOC021;DOC023;DOC024;DOC013;DOC017;DOC014;DOC016;DOC009;DOC002;DOC007 |
| C | CAL019 | DOC020 | 1 | DOC020;DOC005;DOC009;DOC014;DOC019;DOC018;DOC010;DOC021;DOC023;DOC007;DOC013;DOC015;DOC006 |
| D | CAL019 | DOC020 | 1 | DOC014;DOC009;DOC020;DOC005;DOC018;DOC019;DOC023;DOC021;DOC007;DOC013;DOC017;DOC010;DOC015;DOC006;DOC016 |
| C | CAL020 | DOC021 | 1 | DOC019;DOC021;DOC018;DOC022;DOC020;DOC024;DOC017;DOC023;DOC002;DOC016;DOC003;DOC015 |
| D | CAL020 | DOC021 | 1 | DOC021;DOC019;DOC018;DOC023;DOC017;DOC020;DOC015;DOC016;DOC002;DOC022;DOC024;DOC005;DOC009;DOC013;DOC014;DOC003;DOC001;DOC010 |
| C | CAL021 | DOC022 | 1 | DOC022;DOC003;DOC018;DOC017;DOC006;DOC002;DOC024;DOC005;DOC004;DOC010;DOC020;DOC023;DOC011;DOC012;DOC019 |
| D | CAL021 | DOC022 | 1 | DOC022;DOC003;DOC002;DOC006;DOC017;DOC010;DOC005;DOC018;DOC023;DOC020;DOC004;DOC024;DOC009;DOC021;DOC014;DOC016;DOC015;DOC013;DOC011;DOC012;DOC019 |
| C | CAL022 | DOC023 | 1 | DOC023;DOC024;DOC018;DOC020;DOC022;DOC019;DOC017;DOC002;DOC021;DOC003 |
| D | CAL022 | DOC023 | 1 | DOC023;DOC024;DOC018;DOC019;DOC020;DOC017;DOC022;DOC021;DOC002;DOC014;DOC004;DOC010;DOC003;DOC013;DOC015;DOC005;DOC009 |
| C | CAL023 | DOC024 | 1 | DOC024;DOC017;DOC002;DOC022;DOC018;DOC003;DOC021;DOC023;DOC005;DOC020;DOC006;DOC004;DOC007 |
| D | CAL023 | DOC024 | 1 | DOC024;DOC017;DOC005;DOC023;DOC018;DOC003;DOC006;DOC002;DOC009;DOC012;DOC022;DOC011;DOC007;DOC015;DOC021;DOC014;DOC013;DOC020;DOC019;DOC016;DOC001;DOC004 |
| C | CAL024 | DOC004 | 1 | DOC005;DOC007;DOC004;DOC013;DOC018;DOC016;DOC020;DOC010;DOC014;DOC012;DOC009;DOC017;DOC023;DOC002;DOC022 |
| D | CAL024 | DOC004 | 1 | DOC005;DOC016;DOC004;DOC013;DOC020;DOC007;DOC014;DOC012;DOC010;DOC002;DOC023;DOC018;DOC022;DOC009;DOC017;DOC011;DOC003 |
| C | CAL025 | DOC005 | 1 | DOC013;DOC005;DOC004;DOC016;DOC007;DOC015;DOC006;DOC002;DOC022;DOC010;DOC003;DOC018;DOC023;DOC019;DOC001;DOC012;DOC021 |
| D | CAL025 | DOC005 | 1 | DOC005;DOC013;DOC016;DOC004;DOC007;DOC018;DOC006;DOC001;DOC023;DOC022;DOC002;DOC012;DOC010;DOC011;DOC020;DOC015;DOC014;DOC003;DOC019;DOC021 |
| C | CAL026 | DOC013 | 1 | DOC005;DOC013;DOC004;DOC016;DOC010;DOC003;DOC015;DOC021;DOC022;DOC002;DOC007;DOC006;DOC009;DOC018;DOC020;DOC012;DOC001;DOC019 |
| D | CAL026 | DOC013 | 1 | DOC005;DOC013;DOC003;DOC016;DOC004;DOC022;DOC018;DOC006;DOC015;DOC009;DOC020;DOC002;DOC010;DOC021;DOC019;DOC007;DOC014;DOC023;DOC017;DOC012;DOC001;DOC024 |
| C | CAL027 | DOC007 | 1 | DOC007;DOC016;DOC015;DOC021;DOC005;DOC013;DOC009;DOC019;DOC004;DOC014;DOC002;DOC006;DOC023;DOC017;DOC022 |
| D | CAL027 | DOC007 | 1 | DOC007;DOC016;DOC015;DOC019;DOC014;DOC013;DOC009;DOC022;DOC017;DOC012;DOC021;DOC005;DOC023;DOC018;DOC020;DOC011;DOC004;DOC002;DOC024;DOC006;DOC010 |
| C | CAL028 | DOC016 | 1 | DOC016;DOC007;DOC015;DOC019;DOC021;DOC014;DOC018;DOC002;DOC003;DOC013;DOC017;DOC005;DOC022;DOC006;DOC020;DOC023 |
| D | CAL028 | DOC016 | 1 | DOC016;DOC007;DOC013;DOC019;DOC014;DOC020;DOC006;DOC022;DOC018;DOC005;DOC015;DOC021;DOC023;DOC012;DOC002;DOC003;DOC011;DOC017;DOC004;DOC009;DOC024;DOC010 |
| C | CAL029 | DOC011 | 1 | DOC012;DOC011;DOC015;DOC016;DOC005;DOC021;DOC022;DOC017;DOC002;DOC023;DOC018;DOC013;DOC004;DOC014;DOC006;DOC009;DOC024 |
| D | CAL029 | DOC011 | 1 | DOC012;DOC011;DOC023;DOC005;DOC017;DOC016;DOC021;DOC013;DOC014;DOC024;DOC015;DOC022;DOC020;DOC018;DOC002;DOC010;DOC019;DOC004;DOC006;DOC009 |
| C | CAL030 | DOC012 | 1 | DOC012;DOC011;DOC015;DOC013;DOC016;DOC009;DOC018;DOC021;DOC017;DOC023;DOC014;DOC022;DOC010;DOC006;DOC005;DOC004;DOC002 |
| D | CAL030 | DOC012 | 1 | DOC012;DOC011;DOC018;DOC016;DOC017;DOC023;DOC013;DOC005;DOC010;DOC015;DOC009;DOC021;DOC014;DOC002;DOC022;DOC003;DOC006;DOC004;DOC020 |
| C | CAL031 | DOC009 | 1 | DOC002;DOC004;DOC003;DOC020;DOC007;DOC005;DOC001;DOC021;DOC019;DOC018;DOC006;DOC009;DOC022;DOC010;DOC016;DOC015;DOC023;DOC017;DOC024 |
| D | CAL031 | DOC009 | 1 | DOC002;DOC020;DOC019;DOC007;DOC022;DOC018;DOC005;DOC009;DOC006;DOC010;DOC016;DOC015;DOC014;DOC004;DOC003;DOC013;DOC001;DOC021;DOC023;DOC017;DOC024 |
| C | CAL032 | DOC014 | 1 | DOC020;DOC018;DOC019;DOC009;DOC021;DOC014;DOC023;DOC002;DOC016;DOC001;DOC004;DOC005;DOC007;DOC022;DOC003 |
| D | CAL032 | DOC014 | 1 | DOC020;DOC014;DOC018;DOC009;DOC019;DOC021;DOC007;DOC016;DOC002;DOC005;DOC010;DOC023;DOC006;DOC013;DOC022;DOC001;DOC004;DOC015;DOC003 |

## Neutral Conclusion

The BGE reranker experiment completed successfully after increasing only the Cloud Foundry task disk allocation. It provides the final planned reranker-model comparison evidence before retrieval architecture selection. No production architecture, abstention threshold, LLM layer, or RAG behavior is selected or implemented here.
