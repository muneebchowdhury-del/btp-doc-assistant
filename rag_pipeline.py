import re
import threading

from llm_provider import generate_grounded_answer_groq
from scripts.evaluate_rag_development_v2 import evaluate_question
from scripts.evaluate_retrieval_variants_v2 import (
    build_bm25_index,
    fetch_corpus_chunks,
)


_assets_lock = threading.Lock()
_corpus_chunks = None
_bm25_index = None


def _get_retrieval_assets():
    global _corpus_chunks
    global _bm25_index

    with _assets_lock:
        if _corpus_chunks is None:
            _corpus_chunks, _ = fetch_corpus_chunks()

        if _bm25_index is None:
            _bm25_index = build_bm25_index(
                _corpus_chunks
            )

    return _corpus_chunks, _bm25_index


def _extract_cited_sources(answer, contexts):
    cited_ids = set(
        re.findall(
            r"DOC\d+",
            str(answer or "")
        )
    )

    sources = []
    seen = set()

    for context in contexts or []:
        document_id = context["document_id"]

        if document_id not in cited_ids:
            continue

        if document_id in seen:
            continue

        seen.add(document_id)

        sources.append(
            {
                "document_id": document_id,
                "title": context["title"],
                "source_url": context["source_url"],
            }
        )

    return sources


def answer_documentation_question(question):
    clean_question = str(
        question or ""
    ).strip()

    if not clean_question:
        raise ValueError(
            "Question is required."
        )

    corpus_chunks, bm25_index = (
        _get_retrieval_assets()
    )

    evaluation_item = {
        "QUERY_ID": "UI",
        "QUESTION": clean_question,
        "EXPECTED_SUPPORTED": "",
        "EXPECTED_DOCUMENT_ID": "",
        "CATEGORY": "ui_request",
        "REFERENCE_FACT": "",
    }

    result = evaluate_question(
        evaluation_item,
        corpus_chunks,
        bm25_index,
        answer_provider=generate_grounded_answer_groq,
    )

    answer = result.get(
        "GEMINI_ANSWER_OR_REFUSAL",
        ""
    )

    result["ANSWER"] = answer
    result["SOURCES"] = _extract_cited_sources(
        answer,
        result.get(
            "CONTEXTS",
            []
        ),
    )

    return result
