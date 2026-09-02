import csv
import os
import sys
import time
from typing import Any, Callable


# Allow imports from project root.
PROJECT_ROOT = os.path.dirname(
    os.path.dirname(
        os.path.abspath(__file__)
    )
)

if PROJECT_ROOT not in sys.path:
    sys.path.insert(
        0,
        PROJECT_ROOT
    )


from llm_provider import generate_grounded_answer  # noqa: E402
from rag_context import build_rag_contexts_from_hybrid_results  # noqa: E402
from scripts.evaluate_retrieval_variants_v2 import (  # noqa: E402
    RRF_K,
    bm25_rank,
    build_bm25_index,
    dedupe_document_ranking,
    fetch_corpus_chunks,
    fetch_dense_chunks,
    reciprocal_rank_fusion
)


RAG_DEVELOPMENT_FILE = "data/rag_development_v2.csv"
ABSTENTION_DENSE_SCORE_THRESHOLD = 0.75


def load_development_queries():
    with open(
        RAG_DEVELOPMENT_FILE,
        newline="",
        encoding="utf-8"
    ) as file:
        return list(
            csv.DictReader(
                file
            )
        )


def score_at(document_ranking, index):
    if len(
        document_ranking
    ) <= index:
        return None

    return document_ranking[index]["score"]


def document_at(document_ranking, index):
    if len(
        document_ranking
    ) <= index:
        return ""

    return document_ranking[index]["document_id"]


def top_documents(document_ranking, limit=5):
    return ";".join(
        item["document_id"]
        for item in document_ranking[:limit]
    )


def should_accept(dense_rank1_score):
    return (
        dense_rank1_score is not None
        and dense_rank1_score >= ABSTENTION_DENSE_SCORE_THRESHOLD
    )


def classify_provider_answer(answer):
    normalized = str(
        answer or ""
    ).lower()

    refusal_markers = (
        "available documentation is insufficient",
        "documentation is insufficient",
        "supplied evidence is insufficient",
        "evidence is insufficient",
        "insufficient evidence"
    )

    if any(
        marker in normalized
        for marker in refusal_markers
    ):
        return "LLM_REFUSAL"

    return "GENERATED_ANSWER"


def evaluate_question(
    item: dict[str, str],
    corpus_chunks,
    bm25_index,
    answer_provider: Callable[[str, list[dict[str, Any]]], str] = generate_grounded_answer
) -> dict[str, Any]:
    total_start = time.perf_counter()
    question = item["QUESTION"]

    dense_chunks, embedding_ms, hana_ms = fetch_dense_chunks(
        question
    )

    lexical_start = time.perf_counter()
    lexical_chunks = bm25_rank(
        question,
        corpus_chunks,
        bm25_index
    )
    lexical_ms = (
        time.perf_counter() - lexical_start
    ) * 1000

    fusion_start = time.perf_counter()
    hybrid_chunks = reciprocal_rank_fusion(
        [
            dense_chunks,
            lexical_chunks
        ],
        RRF_K
    )
    hybrid_fusion_ms = (
        time.perf_counter() - fusion_start
    ) * 1000

    dense_documents = dedupe_document_ranking(
        dense_chunks,
        "dense_score"
    )
    hybrid_documents = dedupe_document_ranking(
        hybrid_chunks,
        "fused_score"
    )

    dense_rank1_score = score_at(
        dense_documents,
        0
    )
    accepted = should_accept(
        dense_rank1_score
    )
    retrieval_ms = (
        embedding_ms
        + hana_ms
        + lexical_ms
        + hybrid_fusion_ms
    )

    contexts = []
    generation_ms = 0.0
    answer = ""
    provider_error = ""
    gemini_called = False
    outcome = "PIPELINE_ABSTAIN"

    if accepted:
        contexts = build_rag_contexts_from_hybrid_results(
            hybrid_chunks
        )
        gemini_called = True
        generation_start = time.perf_counter()

        try:
            answer = answer_provider(
                question,
                contexts
            )
            outcome = classify_provider_answer(
                answer
            )
        except Exception as error:  # noqa: BLE001
            provider_error = str(
                error
            )
            outcome = "PROVIDER_ERROR"
        finally:
            generation_ms = (
                time.perf_counter() - generation_start
            ) * 1000

    total_ms = (
        time.perf_counter() - total_start
    ) * 1000

    return {
        "QUERY_ID": item["QUERY_ID"],
        "QUESTION": question,
        "EXPECTED_SUPPORTED": item["EXPECTED_SUPPORTED"].strip(),
        "EXPECTED_DOCUMENT_ID": item["EXPECTED_DOCUMENT_ID"].strip(),
        "CATEGORY": item["CATEGORY"],
        "REFERENCE_FACT": item.get(
            "REFERENCE_FACT",
            ""
        ).strip(),
        "DENSE_RANK1_DOCUMENT_ID": document_at(
            dense_documents,
            0
        ),
        "DENSE_RANK1_SCORE": dense_rank1_score,
        "ACCEPT_DECISION": (
            "ACCEPT"
            if accepted
            else "ABSTAIN"
        ),
        "HYBRID_TOP5_DOCUMENTS": top_documents(
            hybrid_documents
        ),
        "CONTEXT_DOCUMENT_IDS": ";".join(
            context["document_id"]
            for context in contexts
        ),
        "CONTEXTS": contexts,
        "GEMINI_CALLED": gemini_called,
        "OUTCOME": outcome,
        "GEMINI_ANSWER_OR_REFUSAL": answer,
        "PROVIDER_ERROR": provider_error,
        "EMBEDDING_MS": embedding_ms,
        "DENSE_HANA_MS": hana_ms,
        "LEXICAL_MS": lexical_ms,
        "HYBRID_FUSION_MS": hybrid_fusion_ms,
        "RETRIEVAL_MS": retrieval_ms,
        "GENERATION_MS": generation_ms,
        "TOTAL_END_TO_END_MS": total_ms
    }


def format_result_row(result):
    row = dict(
        result
    )
    row["DENSE_RANK1_SCORE"] = (
        ""
        if row["DENSE_RANK1_SCORE"] is None
        else f"{float(row['DENSE_RANK1_SCORE']):.4f}"
    )

    for field in (
        "EMBEDDING_MS",
        "DENSE_HANA_MS",
        "LEXICAL_MS",
        "HYBRID_FUSION_MS",
        "RETRIEVAL_MS",
        "GENERATION_MS",
        "TOTAL_END_TO_END_MS"
    ):
        row[field] = f"{float(row[field]):.2f}"

    row["GEMINI_CALLED"] = int(
        bool(
            row["GEMINI_CALLED"]
        )
    )
    row["CONTEXTS"] = repr(
        row["CONTEXTS"]
    )

    return row


def main():
    queries = load_development_queries()
    corpus_chunks, corpus_read_ms = fetch_corpus_chunks()
    bm25_index = build_bm25_index(
        corpus_chunks
    )
    results = [
        evaluate_question(
            item,
            corpus_chunks,
            bm25_index
        )
        for item in queries
    ]

    fieldnames = list(
        format_result_row(
            results[0]
        ).keys()
    )
    writer = csv.DictWriter(
        sys.stdout,
        fieldnames=fieldnames,
        lineterminator="\n"
    )
    writer.writeheader()

    for result in results:
        writer.writerow(
            format_result_row(
                result
            )
        )


if __name__ == "__main__":
    main()
