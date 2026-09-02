# Version 2 RAG Generation Protocol

## Purpose

This protocol defines the first Version 2 RAG generation boundary after completion of retrieval and abstention research. It prepares a provider-agnostic external LLM interface and grounding contract without making any LLM API call, selecting a concrete external provider, or changing production application behavior.

## SAP-Native Provider Feasibility

The SAP-native feasibility result is accepted:

- SAP AI Core / Generative AI Hub: `UNAVAILABLE`

No further SAP AI Core investigation, entitlement work, service provisioning, service binding, or credential inspection is part of this phase.

Because SAP AI Core with the required Generative AI Hub-capable `extended` plan is unavailable in the currently targeted environment, Version 2 will proceed with a provider-agnostic external LLM boundary while keeping SAP BTP Cloud Foundry and SAP HANA Cloud as the application and retrieval platform.

No alternative external provider is selected in this protocol.

## Frozen Retrieval Boundary

Retrieval and abstention experimentation is closed. This phase does not modify:

- `DOCUMENT_CHUNKS_V2`
- corpus
- chunking
- embeddings
- `BAAI/bge-small-en-v1.5`
- BM25-style lexical retrieval
- full dense ranking
- full lexical ranking
- Reciprocal Rank Fusion
- `RRF k = 60`
- preliminary dense-score gate `0.75`
- held-out datasets or results
- production `app.py`

The frozen retrieval and generation input design is:

```text
question
-> frozen Hybrid RRF retrieval
-> dense-score 0.75 preliminary gate
-> Top-5 retrieved unique-document evidence
-> provider adapter
-> LLM
-> grounded answer or refusal
```

## Top-5 RAG Context Decision

The RAG stage will use Top-5 retrieved unique-document evidence as the generation context depth.

Rationale from completed held-out evidence:

- Held-out Top-3 retrieval: `0.7917`
- Held-out Top-5 retrieval: `0.9167`

This is a new RAG-stage input design choice. It does not alter, reinterpret, tune, or replace the frozen retrieval experiments, calibration results, abstention decision, held-out dataset, or held-out evidence.

## Provider-Neutral Adapter Architecture

The provider boundary is isolated in `llm_provider.py`.

Initial provider-neutral interface:

```python
def generate_grounded_answer(question, contexts):
    ...
```

The module also exposes unit-testable prompt construction helpers:

- `normalize_context(context)`
- `normalize_contexts(contexts)`
- `build_context_block(contexts)`
- `build_grounded_prompt(question, contexts)`

No provider-specific logic should be spread through `app.py`. A future implementation may add a provider adapter behind this interface after provider selection and credential review.

The context objects passed to the provider must contain at minimum:

- `document_id`
- `title`
- `source_url`
- `chunk_text`
- `retrieval_rank`

## Grounding And Refusal Contract

The generation prompt is frozen before observing any generated answer.

The model must:

- answer only from supplied retrieved SAP documentation
- not use unsupported external knowledge to fill missing information
- say that the available documentation is insufficient when evidence is inadequate
- cite the provided SAP source or sources
- distinguish evidence from inference
- avoid inventing URLs, SAP features, configuration steps, commands, or service plans
- keep answers concise and documentation-oriented

The future generation prompt must instruct the LLM to refuse when supplied evidence does not support the requested answer. This second-stage evidence-sufficiency mechanism is motivated by the held-out finding that the `0.75` dense cosine gate alone did not guarantee retrieval correctness.

No second numeric evidence-sufficiency threshold is introduced in this phase.

## Citation Requirements

Generated answers must cite the supplied SAP documentation evidence using the provided:

- document ID
- title
- source URL

The model must not invent or rewrite source URLs. If no supplied context supports an answer, the model must refuse rather than cite unrelated evidence.

## Credential And Security Approach

Credentials for any future external LLM provider must come only from environment variables or Cloud Foundry service configuration.

The repository must not contain:

- API keys
- OAuth client secrets
- service keys
- certificates
- `.env` files
- `VCAP_SERVICES` contents
- provider credentials

This phase adds no credentials and makes no provider request.

## Isolated LLM Connectivity Test Criteria

A future isolated LLM connectivity test will be considered successful only if:

- a concrete provider has been explicitly selected and approved
- credentials are supplied through environment variables or approved Cloud Foundry configuration
- no credentials are printed or committed
- the test uses a small fixed prompt and fixed dummy or reviewed context payload
- the response is captured as connectivity evidence, not as prompt quality evidence
- no production `app.py` behavior is changed
- no retrieval, abstention, corpus, embedding, or evaluation setting is changed

If SAP AI Core / Generative AI Hub remains unavailable, the test must not silently substitute another provider without explicit review.

## Evaluation Boundary

No prompt or model tuning will occur on the final end-to-end evaluation set.

Future generated-answer evaluation must be separated from retrieval evaluation and must use fresh, pre-registered questions and answer-quality criteria after the provider and prompt contract are reviewed.

## Current Non-Goals

This phase does not:

- choose an external LLM provider
- select an LLM model
- make an LLM request
- implement RAG in production
- modify production answer behavior in `app.py`
- deploy the app
- create SAP AI Core resources
- create or expose credentials
- change retrieval, abstention, corpus, chunking, embeddings, HANA tables, or evaluation evidence
