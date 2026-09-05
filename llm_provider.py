from dataclasses import dataclass
import json
import os
from typing import Any


GEMINI_MODEL = "gemini-3.5-flash"
GEMINI_API_KEY_ENV_VAR = "GEMINI_API_KEY"
GEMINI_CF_SERVICE_NAME = "gemini-rag-dev"
GROQ_MODEL = "openai/gpt-oss-120b"
GROQ_API_KEY_ENV_VAR = "GROQ_API_KEY"
GROQ_CF_SERVICE_NAME = "groq-rag-dev"
GROQ_SEED = 42
GROQ_TEMPERATURE = 0.0
VCAP_SERVICES_ENV_VAR = "VCAP_SERVICES"

REQUIRED_CONTEXT_FIELDS = (
    "document_id",
    "title",
    "source_url",
    "chunk_text",
    "retrieval_rank"
)

GROUNDING_SYSTEM_INSTRUCTIONS = """You are a documentation assistant for SAP BTP.

Use only the supplied retrieved SAP documentation evidence.
Do not use unsupported external knowledge to fill missing information.
Do not require exact wording; semantically equivalent evidence can be sufficient.
If the requested answer follows reasonably from the supplied evidence, answer it and label the inferential part explicitly as an inference.
Refuse only when answering would require factual information that is neither stated in nor reasonably supported by the supplied evidence; when refusing, say that the available documentation is insufficient.
If the evidence supports the core answer but not additional requested details, answer the supported part and state which details are not supported.
Cite the provided SAP source(s) using their document IDs and source URLs.
Do not invent URLs, SAP features, configuration steps, commands, plans, or service names.
Answer the question directly first.
Include only the supporting detail necessary to substantiate the answer.
Do not enumerate unrelated retrieved documents merely because they were supplied.
Keep the answer concise and documentation-oriented."""


class LLMProviderNotConfigured(RuntimeError):
    """Raised when generation is requested before a provider is configured."""


class LLMProviderCredentialError(RuntimeError):
    """Raised when the configured provider cannot find required credentials."""


@dataclass(frozen=True)
class GroundingContext:
    document_id: str
    title: str
    source_url: str
    chunk_text: str
    retrieval_rank: int


@dataclass(frozen=True)
class GroundedPromptPayload:
    system: str
    user: str
    contexts: tuple[GroundingContext, ...]


def _require_text(value: Any, field_name: str) -> str:
    text = str(
        value or ""
    ).strip()

    if not text:
        raise ValueError(
            f"Context field {field_name} is required."
        )

    return text


def _normalize_rank(value: Any) -> int:
    try:
        rank = int(
            value
        )
    except (
        TypeError,
        ValueError
    ) as error:
        raise ValueError(
            "Context field retrieval_rank must be an integer."
        ) from error

    if rank < 1:
        raise ValueError(
            "Context field retrieval_rank must be >= 1."
        )

    return rank


def normalize_context(context: dict[str, Any]) -> GroundingContext:
    missing_fields = [
        field
        for field in REQUIRED_CONTEXT_FIELDS
        if field not in context
    ]

    if missing_fields:
        raise ValueError(
            "Context is missing required field(s): "
            + ", ".join(
                missing_fields
            )
        )

    return GroundingContext(
        document_id=_require_text(
            context["document_id"],
            "document_id"
        ),
        title=_require_text(
            context["title"],
            "title"
        ),
        source_url=_require_text(
            context["source_url"],
            "source_url"
        ),
        chunk_text=_require_text(
            context["chunk_text"],
            "chunk_text"
        ),
        retrieval_rank=_normalize_rank(
            context["retrieval_rank"]
        )
    )


def normalize_contexts(contexts: list[dict[str, Any]]) -> tuple[GroundingContext, ...]:
    normalized = tuple(
        sorted(
            (
                normalize_context(
                    context
                )
                for context in contexts
            ),
            key=lambda item: item.retrieval_rank
        )
    )

    if not normalized:
        raise ValueError(
            "At least one grounding context is required."
        )

    return normalized


def build_context_block(contexts: tuple[GroundingContext, ...]) -> str:
    sections = []

    for context in contexts:
        sections.append(
            "\n".join(
                [
                    f"[{context.retrieval_rank}] {context.document_id}: {context.title}",
                    f"Source: {context.source_url}",
                    "Excerpt:",
                    context.chunk_text
                ]
            )
        )

    return "\n\n".join(
        sections
    )


def build_grounded_prompt(question: str, contexts: list[dict[str, Any]]) -> GroundedPromptPayload:
    clean_question = str(
        question or ""
    ).strip()

    if not clean_question:
        raise ValueError(
            "Question is required."
        )

    normalized_contexts = normalize_contexts(
        contexts
    )
    context_block = build_context_block(
        normalized_contexts
    )

    user_prompt = "\n".join(
        [
            "Question:",
            clean_question,
            "",
            "Retrieved SAP documentation evidence:",
            context_block,
            "",
            "Answering requirements:",
            "- Answer only from the retrieved evidence above; do not use external knowledge.",
            "- Treat semantically equivalent evidence as sufficient even when the documentation does not use the exact wording of the question.",
            "- If the answer follows reasonably from the supplied evidence, answer it and explicitly label the inferential part as an inference.",
            "- Refuse only when answering would require factual information that is neither stated in nor reasonably supported by the supplied evidence; use the phrase available documentation is insufficient.",
            "- If evidence supports the core answer but not additional requested details, answer the supported part and clearly state which details are not supported.",
            "- Cite each SAP source used with its document ID and source URL.",
            "- Do not invent URLs, features, commands, configuration steps, service plans, or service names.",
            "- Answer directly first and include only the supporting detail needed.",
            "- Do not enumerate unrelated retrieved documents merely because they were supplied."
        ]
    )

    return GroundedPromptPayload(
        system=GROUNDING_SYSTEM_INSTRUCTIONS,
        user=user_prompt,
        contexts=normalized_contexts
    )


def _extract_response_text(response: Any) -> str:
    text = getattr(
        response,
        "text",
        None
    )

    if text:
        return str(
            text
        ).strip()

    return ""


def _resolve_gemini_api_key() -> str:
    return _resolve_api_key(
        GEMINI_API_KEY_ENV_VAR,
        GEMINI_CF_SERVICE_NAME
    )


def _resolve_groq_api_key() -> str:
    return _resolve_api_key(
        GROQ_API_KEY_ENV_VAR,
        GROQ_CF_SERVICE_NAME
    )


def _resolve_api_key(env_var_name: str, cf_service_name: str) -> str:
    direct_api_key = str(
        os.getenv(
            env_var_name
        )
        or ""
    ).strip()

    if direct_api_key:
        return direct_api_key

    vcap_services = str(
        os.getenv(
            VCAP_SERVICES_ENV_VAR
        )
        or ""
    ).strip()

    if vcap_services:
        try:
            service_groups = json.loads(
                vcap_services
            )
        except json.JSONDecodeError:
            service_groups = {}

        if isinstance(
            service_groups,
            dict
        ):
            for services in service_groups.values():
                if not isinstance(
                    services,
                    list
                ):
                    continue

                for service in services:
                    if not isinstance(
                        service,
                        dict
                    ):
                        continue

                    if service.get(
                        "name"
                    ) != cf_service_name:
                        continue

                    credentials = service.get(
                        "credentials",
                        {}
                    )

                    if not isinstance(
                        credentials,
                        dict
                    ):
                        continue

                    service_api_key = str(
                        credentials.get(
                            env_var_name
                        )
                        or ""
                    ).strip()

                    if service_api_key:
                        return service_api_key

    raise LLMProviderCredentialError(
        f"{env_var_name} is not configured; no LLM request was made."
    )


def _generate_with_gemini(payload: GroundedPromptPayload) -> str:
    api_key = _resolve_gemini_api_key()

    from google import genai
    from google.genai import types

    with genai.Client(
        api_key=api_key
    ) as client:
        response = client.models.generate_content(
            model=GEMINI_MODEL,
            contents=payload.user,
            config=types.GenerateContentConfig(
                system_instruction=payload.system
            )
        )

    return _extract_response_text(
        response
    )


def _extract_groq_response_text(response: Any) -> str:
    choices = getattr(
        response,
        "choices",
        None
    )

    if not choices:
        return ""

    message = getattr(
        choices[0],
        "message",
        None
    )

    if message is None:
        return ""

    content = getattr(
        message,
        "content",
        None
    )

    if content:
        return str(
            content
        ).strip()

    return ""


def _generate_with_groq(payload: GroundedPromptPayload) -> str:
    api_key = _resolve_groq_api_key()

    from groq import Groq

    client = Groq(
        api_key=api_key,
        max_retries=0
    )
    response = client.chat.completions.create(
        model=GROQ_MODEL,
        messages=[
            {
                "role": "system",
                "content": payload.system
            },
            {
                "role": "user",
                "content": payload.user
                + "\n\nGroq-specific citation-format requirement:\n"
                + "- For every SAP source cited, include both its document ID and the exact source URL from the retrieved evidence.\n"
                + "- Use this exact format: [DOCxxx](SOURCE_URL).\n"
                + "- Do not cite a document ID without its source URL.\n"
                + "- Before returning the answer, verify that every cited SAP document includes its exact retrieved source URL."
            }
        ],
        reasoning_effort="medium",
        include_reasoning=False,
        seed=GROQ_SEED,
        temperature=GROQ_TEMPERATURE
    )

    return _extract_groq_response_text(
        response
    )


def generate_grounded_answer(question: str, contexts: list[dict[str, Any]]) -> str:
    payload = build_grounded_prompt(
        question,
        contexts
    )

    answer = _generate_with_gemini(
        payload
    )

    if not answer:
        raise LLMProviderNotConfigured(
            "The LLM provider returned no text."
        )

    return answer


def generate_grounded_answer_groq(question: str, contexts: list[dict[str, Any]]) -> str:
    payload = build_grounded_prompt(
        question,
        contexts
    )

    answer = _generate_with_groq(
        payload
    )

    if not answer:
        raise LLMProviderNotConfigured(
            "The LLM provider returned no text."
        )

    return answer
