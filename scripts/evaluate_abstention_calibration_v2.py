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
    CALIBRATION_FILE,
    RRF_K,
    bm25_rank,
    build_bm25_index,
    dedupe_document_ranking,
    fetch_corpus_chunks,
    fetch_dense_chunks,
    find_expected_rank,
    is_supported,
    load_queries,
    reciprocal_rank_fusion
)


HIGH_RANKING_CHUNK_WINDOW = 10


def bool_as_int(value):
    return int(
        bool(value)
    )


def top_documents(document_ranking, limit=5):
    return ";".join(
        item["document_id"]
        for item in document_ranking[:limit]
    )


def score_at(document_ranking, index):
    if len(document_ranking) <= index:
        return None

    return document_ranking[index]["score"]


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


def count_rank1_chunk_support(ranked_chunks, rank1_document_id):
    if not rank1_document_id:
        return 0

    return sum(
        1
        for chunk in ranked_chunks[:HIGH_RANKING_CHUNK_WINDOW]
        if chunk.document_id == rank1_document_id
    )


def evaluate_question(item, corpus_chunks, bm25_index):
    dense_chunks, embedding_ms, hana_ms = fetch_dense_chunks(
        item["QUESTION"]
    )

    lexical_chunks = bm25_rank(
        item["QUESTION"],
        corpus_chunks,
        bm25_index
    )

    hybrid_start = time.perf_counter()
    hybrid_chunks = reciprocal_rank_fusion(
        [
            dense_chunks,
            lexical_chunks
        ],
        RRF_K
    )
    hybrid_ms = (
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

    dense_rank1 = (
        dense_documents[0]["document_id"]
        if dense_documents
        else ""
    )
    hybrid_rank1 = (
        hybrid_documents[0]["document_id"]
        if hybrid_documents
        else ""
    )

    expected_document = item["EXPECTED_DOCUMENT_ID"].strip()
    expected_rank = find_expected_rank(
        hybrid_documents,
        expected_document
    )

    hybrid_rank1_chunk_count = count_rank1_chunk_support(
        hybrid_chunks,
        hybrid_rank1
    )
    dense_rank1_chunk_count = count_rank1_chunk_support(
        dense_chunks,
        dense_rank1
    )

    dense_rank1_score = score_at(
        dense_documents,
        0
    )
    dense_margin = score_margin(
        dense_documents
    )
    hybrid_rank1_score = score_at(
        hybrid_documents,
        0
    )
    hybrid_margin = score_margin(
        hybrid_documents
    )

    return {
        "QUERY_ID": item["QUERY_ID"],
        "EXPECTED_SUPPORTED": item["EXPECTED_SUPPORTED"],
        "EXPECTED_DOCUMENT_ID": expected_document,
        "CATEGORY": item["CATEGORY"],
        "EXPECTED_RANK": (
            expected_rank
            if expected_rank is not None
            else 0
        ),
        "DENSE_RANK1_DOCUMENT_ID": dense_rank1,
        "DENSE_RANK1_SCORE": dense_rank1_score,
        "DENSE_RANK1_RANK2_MARGIN": dense_margin,
        "HYBRID_RANK1_DOCUMENT_ID": hybrid_rank1,
        "HYBRID_RANK1_SCORE": hybrid_rank1_score,
        "HYBRID_RANK1_RANK2_MARGIN": hybrid_margin,
        "DENSE_HYBRID_RANK1_AGREE": bool_as_int(
            dense_rank1 == hybrid_rank1
        ),
        "DENSE_RANK1_TOP_CHUNK_COUNT": dense_rank1_chunk_count,
        "HYBRID_RANK1_TOP_CHUNK_COUNT": hybrid_rank1_chunk_count,
        "HYBRID_TOP5_DOCUMENTS": top_documents(
            hybrid_documents
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
        "HYBRID_FUSION_MS": hybrid_ms
    }


def signal_value(result, signal_name):
    value = result[signal_name]

    if value is None:
        return 0.0

    return float(
        value
    )


def is_safe_to_answer(result, depth):
    return (
        result["EXPECTED_SUPPORTED"] == "1"
        and result["EXPECTED_RANK"] > 0
        and result["EXPECTED_RANK"] <= depth
    )


def candidate_rules():
    rules = []

    for threshold in [
        0.65,
        0.70,
        0.75
    ]:
        rules.append(
            {
                "RULE_ID": f"DENSE_SCORE_GE_{threshold:.2f}",
                "DESCRIPTION": (
                    f"dense top-1 cosine score >= {threshold:.2f}"
                ),
                "ACCEPT": lambda result, threshold=threshold:
                    signal_value(
                        result,
                        "DENSE_RANK1_SCORE"
                    ) >= threshold
            }
        )

    for threshold in [
        0.005,
        0.010,
        0.020
    ]:
        rules.append(
            {
                "RULE_ID": f"DENSE_MARGIN_GE_{threshold:.3f}",
                "DESCRIPTION": (
                    f"dense top-1/top-2 margin >= {threshold:.3f}"
                ),
                "ACCEPT": lambda result, threshold=threshold:
                    signal_value(
                        result,
                        "DENSE_RANK1_RANK2_MARGIN"
                    ) >= threshold
            }
        )

    for threshold in [
        0.0005,
        0.0010,
        0.0020
    ]:
        rules.append(
            {
                "RULE_ID": f"HYBRID_MARGIN_GE_{threshold:.4f}",
                "DESCRIPTION": (
                    f"hybrid rank-1/rank-2 RRF margin >= {threshold:.4f}"
                ),
                "ACCEPT": lambda result, threshold=threshold:
                    signal_value(
                        result,
                        "HYBRID_RANK1_RANK2_MARGIN"
                    ) >= threshold
            }
        )

    rules.extend(
        [
            {
                "RULE_ID": "DENSE_HYBRID_RANK1_AGREE",
                "DESCRIPTION": (
                    "dense and hybrid rank-1 document IDs agree"
                ),
                "ACCEPT": lambda result:
                    result["DENSE_HYBRID_RANK1_AGREE"] == 1
            },
            {
                "RULE_ID": "HYBRID_RANK1_MULTI_CHUNK_GE_2",
                "DESCRIPTION": (
                    "hybrid rank-1 document appears in at least 2 "
                    "of the top high-ranking chunks"
                ),
                "ACCEPT": lambda result:
                    result["HYBRID_RANK1_TOP_CHUNK_COUNT"] >= 2
            },
            {
                "RULE_ID": "HYBRID_RANK1_MULTI_CHUNK_GE_3",
                "DESCRIPTION": (
                    "hybrid rank-1 document appears in at least 3 "
                    "of the top high-ranking chunks"
                ),
                "ACCEPT": lambda result:
                    result["HYBRID_RANK1_TOP_CHUNK_COUNT"] >= 3
            },
            {
                "RULE_ID": "AGREE_AND_DENSE_SCORE_GE_0.70",
                "DESCRIPTION": (
                    "dense/hybrid rank-1 agreement and dense "
                    "top-1 score >= 0.70"
                ),
                "ACCEPT": lambda result:
                    result["DENSE_HYBRID_RANK1_AGREE"] == 1
                    and signal_value(
                        result,
                        "DENSE_RANK1_SCORE"
                    ) >= 0.70
            },
            {
                "RULE_ID": "AGREE_AND_HYBRID_MARGIN_GE_0.0010",
                "DESCRIPTION": (
                    "dense/hybrid rank-1 agreement and hybrid "
                    "RRF margin >= 0.0010"
                ),
                "ACCEPT": lambda result:
                    result["DENSE_HYBRID_RANK1_AGREE"] == 1
                    and signal_value(
                        result,
                        "HYBRID_RANK1_RANK2_MARGIN"
                    ) >= 0.0010
            },
            {
                "RULE_ID": "DENSE_SCORE_GE_0.70_AND_MULTI_CHUNK_GE_2",
                "DESCRIPTION": (
                    "dense top-1 score >= 0.70 and hybrid rank-1 "
                    "has at least 2 high-ranking chunks"
                ),
                "ACCEPT": lambda result:
                    signal_value(
                        result,
                        "DENSE_RANK1_SCORE"
                    ) >= 0.70
                    and result["HYBRID_RANK1_TOP_CHUNK_COUNT"] >= 2
            },
            {
                "RULE_ID": "AGREE_SCORE_GE_0.70_AND_MULTI_CHUNK_GE_2",
                "DESCRIPTION": (
                    "dense/hybrid agreement, dense top-1 score >= "
                    "0.70, and hybrid rank-1 has at least 2 "
                    "high-ranking chunks"
                ),
                "ACCEPT": lambda result:
                    result["DENSE_HYBRID_RANK1_AGREE"] == 1
                    and signal_value(
                        result,
                        "DENSE_RANK1_SCORE"
                    ) >= 0.70
                    and result["HYBRID_RANK1_TOP_CHUNK_COUNT"] >= 2
            }
        ]
    )

    return rules


def evaluate_rule(rule, results):
    true_accepts = []
    false_accepts = []
    true_abstentions = []
    false_rejects = []

    for result in results:
        supported = result["EXPECTED_SUPPORTED"] == "1"
        accepted = bool(
            rule["ACCEPT"](
                result
            )
        )

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

    top3_metrics = evaluate_safety_target(
        rule,
        results,
        3
    )
    top5_metrics = evaluate_safety_target(
        rule,
        results,
        5
    )

    metrics = {
        "RULE_ID": rule["RULE_ID"],
        "DESCRIPTION": rule["DESCRIPTION"],
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
            rule,
            near_domain
        ),
        "OUT_OF_SCOPE_ABSTAIN_RATE": abstain_rate(
            rule,
            out_of_scope
        ),
        "FALSE_ACCEPT_QUERY_IDS": ";".join(
            result["QUERY_ID"]
            for result in false_accepts
        ),
        "FALSE_REJECT_QUERY_IDS": ";".join(
            result["QUERY_ID"]
            for result in false_rejects
        )
    }

    metrics.update(
        top3_metrics
    )
    metrics.update(
        top5_metrics
    )

    return metrics


def abstain_rate(rule, results):
    if not results:
        return 0.0

    abstained = sum(
        1
        for result in results
        if not rule["ACCEPT"](
            result
        )
    )

    return abstained / len(results)


def evaluate_safety_target(rule, results, depth):
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
        if rule["ACCEPT"](
            result
        )
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
        if not rule["ACCEPT"](
            result
        )
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

    prefix = f"TOP{depth}"

    return {
        f"SAFE_ACCEPTS_{prefix}": len(
            safe_accepts
        ),
        f"UNSAFE_ACCEPTS_{prefix}": len(
            unsafe_accepts
        ),
        f"FALSE_REJECTS_SAFE_{prefix}": len(
            false_rejects
        ),
        f"ACCEPTED_ANSWER_PRECISION_{prefix}": (
            len(safe_accepts) / accepted_total
            if accepted_total
            else 0.0
        ),
        f"SAFE_ANSWER_RECALL_{prefix}": (
            len(safe_accepts) / safe_total
            if safe_total
            else 0.0
        ),
        f"COVERAGE_{prefix}": (
            accepted_total / total
            if total
            else 0.0
        ),
        f"UNSAFE_ACCEPT_QUERY_IDS_{prefix}": ";".join(
            result["QUERY_ID"]
            for result in unsafe_accepts
        ),
        f"FALSE_REJECT_SAFE_QUERY_IDS_{prefix}": ";".join(
            result["QUERY_ID"]
            for result in false_rejects
        )
    }


def format_float(value, digits=4):
    if value is None:
        return ""

    return f"{float(value):.{digits}f}"


def print_signal_results(results):
    print()
    print("=" * 90)
    print("PER-QUERY ABSTENTION SIGNALS")
    print("=" * 90)
    print(
        "QUERY_ID,"
        "EXPECTED_SUPPORTED,"
        "EXPECTED_DOCUMENT_ID,"
        "CATEGORY,"
        "EXPECTED_RANK,"
        "DENSE_RANK1_DOCUMENT_ID,"
        "DENSE_RANK1_SCORE,"
        "DENSE_RANK1_RANK2_MARGIN,"
        "HYBRID_RANK1_DOCUMENT_ID,"
        "HYBRID_RANK1_SCORE,"
        "HYBRID_RANK1_RANK2_MARGIN,"
        "DENSE_HYBRID_RANK1_AGREE,"
        "DENSE_RANK1_TOP_CHUNK_COUNT,"
        "HYBRID_RANK1_TOP_CHUNK_COUNT,"
        "HYBRID_TOP5_DOCUMENTS,"
        "HYBRID_TOP1_CORRECT,"
        "HYBRID_TOP3_CORRECT,"
        "HYBRID_TOP5_CORRECT,"
        "SAFE_TO_ANSWER_TOP3,"
        "SAFE_TO_ANSWER_TOP5,"
        "EMBEDDING_MS,"
        "DENSE_HANA_MS,"
        "HYBRID_FUSION_MS"
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
            f"{format_float(result['DENSE_RANK1_RANK2_MARGIN'])},"
            f"{result['HYBRID_RANK1_DOCUMENT_ID']},"
            f"{format_float(result['HYBRID_RANK1_SCORE'])},"
            f"{format_float(result['HYBRID_RANK1_RANK2_MARGIN'])},"
            f"{result['DENSE_HYBRID_RANK1_AGREE']},"
            f"{result['DENSE_RANK1_TOP_CHUNK_COUNT']},"
            f"{result['HYBRID_RANK1_TOP_CHUNK_COUNT']},"
            f"{result['HYBRID_TOP5_DOCUMENTS']},"
            f"{result['HYBRID_TOP1_CORRECT']},"
            f"{result['HYBRID_TOP3_CORRECT']},"
            f"{result['HYBRID_TOP5_CORRECT']},"
            f"{bool_as_int(is_safe_to_answer(result, 3))},"
            f"{bool_as_int(is_safe_to_answer(result, 5))},"
            f"{format_float(result['EMBEDDING_MS'], 2)},"
            f"{format_float(result['DENSE_HANA_MS'], 2)},"
            f"{format_float(result['HYBRID_FUSION_MS'], 2)}"
        )


def print_rule_results(rule_results):
    print()
    print("=" * 90)
    print("CANDIDATE ABSTENTION RULE METRICS")
    print("=" * 90)
    print(
        "RULE_ID,"
        "DESCRIPTION,"
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
        "FALSE_REJECT_QUERY_IDS,"
        "SAFE_ACCEPTS_TOP3,"
        "UNSAFE_ACCEPTS_TOP3,"
        "FALSE_REJECTS_SAFE_TOP3,"
        "ACCEPTED_ANSWER_PRECISION_TOP3,"
        "SAFE_ANSWER_RECALL_TOP3,"
        "COVERAGE_TOP3,"
        "UNSAFE_ACCEPT_QUERY_IDS_TOP3,"
        "FALSE_REJECT_SAFE_QUERY_IDS_TOP3,"
        "SAFE_ACCEPTS_TOP5,"
        "UNSAFE_ACCEPTS_TOP5,"
        "FALSE_REJECTS_SAFE_TOP5,"
        "ACCEPTED_ANSWER_PRECISION_TOP5,"
        "SAFE_ANSWER_RECALL_TOP5,"
        "COVERAGE_TOP5,"
        "UNSAFE_ACCEPT_QUERY_IDS_TOP5,"
        "FALSE_REJECT_SAFE_QUERY_IDS_TOP5"
    )

    for result in rule_results:
        print(
            f"{result['RULE_ID']},"
            f"\"{result['DESCRIPTION']}\","
            f"{result['TRUE_ACCEPTS']},"
            f"{result['FALSE_ACCEPTS']},"
            f"{result['TRUE_ABSTENTIONS']},"
            f"{result['FALSE_REJECTS']},"
            f"{format_float(result['ACCEPT_PRECISION'])},"
            f"{format_float(result['SUPPORTED_ACCEPT_RECALL'])},"
            f"{format_float(result['UNSUPPORTED_ABSTAIN_RATE'])},"
            f"{format_float(result['NEAR_DOMAIN_ABSTAIN_RATE'])},"
            f"{format_float(result['OUT_OF_SCOPE_ABSTAIN_RATE'])},"
            f"{result['FALSE_ACCEPT_QUERY_IDS']},"
            f"{result['FALSE_REJECT_QUERY_IDS']},"
            f"{result['SAFE_ACCEPTS_TOP3']},"
            f"{result['UNSAFE_ACCEPTS_TOP3']},"
            f"{result['FALSE_REJECTS_SAFE_TOP3']},"
            f"{format_float(result['ACCEPTED_ANSWER_PRECISION_TOP3'])},"
            f"{format_float(result['SAFE_ANSWER_RECALL_TOP3'])},"
            f"{format_float(result['COVERAGE_TOP3'])},"
            f"{result['UNSAFE_ACCEPT_QUERY_IDS_TOP3']},"
            f"{result['FALSE_REJECT_SAFE_QUERY_IDS_TOP3']},"
            f"{result['SAFE_ACCEPTS_TOP5']},"
            f"{result['UNSAFE_ACCEPTS_TOP5']},"
            f"{result['FALSE_REJECTS_SAFE_TOP5']},"
            f"{format_float(result['ACCEPTED_ANSWER_PRECISION_TOP5'])},"
            f"{format_float(result['SAFE_ANSWER_RECALL_TOP5'])},"
            f"{format_float(result['COVERAGE_TOP5'])},"
            f"{result['UNSAFE_ACCEPT_QUERY_IDS_TOP5']},"
            f"{result['FALSE_REJECT_SAFE_QUERY_IDS_TOP5']}"
        )


def main():
    print("SAP BTP Documentation Assistant")
    print("Version 2 Abstention Calibration")
    print("=" * 90)
    print(f"Calibration file: {CALIBRATION_FILE}")
    print(
        "Selected retrieval: full dense ranking + full "
        "BM25-style lexical ranking + RRF"
    )
    print("Reranker: none")
    print(f"RRF k: {RRF_K}")
    print(
        "High-ranking chunk support window: "
        f"{HIGH_RANKING_CHUNK_WINDOW}"
    )
    print(
        "This script is read-only to HANA and does not modify "
        "production app.py."
    )

    queries = load_queries()
    corpus_chunks, corpus_hana_ms = fetch_corpus_chunks()
    bm25_index = build_bm25_index(
        corpus_chunks
    )

    print(
        f"Corpus chunks loaded: {len(corpus_chunks)} "
        f"({corpus_hana_ms:.2f} ms one-time read)"
    )
    print(f"Questions: {len(queries)}")

    results = [
        evaluate_question(
            item,
            corpus_chunks,
            bm25_index
        )
        for item in queries
    ]

    rules = candidate_rules()
    rule_results = [
        evaluate_rule(
            rule,
            results
        )
        for rule in rules
    ]

    print_signal_results(
        results
    )
    print_rule_results(
        rule_results
    )

    print()
    print("=" * 90)
    print("NOTE")
    print("=" * 90)
    print(
        "These are calibration signals and candidate rules only. "
        "No production abstention threshold is selected or implemented."
    )


if __name__ == "__main__":
    main()
