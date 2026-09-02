import csv
import os
import sys
import time


# Allow imports from project root.
PROJECT_ROOT = os.path.dirname(
    os.path.dirname(
        os.path.abspath(__file__)
    )
)

if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)


from scripts.evaluate_retrieval_variants_v2 import (  # noqa: E402
    MODEL_NAME,
    RRF_K,
    TABLE_NAME,
    bm25_rank,
    build_bm25_index,
    dedupe_document_ranking,
    fetch_corpus_chunks,
    fetch_dense_chunks,
    find_expected_rank,
    is_supported,
    reciprocal_rank_fusion
)


HELDOUT_FILE = "data/retrieval_abstention_heldout_v2.csv"
ABSTENTION_DENSE_SCORE_THRESHOLD = 0.75


def load_heldout_queries():
    with open(
        HELDOUT_FILE,
        newline="",
        encoding="utf-8"
    ) as file:
        return list(
            csv.DictReader(
                file
            )
        )


def score_at(document_ranking, index):
    if len(document_ranking) <= index:
        return None

    return document_ranking[index]["score"]


def document_at(document_ranking, index):
    if len(document_ranking) <= index:
        return ""

    return document_ranking[index]["document_id"]


def score_margin(document_ranking):
    first_score = score_at(
        document_ranking,
        0
    )
    second_score = score_at(
        document_ranking,
        1
    )

    if (
        first_score is None
        or second_score is None
    ):
        return None

    return first_score - second_score


def top_documents(document_ranking, limit=5):
    return ";".join(
        item["document_id"]
        for item in document_ranking[:limit]
    )


def bool_as_int(value):
    return int(
        bool(value)
    )


def format_float(value, digits=4):
    if value is None:
        return ""

    return f"{float(value):.{digits}f}"


def is_safe_to_answer(result, depth):
    return (
        result["EXPECTED_SUPPORTED"] == "1"
        and result["EXPECTED_RANK"] > 0
        and result["EXPECTED_RANK"] <= depth
    )


def should_accept(dense_rank1_score):
    return (
        dense_rank1_score is not None
        and dense_rank1_score >= ABSTENTION_DENSE_SCORE_THRESHOLD
    )


def evaluate_question(item, corpus_chunks, bm25_index):
    dense_chunks, embedding_ms, hana_ms = fetch_dense_chunks(
        item["QUESTION"]
    )

    lexical_start = time.perf_counter()
    lexical_chunks = bm25_rank(
        item["QUESTION"],
        corpus_chunks,
        bm25_index
    )
    lexical_ms = (
        time.perf_counter() - lexical_start
    ) * 1000

    hybrid_start = time.perf_counter()
    hybrid_chunks = reciprocal_rank_fusion(
        [
            dense_chunks,
            lexical_chunks
        ],
        RRF_K
    )
    hybrid_fusion_ms = (
        time.perf_counter() - hybrid_start
    ) * 1000

    dense_documents = dedupe_document_ranking(
        dense_chunks,
        "dense_score"
    )
    hybrid_documents = dedupe_document_ranking(
        hybrid_chunks,
        "fused_score"
    )

    expected_document = item["EXPECTED_DOCUMENT_ID"].strip()
    expected_rank = find_expected_rank(
        hybrid_documents,
        expected_document
    )

    dense_rank1_score = score_at(
        dense_documents,
        0
    )
    accepted = should_accept(
        dense_rank1_score
    )

    return {
        "QUERY_ID": item["QUERY_ID"],
        "EXPECTED_SUPPORTED": item["EXPECTED_SUPPORTED"].strip(),
        "EXPECTED_DOCUMENT_ID": expected_document,
        "CATEGORY": item["CATEGORY"],
        "EXPECTED_RANK": (
            expected_rank
            if expected_rank is not None
            else 0
        ),
        "DENSE_RANK1_DOCUMENT_ID": document_at(
            dense_documents,
            0
        ),
        "DENSE_RANK1_SCORE": dense_rank1_score,
        "DENSE_RANK2_DOCUMENT_ID": document_at(
            dense_documents,
            1
        ),
        "DENSE_RANK2_SCORE": score_at(
            dense_documents,
            1
        ),
        "DENSE_RANK1_RANK2_MARGIN": score_margin(
            dense_documents
        ),
        "HYBRID_RANK1_DOCUMENT_ID": document_at(
            hybrid_documents,
            0
        ),
        "HYBRID_RANK1_SCORE": score_at(
            hybrid_documents,
            0
        ),
        "HYBRID_RANK2_DOCUMENT_ID": document_at(
            hybrid_documents,
            1
        ),
        "HYBRID_RANK2_SCORE": score_at(
            hybrid_documents,
            1
        ),
        "HYBRID_RANK1_RANK2_MARGIN": score_margin(
            hybrid_documents
        ),
        "HYBRID_TOP5_DOCUMENTS": top_documents(
            hybrid_documents
        ),
        "DENSE_HYBRID_RANK1_AGREE": bool_as_int(
            document_at(
                dense_documents,
                0
            )
            == document_at(
                hybrid_documents,
                0
            )
        ),
        "ACCEPT_DECISION": (
            "ACCEPT"
            if accepted
            else "ABSTAIN"
        ),
        "HYBRID_TOP1_CORRECT": bool_as_int(
            is_supported(item)
            and expected_rank == 1
        ),
        "HYBRID_TOP3_CORRECT": bool_as_int(
            is_supported(item)
            and expected_rank is not None
            and expected_rank <= 3
        ),
        "HYBRID_TOP5_CORRECT": bool_as_int(
            is_supported(item)
            and expected_rank is not None
            and expected_rank <= 5
        ),
        "EMBEDDING_MS": embedding_ms,
        "DENSE_HANA_MS": hana_ms,
        "LEXICAL_MS": lexical_ms,
        "HYBRID_FUSION_MS": hybrid_fusion_ms,
        "TOTAL_RETRIEVAL_MS": (
            embedding_ms
            + hana_ms
            + lexical_ms
            + hybrid_fusion_ms
        )
    }


def summarize_retrieval(results):
    supported_results = [
        result
        for result in results
        if result["EXPECTED_SUPPORTED"] == "1"
    ]
    total = len(
        supported_results
    )

    top1 = sum(
        result["HYBRID_TOP1_CORRECT"]
        for result in supported_results
    )
    top3 = sum(
        result["HYBRID_TOP3_CORRECT"]
        for result in supported_results
    )
    top5 = sum(
        result["HYBRID_TOP5_CORRECT"]
        for result in supported_results
    )
    reciprocal_rank_sum = 0.0

    for result in supported_results:
        rank = result["EXPECTED_RANK"]
        reciprocal_rank_sum += (
            1.0 / rank
            if rank
            else 0.0
        )

    return {
        "SUPPORTED_TOTAL": total,
        "TOP1_COUNT": top1,
        "TOP1": (
            top1 / total
            if total
            else 0.0
        ),
        "TOP3_COUNT": top3,
        "TOP3": (
            top3 / total
            if total
            else 0.0
        ),
        "TOP5_COUNT": top5,
        "TOP5": (
            top5 / total
            if total
            else 0.0
        ),
        "MRR": (
            reciprocal_rank_sum / total
            if total
            else 0.0
        )
    }


def summarize_scope(results):
    true_accepts = []
    false_accepts = []
    true_abstentions = []
    false_rejects = []

    for result in results:
        supported = result["EXPECTED_SUPPORTED"] == "1"
        accepted = result["ACCEPT_DECISION"] == "ACCEPT"

        if supported and accepted:
            true_accepts.append(
                result
            )
        elif supported and not accepted:
            false_rejects.append(
                result
            )
        elif not supported and accepted:
            false_accepts.append(
                result
            )
        else:
            true_abstentions.append(
                result
            )

    unsupported = [
        result
        for result in results
        if result["EXPECTED_SUPPORTED"] == "0"
    ]
    near_domain = [
        result
        for result in unsupported
        if result["CATEGORY"] == "unsupported_near_domain"
    ]
    out_of_scope = [
        result
        for result in unsupported
        if result["CATEGORY"] == "unsupported_out_of_scope"
    ]

    accepted_total = len(true_accepts) + len(false_accepts)
    supported_total = len(true_accepts) + len(false_rejects)
    unsupported_total = len(true_abstentions) + len(false_accepts)

    return {
        "TRUE_ACCEPTS": len(true_accepts),
        "FALSE_ACCEPTS": len(false_accepts),
        "TRUE_ABSTENTIONS": len(true_abstentions),
        "FALSE_REJECTS": len(false_rejects),
        "ACCEPT_PRECISION": (
            len(true_accepts) / accepted_total
            if accepted_total
            else 0.0
        ),
        "SUPPORTED_ACCEPT_RECALL": (
            len(true_accepts) / supported_total
            if supported_total
            else 0.0
        ),
        "UNSUPPORTED_ABSTAIN_RATE": (
            len(true_abstentions) / unsupported_total
            if unsupported_total
            else 0.0
        ),
        "NEAR_DOMAIN_ABSTAIN_RATE": abstain_rate(
            near_domain
        ),
        "OUT_OF_SCOPE_ABSTAIN_RATE": abstain_rate(
            out_of_scope
        ),
        "FALSE_ACCEPT_QUERY_IDS": query_ids(
            false_accepts
        ),
        "FALSE_REJECT_QUERY_IDS": query_ids(
            false_rejects
        )
    }


def abstain_rate(results):
    if not results:
        return 0.0

    abstained = sum(
        1
        for result in results
        if result["ACCEPT_DECISION"] == "ABSTAIN"
    )

    return abstained / len(results)


def summarize_safety(results, depth):
    safe_results = [
        result
        for result in results
        if is_safe_to_answer(
            result,
            depth
        )
    ]
    accepted_results = [
        result
        for result in results
        if result["ACCEPT_DECISION"] == "ACCEPT"
    ]
    safe_accepts = [
        result
        for result in accepted_results
        if is_safe_to_answer(
            result,
            depth
        )
    ]
    unsafe_accepts = [
        result
        for result in accepted_results
        if not is_safe_to_answer(
            result,
            depth
        )
    ]
    false_rejects = [
        result
        for result in safe_results
        if result["ACCEPT_DECISION"] == "ABSTAIN"
    ]

    accepted_total = len(
        accepted_results
    )
    safe_total = len(
        safe_results
    )
    total = len(
        results
    )

    return {
        "DEPTH": depth,
        "SAFE_ACCEPTS": len(
            safe_accepts
        ),
        "UNSAFE_ACCEPTS": len(
            unsafe_accepts
        ),
        "FALSE_REJECTS_SAFE": len(
            false_rejects
        ),
        "ACCEPTED_ANSWER_PRECISION": (
            len(safe_accepts) / accepted_total
            if accepted_total
            else 0.0
        ),
        "SAFE_ANSWER_RECALL": (
            len(safe_accepts) / safe_total
            if safe_total
            else 0.0
        ),
        "COVERAGE": (
            accepted_total / total
            if total
            else 0.0
        ),
        "UNSAFE_ACCEPT_QUERY_IDS": query_ids(
            unsafe_accepts
        ),
        "FALSE_REJECT_SAFE_QUERY_IDS": query_ids(
            false_rejects
        )
    }


def query_ids(results):
    return ";".join(
        result["QUERY_ID"]
        for result in results
    )


def print_dataset_summary(queries):
    supported = [
        item
        for item in queries
        if is_supported(item)
    ]
    near_domain = [
        item
        for item in queries
        if item["CATEGORY"] == "unsupported_near_domain"
    ]
    out_of_scope = [
        item
        for item in queries
        if item["CATEGORY"] == "unsupported_out_of_scope"
    ]

    print()
    print("=" * 90)
    print("DATASET SUMMARY")
    print("=" * 90)
    print(f"TOTAL,{len(queries)}")
    print(f"SUPPORTED,{len(supported)}")
    print(f"UNSUPPORTED_NEAR_DOMAIN,{len(near_domain)}")
    print(f"UNSUPPORTED_OUT_OF_SCOPE,{len(out_of_scope)}")


def print_retrieval_summary(results):
    summary = summarize_retrieval(
        results
    )

    print()
    print("=" * 90)
    print("SUPPORTED RETRIEVAL METRICS")
    print("=" * 90)
    print(
        "SUPPORTED_TOTAL,"
        "TOP1,"
        "TOP1_COUNT,"
        "TOP3,"
        "TOP3_COUNT,"
        "TOP5,"
        "TOP5_COUNT,"
        "MRR"
    )
    print(
        f"{summary['SUPPORTED_TOTAL']},"
        f"{summary['TOP1']:.4f},"
        f"{summary['TOP1_COUNT']},"
        f"{summary['TOP3']:.4f},"
        f"{summary['TOP3_COUNT']},"
        f"{summary['TOP5']:.4f},"
        f"{summary['TOP5_COUNT']},"
        f"{summary['MRR']:.4f}"
    )


def print_scope_summary(results):
    summary = summarize_scope(
        results
    )

    print()
    print("=" * 90)
    print("ABSTENTION SCOPE METRICS")
    print("=" * 90)
    print(
        "TRUE_ACCEPTS,"
        "FALSE_ACCEPTS,"
        "TRUE_ABSTENTIONS,"
        "FALSE_REJECTS,"
        "ACCEPT_PRECISION,"
        "SUPPORTED_ACCEPT_RECALL,"
        "UNSUPPORTED_ABSTAIN_RATE,"
        "NEAR_DOMAIN_ABSTAIN_RATE,"
        "OUT_OF_SCOPE_ABSTAIN_RATE,"
        "FALSE_ACCEPT_QUERY_IDS,"
        "FALSE_REJECT_QUERY_IDS"
    )
    print(
        f"{summary['TRUE_ACCEPTS']},"
        f"{summary['FALSE_ACCEPTS']},"
        f"{summary['TRUE_ABSTENTIONS']},"
        f"{summary['FALSE_REJECTS']},"
        f"{summary['ACCEPT_PRECISION']:.4f},"
        f"{summary['SUPPORTED_ACCEPT_RECALL']:.4f},"
        f"{summary['UNSUPPORTED_ABSTAIN_RATE']:.4f},"
        f"{summary['NEAR_DOMAIN_ABSTAIN_RATE']:.4f},"
        f"{summary['OUT_OF_SCOPE_ABSTAIN_RATE']:.4f},"
        f"{summary['FALSE_ACCEPT_QUERY_IDS']},"
        f"{summary['FALSE_REJECT_QUERY_IDS']}"
    )


def print_safety_summary(results, depth):
    summary = summarize_safety(
        results,
        depth
    )

    print()
    print("=" * 90)
    print(f"TOP-{depth} ANSWER SAFETY METRICS")
    print("=" * 90)
    print(
        "DEPTH,"
        "SAFE_ACCEPTS,"
        "UNSAFE_ACCEPTS,"
        "FALSE_REJECTS_SAFE,"
        "ACCEPTED_ANSWER_PRECISION,"
        "SAFE_ANSWER_RECALL,"
        "COVERAGE,"
        "UNSAFE_ACCEPT_QUERY_IDS,"
        "FALSE_REJECT_SAFE_QUERY_IDS"
    )
    print(
        f"{summary['DEPTH']},"
        f"{summary['SAFE_ACCEPTS']},"
        f"{summary['UNSAFE_ACCEPTS']},"
        f"{summary['FALSE_REJECTS_SAFE']},"
        f"{summary['ACCEPTED_ANSWER_PRECISION']:.4f},"
        f"{summary['SAFE_ANSWER_RECALL']:.4f},"
        f"{summary['COVERAGE']:.4f},"
        f"{summary['UNSAFE_ACCEPT_QUERY_IDS']},"
        f"{summary['FALSE_REJECT_SAFE_QUERY_IDS']}"
    )


def print_detailed_results(results):
    print()
    print("=" * 90)
    print("PER-QUERY HELD-OUT RESULTS")
    print("=" * 90)
    print(
        "QUERY_ID,"
        "EXPECTED_SUPPORTED,"
        "EXPECTED_DOCUMENT_ID,"
        "CATEGORY,"
        "EXPECTED_RANK,"
        "DENSE_RANK1_DOCUMENT_ID,"
        "DENSE_RANK1_SCORE,"
        "DENSE_RANK2_DOCUMENT_ID,"
        "DENSE_RANK2_SCORE,"
        "DENSE_RANK1_RANK2_MARGIN,"
        "HYBRID_RANK1_DOCUMENT_ID,"
        "HYBRID_RANK1_SCORE,"
        "HYBRID_RANK2_DOCUMENT_ID,"
        "HYBRID_RANK2_SCORE,"
        "HYBRID_RANK1_RANK2_MARGIN,"
        "HYBRID_TOP5_DOCUMENTS,"
        "DENSE_HYBRID_RANK1_AGREE,"
        "ACCEPT_DECISION,"
        "HYBRID_TOP1_CORRECT,"
        "HYBRID_TOP3_CORRECT,"
        "HYBRID_TOP5_CORRECT,"
        "SAFE_TO_ANSWER_TOP3,"
        "SAFE_TO_ANSWER_TOP5,"
        "EMBEDDING_MS,"
        "DENSE_HANA_MS,"
        "LEXICAL_MS,"
        "HYBRID_FUSION_MS,"
        "TOTAL_RETRIEVAL_MS"
    )

    for result in results:
        print(
            f"{result['QUERY_ID']},"
            f"{result['EXPECTED_SUPPORTED']},"
            f"{result['EXPECTED_DOCUMENT_ID']},"
            f"{result['CATEGORY']},"
            f"{result['EXPECTED_RANK']},"
            f"{result['DENSE_RANK1_DOCUMENT_ID']},"
            f"{format_float(result['DENSE_RANK1_SCORE'])},"
            f"{result['DENSE_RANK2_DOCUMENT_ID']},"
            f"{format_float(result['DENSE_RANK2_SCORE'])},"
            f"{format_float(result['DENSE_RANK1_RANK2_MARGIN'])},"
            f"{result['HYBRID_RANK1_DOCUMENT_ID']},"
            f"{format_float(result['HYBRID_RANK1_SCORE'])},"
            f"{result['HYBRID_RANK2_DOCUMENT_ID']},"
            f"{format_float(result['HYBRID_RANK2_SCORE'])},"
            f"{format_float(result['HYBRID_RANK1_RANK2_MARGIN'])},"
            f"{result['HYBRID_TOP5_DOCUMENTS']},"
            f"{result['DENSE_HYBRID_RANK1_AGREE']},"
            f"{result['ACCEPT_DECISION']},"
            f"{result['HYBRID_TOP1_CORRECT']},"
            f"{result['HYBRID_TOP3_CORRECT']},"
            f"{result['HYBRID_TOP5_CORRECT']},"
            f"{bool_as_int(is_safe_to_answer(result, 3))},"
            f"{bool_as_int(is_safe_to_answer(result, 5))},"
            f"{format_float(result['EMBEDDING_MS'], 2)},"
            f"{format_float(result['DENSE_HANA_MS'], 2)},"
            f"{format_float(result['LEXICAL_MS'], 2)},"
            f"{format_float(result['HYBRID_FUSION_MS'], 2)},"
            f"{format_float(result['TOTAL_RETRIEVAL_MS'], 2)}"
        )


def main():
    print("SAP BTP Documentation Assistant")
    print("Version 2 Fresh Held-Out Retrieval And Abstention Validation")
    print("=" * 90)
    print(f"Held-out file: {HELDOUT_FILE}")
    print(f"Target table: {TABLE_NAME}")
    print(f"Dense embedding model: {MODEL_NAME}")
    print("Selected retrieval: full dense ranking + full BM25-style lexical ranking + RRF")
    print(f"RRF k: {RRF_K}")
    print("Reranker: none")
    print(
        "Candidate abstention gate: dense document-level top-1 "
        f"cosine score >= {ABSTENTION_DENSE_SCORE_THRESHOLD:.2f}"
    )
    print(
        "This script is read-only to HANA and does not modify "
        "production app.py."
    )

    queries = load_heldout_queries()
    print_dataset_summary(
        queries
    )

    corpus_chunks, corpus_hana_ms = fetch_corpus_chunks()
    print(
        f"Corpus chunks loaded: {len(corpus_chunks)} "
        f"({corpus_hana_ms:.2f} ms one-time read)"
    )
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

    print_retrieval_summary(
        results
    )
    print_scope_summary(
        results
    )
    print_safety_summary(
        results,
        3
    )
    print_safety_summary(
        results,
        5
    )
    print_detailed_results(
        results
    )

    print()
    print("=" * 90)
    print("NOTE")
    print("=" * 90)
    print(
        "This is fresh held-out validation for the frozen candidate "
        "configuration only. It does not tune or implement a production "
        "abstention threshold."
    )


if __name__ == "__main__":
    main()
