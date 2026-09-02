from dataclasses import dataclass
from typing import Any


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
If the supplied evidence is inadequate, say that the available documentation is insufficient.
Cite the provided SAP source(s) using their document IDs and source URLs.
Distinguish direct evidence from inference.
Do not invent URLs, SAP features, configuration steps, commands, plans, or service names.
Keep the answer concise and documentation-oriented."""


class LLMProviderNotConfigured(RuntimeError):
    """Raised when generation is requested before a provider is configured."""


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
            "- Answer only from the retrieved evidence above.",
            "- If the evidence does not support the answer, refuse by saying the available documentation is insufficient.",
            "- Cite each SAP source used with its document ID and source URL.",
            "- Label any inference explicitly.",
            "- Do not invent URLs, features, commands, configuration steps, or service plans.",
            "- Keep the answer concise."
        ]
    )

    return GroundedPromptPayload(
        system=GROUNDING_SYSTEM_INSTRUCTIONS,
        user=user_prompt,
        contexts=normalized_contexts
    )


def generate_grounded_answer(question: str, contexts: list[dict[str, Any]]) -> str:
    build_grounded_prompt(
        question,
        contexts
    )

    raise LLMProviderNotConfigured(
        "No external LLM provider adapter is configured; no LLM request was made."
    )
