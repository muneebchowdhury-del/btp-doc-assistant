# V2 Report Evidence Ledger

## Purpose

This ledger is the master index for reconstructing the V2 SAP BTP Documentation Assistant project in the final report. It links each major experiment or engineering milestone to its purpose, frozen configuration state, version-control reference, primary artifact, result, interpretation, and likely report section.

It does not replace the raw artifacts or experiment-specific protocol/result documents. The raw files remain the authoritative evidence.

## Evidence Ledger

| Stage / experiment | Purpose | Configuration / intervention | Version-control reference | Primary evidence | Main result / interpretation | Report use |
|---|---|---|---|---|---|---|
| Original V1 retrieval baseline | Establish initial semantic-retrieval benchmark before V2 work | Frozen V1 semantic retrieval | Preserved V1 baseline | V1 evaluation artifacts | 30 queries; Top-1 66.67%, Top-3 96.67%, Top-5 100%, MRR 0.8083 | Baseline / motivation |
| V2 HDI + corpus deployment | Create expanded V2 documentation corpus without overwriting V1 | `DOCUMENT_CHUNKS_V2`; BAAI/bge-small-en-v1.5; 384 dimensions | See `docs/V2_DEPLOYMENT_EVIDENCE.md` | `docs/V2_DEPLOYMENT_EVIDENCE.md` | 23 documents processed, 1 skipped (DOC008), 138 chunks embedded; V1 table preserved | Data / architecture / implementation |
| V2 regression retrieval | Measure V2 corpus behavior on prior query set | V2 corpus with existing dense retrieval | See deployment evidence | `docs/V2_DEPLOYMENT_EVIDENCE.md` | V1 regression set on V2: Top-1 63.33%, Top-3 93.33%, Top-5 96.67%, MRR 0.7731; this is distinct from the original frozen V1 baseline | Retrieval comparison |
| Retrieval variant experiments | Compare candidate V2 retrieval methods | Dense, lexical/hybrid and reranking candidates | See V2 retrieval protocol/results documents | `docs/V2_RETRIEVAL_VARIANTS_PROTOCOL.md` and related results if present; retrieval scripts | Basis for selecting the hybrid retrieval design used downstream | Methodology / retrieval selection |
| BGE reranker experiment | Test reranking as a possible retrieval improvement | BGE reranker candidate | See `docs/V2_BGE_RERANKER_EXPERIMENT_PROTOCOL.md` | `docs/V2_BGE_RERANKER_EXPERIMENT_RESULTS.md` | Preserved as a controlled alternative; final system did not rely on endless reranker tuning | Rejected/alternative approaches |
| Abstention calibration | Select retrieval-confidence threshold without using held-out final generation data | Dense rank-1 score threshold calibration | See `docs/V2_ABSTENTION_CALIBRATION_PROTOCOL.md` | `docs/V2_ABSTENTION_CALIBRATION_RESULTS.md` | Final threshold fixed at 0.75 before held-out evaluation | Safety / calibration methodology |
| Held-out retrieval/abstention validation | Validate threshold and retrieval behavior on distinct held-out questions | Frozen retrieval and threshold | See held-out protocol docs | `data/retrieval_abstention_heldout_v2.csv`, held-out assessment/audit files | Established supported vs near-domain vs clear-out-of-scope behavior before final RAG reporting | Retrieval held-out results |
| Gemini RAG development baseline | Establish initial grounded-generation behavior | Gemini 3.5 Flash; shared grounding prompt; fixed RAG development subset | Earlier RAG development commits | `data/rag_development_primary_results_v2.csv`; Gemini confirmation artifact | Gemini useful for development but later hit quota/provider errors on RAGDEV015/016/019 | Generation baseline |
| Groq provider comparison | Compare Groq to Gemini using the same questions and contexts | Groq `openai/gpt-oss-120b`, reasoning medium, default sampling | Commit `6946c0b0b13468ab048b4305dc6774e26d1f9252` | `data/rag_generation_provider_groq_results_v2.csv`; SHA-256 `F29E4828C2675E1A621758142528477B14056FF9793F506163A747B6AD0E835D` | Groq completed 16/16 with no provider errors; Gemini completed 13/16 because of three quota errors. Completion is not accuracy. | Provider selection |
| Provider latency comparison | Compare generation latency under paired generated cases | Same 12 common generated cases | Derived from provider comparison artifacts | Gemini/Groq raw result files | Gemini mean 13,094.44 ms / median 12,126.95 ms; Groq mean 1,245.97 ms / median 1,295.79 ms; ~10.51x mean speedup | Performance results |
| Groq citation refinement | Improve source traceability without changing retrieval/model | Added exact `[DOCxxx](SOURCE_URL)` requirement | Commit `cc697c9f3889620c617803c487ee4348f1997b1b` | `data/rag_generation_provider_groq_citation_refinement_results_v2.csv`; SHA-256 `E46FA6B1697A6A84C8E356BDEF8B2A089DDB9D948224F66C0A7DF32312A85439`; result commit `77a2973ec6a546466c291b0bd722b7fccf01d815` | Baseline Groq expected-URL compliance 3/15 improved to 14/14 among eligible generated supported cases in the refinement batch | Citation-quality experiment |
| RAGDEV004 unseeded repeatability | Test whether borderline answer/refusal behavior was stable | Citation-refined Groq; default sampling; same evidence repeated 5 times | Commit short `a6df76b` | `data/ragdev004_groq_citation_refinement_repeatability_v2.csv`; SHA-256 `5C0C538DB5CB0C9A1D2FD9CD09B49933E23B834A9C947C713130F6492C07A63` | Manual audit: 1 valid answer / 4 refusals. Automatic classifier had misclassified two refusals as generated answers. | Repeatability + evaluator failure |
| Outcome classifier refinement | Separate full answers, refusals and partial scoped abstention correctly | Added semantic/refusal wording variants; preserved old raw labels | Subsequent classifier-fix commit | `scripts/rag_generation_outcomes_v2.py`; raw repeatability artifact retained | Demonstrated evaluation-instrument failure distinct from model failure; raw outputs are necessary | Methodological limitation / evaluator validation |
| Seed-42 repeatability | Test best-effort deterministic sampling | Groq citation refinement + seed 42 | Embedded commit `d5bc8806311b73b9255e15be9132f0500c0d9e43` | `data/ragdev004_groq_seed42_repeatability_v2.csv`; SHA-256 `1E4CE580E41CCAF3DB9B6E402061F113A19DD289EB94AF4DA8997714E7DF7590` | 4 generated / 1 refusal, but one generated answer selected DOC005 rather than expected DOC004. Seed did not guarantee document-level stability. | Reproducibility experiment |
| Seed-42 + temperature 0 | Test whether lower sampling temperature improves stability | Seed 42 + temperature 0 | Embedded commit `1d3b45d74620bf49074210702da9a05d2d11721f` | `data/ragdev004_groq_seed42_temp0_repeatability_v2.csv` | Manual audit: 1 answer / 4 refusals; configuration became more conservative rather than reliably correct | Rejected sampling intervention |
| Inference calibration repeatability | Address false refusals caused by exact-wording expectations | Restored provider-default sampling; added generic semantic-support rule | Embedded commit `edc422ec0b4ea347a8ca9be16ee8b9119848862b` | `data/ragdev004_groq_inference_calibration_repeatability_v2.csv` | 3 valid generated / 2 refusals; generated cases cited DOC004 and labeled inference | Prompt refinement |
| Full inference-calibration validation | Verify refined prompt on all 16 development cases | Final Groq prompt + citations + semantic-support rule | Commit `a4377ab` | `data/rag_generation_provider_groq_inference_calibration_results_v2.csv`; SHA-256 `39146187FE530EFAC9B4A100A5DEEA5DE7C7347D59DB7EC747B6EC45430F0027` | 15 supported generated + 1 unsupported refusal; 0 provider errors. Outcome-level development alignment 16/16; not equivalent to factual-answer accuracy. | Final development validation |
| Final development freeze | Prevent held-out tuning | Final Groq config: `openai/gpt-oss-120b`, reasoning medium, default sampling, citation refinement + semantic-support calibration; retrieval threshold 0.75 | Tag `v2-rag-final-dev-freeze` at `a4377ab` | Git tag + frozen files | No prompt/model/provider/retrieval-threshold tuning after this point based on held-out final-generation results | Contamination prevention |
| Final held-out RAG evaluation | Measure frozen end-to-end performance | 40 held-out questions: 24 supported + 16 unsupported | Run under `v2-rag-final-dev-freeze` | `data/rag_heldout_final_groq_results_v2.csv`; SHA-256 `9DE3FABBB9F9CE439A24D45DEB6FF6FB60FA6F282AB4F86C3279664F025A7346` | 20 generated, 19 pipeline abstain, 1 LLM refusal; supported generated 19/24; unsupported safe handling 15/16; expected Top-1 13/24; expected Top-5 22/24; 0 provider errors | Final quantitative results |
| Final semantic audit | Separate mechanical outcomes from semantic correctness | Manual review of each final held-out case; raw CSV unchanged | Commit `8a55a7df7b8a2a2af6e15781ed3a4093bd5303f4` | `data/rag_heldout_semantic_audit_v2.csv` | Five supported false abstentions were retrieval-gate failures; HOUT025 was primary unsafe end-to-end answer; HOUT028 showed successful LLM refusal after retrieval false accept; HOUT006 showed retrieval/generation alignment failure | Final qualitative results / limitations |
| UI integration | Expose frozen V2 RAG pipeline in the Flask application | Question -> frozen retrieval -> threshold -> Groq -> answer/refusal -> SAP sources | UI integration commit in branch history | `app.py`, `rag_pipeline.py`, `templates/index.html`, `static/app.css`, `static/app.js` | Local smoke test generated answer with sources DOC001/DOC018; only UI/presentation work followed final evaluation | Implementation |
| Groq Cloud Foundry credential binding | Resolve production credential delivery | User-provided CF service `groq-rag-dev` with `GROQ_API_KEY`; service binding + restage | Deployment state, not a RAG code change | Final deployment validation record | Initial live request correctly failed before LLM call because key was absent; service was created/bound/restaged and live generation then succeeded | Deployment / operational lessons |
| Final deployed system validation | Confirm implementation and document protocol deviations | Frozen RAG logic + polished UI; HANA and Groq bindings | `ab812dde0fc25307817810e3994cf7b7f1175cfd` | `docs/V2_FINAL_SYSTEM_VALIDATION.md` | Live application operational; supported grounded answer and unrelated-question abstention validated; remaining work is report synthesis | Final system status |

## Key Numerical Results for the Report

### Original V1 baseline

- Queries: 30
- Top-1: 66.67%
- Top-3: 96.67%
- Top-5: 100%
- MRR: 0.8083

### V2 final held-out end-to-end run

- Total: 40
- Supported: 24
- Unsupported: 16
- Generated answers: 20
- Pipeline abstentions: 19
- LLM refusals: 1
- Supported answer coverage: 19/24 = 79.17%
- Unsupported safe handling: 15/16 = 93.75%
- Near-domain unsupported safe handling: 7/8 = 87.50%
- Clear out-of-scope safe handling: 8/8 = 100%
- Expected document Top-1: 13/24 = 54.17%
- Expected document Top-5: 22/24 = 91.67%
- Provider errors: 0

### Final qualitative failure decomposition

- Supported retrieval-gate false abstentions: 5 (`HOUT004`, `HOUT005`, `HOUT011`, `HOUT017`, `HOUT024`)
- Primary unsafe unsupported answer: 1 (`HOUT025`)
- Unsupported retrieval false accept recovered by LLM refusal: 1 (`HOUT028`)
- Material supported retrieval/generation alignment failure: `HOUT006`

## Report Principles

1. Do not call `GENERATED_ANSWER` equivalent to a correct answer.
2. Do not call provider completion equivalent to model accuracy.
3. Report the original V1 baseline separately from the V2-corpus regression run on the old V1 query set.
4. Preserve and discuss evaluator/classifier failures as methodology evidence, not hide them.
5. Separate retrieval-stage false rejection, retrieval false acceptance, LLM refusal, grounded answer quality, and citation quality.
6. Treat the final held-out run as frozen evidence; do not tune the V2 system based on its weaknesses.
7. Use the semantic audit as a separate qualitative layer rather than modifying the canonical raw results.

## Recommended Final Report Structure

1. Problem and research objective
2. SAP BTP / HANA Cloud system architecture
3. Data and document corpus construction
4. V1 baseline
5. V2 retrieval methodology and experiments
6. Abstention calibration and contamination prevention
7. RAG generation design
8. Gemini vs Groq provider comparison
9. Citation refinement
10. Repeatability, evaluator failure and sampling experiments
11. Inference calibration and final development freeze
12. Final held-out end-to-end evaluation
13. Manual semantic audit and failure analysis
14. UI integration and SAP BTP Cloud Foundry deployment
15. Limitations
16. Conclusions and future work
