# Version 2 RAG Development Protocol

## Purpose

This protocol pre-registers the Version 2 RAG development experiment before any RAG development execution. It defines the fixed development dataset, frozen retrieval-to-generation pipeline, recorded outputs, and answer-quality rubric.

This is a development experiment protocol, not production integration. Production `app.py` remains retrieval-only.

## Frozen Boundaries

Retrieval and abstention are permanently frozen for this phase:

- HANA table: `DOCUMENT_CHUNKS_V2`
- corpus and document source catalog: unchanged
- chunking: unchanged
- embedding model: `BAAI/bge-small-en-v1.5`
- dense retrieval: existing HANA cosine ranking
- lexical retrieval: existing BM25-style ranking over `TITLE`, `TOPIC`, and `CHUNK_TEXT`
- fusion: full dense ranking plus full lexical ranking through Reciprocal Rank Fusion
- `RRF k = 60`
- preliminary gate: dense document-level top-1 cosine score `>= 0.75`
- reranker: none
- Gemini provider: Google Gemini Developer API
- Gemini model: `gemini-3.5-flash`
- grounding/refusal prompt contract: unchanged
- deterministic context bridge: `build_rag_contexts_from_hybrid_results(hybrid_chunks)`

This protocol does not change historical V1/V2 evaluation datasets, retrieval calibration evidence, retrieval/abstention held-out datasets, held-out results, HANA tables, retrieval parameters, model configuration, provider configuration, or prompts.

## Development Dataset

The development dataset is `data/rag_development_v2.csv`.

Composition:

- Total questions: `24`
- Supported: `16`
- Near-domain unsupported: `4`
- Out-of-scope: `4`

The questions are fresh development questions and are not frozen retrieval held-out questions. Supported rows include an expected source document and a concise pre-execution `REFERENCE_FACT` grounded in the active V2 corpus.

This dataset may be used for RAG development analysis after review. It is not a final end-to-end evaluation set.

## Novelty And Leakage Check

Before execution, `scripts/audit_rag_development_novelty_v2.py` compares the development questions against:

- `data/evaluation_queries.csv`
- `data/evaluation_queries_v2_foundation.csv`
- `data/retrieval_calibration_v2.csv`
- `data/retrieval_abstention_heldout_v2.csv`

The audit uses:

- exact duplicate detection
- normalized lexical Jaccard overlap
- local question-to-question embedding cosine similarity with FastEmbed `BAAI/bge-small-en-v1.5`

The audit does not query HANA, retrieve corpus documents, call Gemini, inspect retrieval scores, or execute the RAG development harness.

No arbitrary semantic-similarity rejection threshold is used. Natural same-domain semantic similarity is acceptable when the question is substantively distinct and not an exact duplicate.

Audit evidence is recorded in `docs/V2_RAG_DEVELOPMENT_NOVELTY_AUDIT.md`.

## Frozen Development Pipeline

For each development question, the pre-registered pipeline is:

```text
Question
-> BGE dense retrieval from DOCUMENT_CHUNKS_V2
-> full BM25 TITLE + TOPIC + CHUNK_TEXT
-> full RRF, k=60
-> dense document-level top1 cosine gate >= 0.75
-> if below threshold: pipeline ABSTAIN, Gemini is NOT called
-> if accepted:
   deterministic Top-5 unique-document context
   using build_rag_contexts_from_hybrid_results(...)
-> gemini-3.5-flash
-> grounded answer or evidence-based refusal
```

The RAG harness must call `build_rag_contexts_from_hybrid_results(hybrid_chunks)` using the helper's default fixed Top-5 behavior. The context limit must not be overridden.

## Recorded Per-Query Fields

For every development query, the harness will record:

- query ID
- question
- expected supported status
- expected document
- dense rank-1 document
- dense rank-1 cosine score
- `ACCEPT` / `ABSTAIN` decision
- Hybrid Top-5 document IDs
- generated context object document IDs
- whether Gemini was called
- Gemini answer or refusal
- provider error, if one occurs
- retrieval latency
- generation latency
- total end-to-end latency

For pipeline abstention, no Gemini call must occur.

## Outcome Types

The development harness distinguishes:

- `PIPELINE_ABSTAIN`: the dense score gate is below `0.75`; Gemini is not called
- `GENERATED_ANSWER`: Gemini returns an answer that is not classified as an evidence-based refusal by the harness
- `LLM_REFUSAL`: Gemini returns a refusal indicating the supplied evidence is insufficient
- `PROVIDER_ERROR`: the provider raises an exception or fails before returning an answer

These are distinct outcomes and must not be merged in later analysis.

## Answer-Quality Rubric

Generated answers will be evaluated separately from retrieval performance.

Scoring uses simple reproducible fields:

| Criterion | Score | Definition |
| --- | --- | --- |
| Groundedness / faithfulness | `0` or `1` | `1` when factual claims are supported by the supplied retrieved chunks; `0` when unsupported factual claims appear. |
| Answer correctness | `0` or `1` | For supported questions with sufficient retrieved evidence, `1` when the answer contains the pre-registered `REFERENCE_FACT`; `0` otherwise. |
| Citation correctness | `0` or `1` | `1` when cited document IDs, titles, and URLs are among the supplied contexts and support the associated claim; `0` otherwise. |
| Unsupported claim / hallucination | `0` or `1` | `1` when unsupported factual SAP claims are introduced; `0` when they are not. Lower is better. |
| Evidence-based refusal | `0` or `1` | For unsupported or insufficient-evidence cases, `1` when the model refuses instead of inventing an answer; `0` otherwise. |
| Concision / documentation orientation | `0`, `1`, or `2` | Secondary descriptive score: `0` verbose or conversational, `1` usable, `2` concise and documentation-oriented. |

Also record:

- Gemini generation latency
- total pipeline latency
- provider failures

First-stage gate abstention, LLM evidence-based refusal, incorrect generated answer, and provider/API failure are not the same outcome.

## Non-Goals

This pre-execution preparation does not:

- execute `scripts/evaluate_rag_development_v2.py`
- send any development question to Gemini
- observe any development RAG answer
- use frozen retrieval held-out questions
- deploy the RAG pipeline
- change `app.py`
- tune retrieval, thresholds, prompts, models, corpus, or providers
