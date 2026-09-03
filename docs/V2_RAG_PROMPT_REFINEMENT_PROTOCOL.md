# Version 2 RAG Prompt Refinement Protocol

## Purpose

This protocol records a minimal prompt refinement for the Version 2 RAG generation layer after the scored RAG development experiment.

The change is derived only from development evidence. It is not based on frozen retrieval held-out evidence, final end-to-end evidence, or any new retrieval or generation run.

## Motivation

The development results showed:

- false refusals on `RAGDEV002` and `RAGDEV004`, where the supplied evidence supported a grounded answer but the model refused;
- successful grounded answers on other accepted development questions;
- an appropriate refusal on `RAGDEV019`;
- mild verbosity in some observable LLM outputs.

The prompt is therefore refined to clarify when semantic evidence and reasonable inference are sufficient, when refusal is required, and how concise the generated answer should be.

## Frozen Boundaries

The retrieval and abstention system remains frozen:

- HANA table: `DOCUMENT_CHUNKS_V2`
- corpus and source catalog: unchanged
- chunking: unchanged
- embedding model: `BAAI/bge-small-en-v1.5`
- dense retrieval: existing HANA cosine ranking
- lexical retrieval: existing BM25-style ranking
- fusion: full dense ranking plus full lexical ranking through Reciprocal Rank Fusion
- `RRF k = 60`
- preliminary dense document-level top-1 gate: `>= 0.75`
- reranker: none
- RAG context: Top-5 unique documents, one highest-ranked fused chunk per document
- provider: Gemini Developer API
- model: `gemini-3.5-flash`

Historical primary and secondary development outputs, canonical scoring files, frozen retrieval calibration evidence, retrieval held-out evidence, datasets, HANA contents, and production `app.py` remain unchanged.

## Prompt Refinement

The grounding/refusal/concision instructions are refined without weakening the grounding contract.

The model must still:

- answer only from supplied retrieved SAP documentation evidence;
- avoid unsupported external knowledge;
- cite supplied SAP sources;
- distinguish inference from direct evidence;
- avoid inventing URLs, SAP features, configuration steps, commands, plans, or service names;
- use the exact refusal phrase `available documentation is insufficient` when refusing.

The clarified principles are:

- Semantic evidence: exact wording is not required when supplied evidence is semantically equivalent.
- Reasonable inference: if an answer follows reasonably from supplied evidence, answer it and explicitly label the inferential part.
- Refusal boundary: refuse only when answering would require factual information that is neither stated in nor reasonably supported by the supplied evidence.
- Missing details: when evidence supports the core answer but not extra requested details, answer the supported part and state which details are unsupported.
- Concision: answer directly first, include only necessary supporting detail, and do not enumerate unrelated retrieved documents merely because they were supplied.

The prompt must not instruct the model to guess, use external knowledge, or relax citation and anti-invention requirements.

## Development Confirmation Policy

After this prompt change, a development confirmation run may reuse the already accepted RAG development questions and preserved contexts because `RAGDEV` is development/tuning evidence, not final evaluation evidence.

The confirmation run must:

- not rerun retrieval;
- reuse the exact `QUESTION` and exact `CONTEXTS` preserved in `data/rag_development_primary_results_v2.csv`;
- include all 16 primary `ACCEPT` queries: 15 supported accepted queries plus the accepted near-domain unsupported query `RAGDEV019`;
- execute those questions in the preserved primary-result order;
- use Gemini model `gemini-3.5-flash`;
- use provider/model default generation parameters;
- pace provider calls with 15 seconds between calls because the Gemini free tier exposed a 5 requests/minute limit;
- make exactly one provider attempt per confirmation query;
- use no automatic retry, backoff, fallback model, or fallback provider;
- preserve any provider/API error as a provider error in the confirmation results.

Confirmation outputs must be stored separately. They must never overwrite or retroactively alter the canonical primary run, secondary retry results, or scoring files.

The confirmation purpose is to decide whether this refined prompt should be frozen for the final RAG architecture.

## Final Evaluation Boundary

The RAG development set is not a final hold-out set. Existing `RAGDEV` questions and retrieval-heldout questions cannot serve as final end-to-end RAG evaluation.

After the generation architecture is finalized, a completely fresh preregistered end-to-end RAG evaluation set is mandatory. No prompt or model tuning will be performed on that final set.

## Non-Execution Confirmation

This protocol change does not:

- call Gemini;
- query HANA;
- run retrieval;
- execute RAG development generation;
- execute the secondary provider retry;
- modify canonical CSV evidence;
- modify production `app.py`;
- change retrieval or abstention parameters.
