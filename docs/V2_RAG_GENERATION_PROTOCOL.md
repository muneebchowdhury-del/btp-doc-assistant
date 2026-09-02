# Version 2 RAG Generation Protocol

## Purpose

This protocol defines the Version 2 RAG generation boundary after completion of retrieval and abstention research. It records the provider-neutral LLM interface, grounding contract, selected external provider, and production boundary for the next reviewed RAG-generation step.

The grounding prompt and evidence contract were originally frozen before any generated-answer quality observations. Since then, isolated synthetic provider connectivity testing has occurred. No RAG answer-quality experiment, final end-to-end generation evaluation, or production `app.py` integration has occurred.

## SAP-Native Provider Feasibility

The SAP-native feasibility result is accepted:

- SAP AI Core / Generative AI Hub: `UNAVAILABLE`

No further SAP AI Core investigation, entitlement work, service provisioning, service binding, or credential inspection is part of this phase.

Because SAP AI Core with the required Generative AI Hub-capable `extended` plan is unavailable in the currently targeted environment, Version 2 will proceed with a provider-agnostic external LLM boundary while keeping SAP BTP Cloud Foundry and SAP HANA Cloud as the application and retrieval platform.

OpenAI was considered and an unexecuted adapter prototype was implemented before the provider decision changed. No OpenAI API request occurred. Before any generation experiment, the provider was changed to Gemini because the project requirement is zero API usage cost.

The final external generation provider is frozen for this project as:

- Provider: Google Gemini Developer API
- Model: `gemini-3.5-flash`
- Tier: Free
- Python SDK: `google-genai`
- Credential environment variable: `GEMINI_API_KEY`

This is a RAG-generation design choice. Multiple LLM providers or models will not be compared or tuned in this phase. Gemini is an external generation provider and is not SAP-native.

Free-tier input and output tokens are free subject to Google's current Gemini Developer API free-tier quotas. Billing was not enabled for this decision. Free-tier data may be used by Google to improve its products, so only public SAP documentation and non-sensitive research questions may be sent.

After provider connectivity testing, `gemini-3.7-flash` was not retained because repeated authenticated requests returned provider-side `503 UNAVAILABLE` high-demand failures. `gemini-3.6-flash` metadata access succeeded, but a controlled synthetic generation request timed out after 45 seconds with zero response bytes. `gemini-3.5-flash` completed the controlled synthetic connectivity test and is therefore the selected external generation model for the next reviewed RAG-generation step.

Connectivity testing used only synthetic text and did not use frozen retrieval held-out questions.

References checked for this provider boundary:

- Google Gen AI Python SDK documentation: `https://googleapis.github.io/python-genai/`
- Gemini model documentation: `https://ai.google.dev/gemini-api/docs/models`
- Gemini Developer API pricing: `https://ai.google.dev/gemini-api/docs/pricing`

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

Generation context construction is deterministic:

- retrieval continues to produce the frozen full Hybrid RRF ranking
- document-level results are deduplicated as already defined
- the RAG stage takes the Top-5 unique documents
- for each selected document, the provider receives the highest-ranked fused chunk belonging to that document as that document's `chunk_text`
- document-level retrieval order is preserved as `retrieval_rank`

This is the fixed RAG context-construction rule. It must not be adjusted by inspecting or reusing final held-out questions.

The deterministic retrieval-to-context bridge is implemented in `rag_context.py` as `build_rag_contexts_from_hybrid_results(hybrid_chunks, limit=5)`. The helper consumes an already-produced full Hybrid RRF chunk ranking and formats provider-neutral context objects; it does not run retrieval, alter RRF, apply abstention, call Gemini, or integrate generation into `app.py`.

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

No provider-specific logic should be spread through `app.py`. Gemini-specific code is isolated behind the provider-neutral boundary so another provider could later replace it without changing retrieval.

The context objects passed to the provider must contain at minimum:

- `document_id`
- `title`
- `source_url`
- `chunk_text`
- `retrieval_rank`

## Grounding And Refusal Contract

The generation prompt and grounding contract were frozen before observing any generated-answer quality results.

The model must:

- answer only from supplied retrieved SAP documentation
- not use unsupported external knowledge to fill missing information
- say that the available documentation is insufficient when evidence is inadequate
- cite the provided SAP source or sources
- distinguish evidence from inference
- avoid inventing URLs, SAP features, configuration steps, commands, or service plans
- keep answers concise and documentation-oriented

The generation prompt instructs the LLM to refuse when supplied evidence does not support the requested answer. This second-stage evidence-sufficiency mechanism is motivated by the held-out finding that the `0.75` dense cosine gate alone did not guarantee retrieval correctness.

No second numeric evidence-sufficiency threshold is introduced in this phase.

## Citation Requirements

Generated answers must cite the supplied SAP documentation evidence using the provided:

- document ID
- title
- source URL

The model must not invent or rewrite source URLs. If no supplied context supports an answer, the model must refuse rather than cite unrelated evidence.

## Credential And Security Approach

Credentials for the external LLM provider must come only from environment variables or approved Cloud Foundry service configuration.

The repository must not contain:

- API keys
- OAuth client secrets
- service keys
- certificates
- `.env` files
- `VCAP_SERVICES` contents
- provider credentials

No credentials are committed. Isolated synthetic provider connectivity testing has occurred, but no RAG answer-quality experiment or final end-to-end evaluation has occurred.

The Gemini adapter reads credentials only from `GEMINI_API_KEY`. The key must never be printed, logged, or committed.

## Isolated LLM Connectivity Test Result

The completed isolated LLM connectivity test was considered successful because:

- the frozen Gemini Developer API provider and `gemini-3.5-flash` model are used
- credentials are supplied through environment variables or approved Cloud Foundry configuration
- no credentials are printed or committed
- the test uses a small fixed prompt and fixed dummy or reviewed context payload
- the response is captured as connectivity evidence, not as prompt quality evidence
- no production `app.py` behavior is changed
- no retrieval, abstention, corpus, embedding, or evaluation setting is changed

The connectivity test proved `Python -> Gemini Developer API -> model response`. It was not an answer-quality experiment, prompt-tuning run, RAG evaluation, or production-readiness test.

## Evaluation Boundary

No prompt or model tuning will occur on the final end-to-end evaluation set.

Future generated-answer evaluation must be separated from retrieval evaluation and must use fresh, pre-registered questions and answer-quality criteria after the provider and prompt contract are reviewed.

## Current Non-Goals

This phase does not:

- implement RAG in production
- modify production answer behavior in `app.py`
- deploy the app
- create SAP AI Core resources
- create or expose credentials
- change retrieval, abstention, corpus, chunking, embeddings, HANA tables, or evaluation evidence
