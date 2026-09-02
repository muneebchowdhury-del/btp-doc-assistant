from typing import Any


RAG_CONTEXT_LIMIT = 5
RAG_CONTEXT_FIELDS = (
    "document_id",
    "title",
    "source_url",
    "chunk_text",
    "retrieval_rank"
)


def _read_field(item: Any, field_name: str) -> Any:
    if isinstance(
        item,
        dict
    ):
        return item.get(
            field_name
        )

    return getattr(
        item,
        field_name,
        None
    )


def _require_text(item: Any, field_name: str) -> str:
    text = str(
        _read_field(
            item,
            field_name
        )
        or ""
    ).strip()

    if not text:
        raise ValueError(
            f"Hybrid result field {field_name} is required."
        )

    return text


def build_rag_contexts_from_hybrid_results(
    hybrid_chunks: list[Any],
    limit: int = RAG_CONTEXT_LIMIT
) -> list[dict[str, Any]]:
    if limit < 1:
        raise ValueError(
            "RAG context limit must be >= 1."
        )

    contexts = []
    seen_documents = set()

    for chunk in hybrid_chunks:
        document_id = _require_text(
            chunk,
            "document_id"
        )

        if document_id in seen_documents:
            continue

        seen_documents.add(
            document_id
        )

        contexts.append(
            {
                "document_id": document_id,
                "title": _require_text(
                    chunk,
                    "title"
                ),
                "source_url": _require_text(
                    chunk,
                    "source_url"
                ),
                "chunk_text": _require_text(
                    chunk,
                    "chunk_text"
                ),
                "retrieval_rank": len(
                    contexts
                )
                + 1
            }
        )

        if len(
            contexts
        ) >= limit:
            break

    return contexts
