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


from app import (
    get_embedding_model,
    get_hana_connection,
    vector_to_string
)


MODEL_NAME = "BAAI/bge-small-en-v1.5"

CALIBRATION_FILE = "data/retrieval_calibration_v2.csv"

TABLE_NAME = "DOCUMENT_CHUNKS_V2"


def load_queries():
    with open(
        CALIBRATION_FILE,
        newline="",
        encoding="utf-8"
    ) as file:
        return list(csv.DictReader(file))


def is_supported(item):
    return item["EXPECTED_SUPPORTED"].strip() == "1"


def retrieve_document_ranking(question):
    model = get_embedding_model()

    embedding_start = time.perf_counter()

    query_vector = list(
        model.query_embed(
            [question]
        )
    )[0]

    embedding_ms = (
        time.perf_counter() - embedding_start
    ) * 1000

    connection = get_hana_connection()
    cursor = connection.cursor()

    try:
        hana_start = time.perf_counter()

        cursor.execute(
            f"""
            SELECT
                "DOCUMENT_ID",
                "TITLE",
                COSINE_SIMILARITY(
                    "EMBEDDING",
                    TO_REAL_VECTOR(?)
                ) AS "SCORE"
            FROM "{TABLE_NAME}"
            WHERE "EMBEDDING" IS NOT NULL
            ORDER BY "SCORE" DESC
            """,
            (
                vector_to_string(
                    query_vector
                ),
            )
        )

        rows = cursor.fetchall()

        hana_ms = (
            time.perf_counter() - hana_start
        ) * 1000

    finally:
        cursor.close()
        connection.close()

    document_ranking = []
    seen_documents = set()

    for row in rows:
        document_id = row[0]

        if document_id in seen_documents:
            continue

        seen_documents.add(
            document_id
        )

        document_ranking.append(
            {
                "document_id": document_id,
                "title": row[1],
                "score": float(row[2])
            }
        )

    return (
        document_ranking,
        embedding_ms,
        hana_ms
    )


def find_expected_rank(document_ranking, expected_document):
    if not expected_document:
        return None

    for rank, result in enumerate(
        document_ranking,
        start=1
    ):
        if result["document_id"] == expected_document:
            return rank

    return None


def summarize_supported(results):
    supported_results = [
        result
        for result in results
        if result["EXPECTED_SUPPORTED"] == "1"
    ]

    total = len(supported_results)

    top1_correct = sum(
        int(result["TOP1_CORRECT"])
        for result in supported_results
    )

    top3_correct = sum(
        int(result["TOP3_CORRECT"])
        for result in supported_results
    )

    top5_correct = sum(
        int(result["TOP5_CORRECT"])
        for result in supported_results
    )

    reciprocal_rank_sum = sum(
        float(result["RECIPROCAL_RANK"])
        for result in supported_results
    )

    print()
    print("=" * 90)
    print("SUPPORTED QUESTION METRICS")
    print("=" * 90)

    print(
        f"Supported questions evaluated: {total}"
    )

    print(
        f"Top-1 Accuracy: "
        f"{top1_correct / total:.4f} "
        f"({top1_correct}/{total})"
    )

    print(
        f"Top-3 Accuracy: "
        f"{top3_correct / total:.4f} "
        f"({top3_correct}/{total})"
    )

    print(
        f"Top-5 Accuracy: "
        f"{top5_correct / total:.4f} "
        f"({top5_correct}/{total})"
    )

    print(
        f"MRR: "
        f"{reciprocal_rank_sum / total:.4f}"
    )


def print_detailed_results(results):
    print()
    print("=" * 90)
    print("DETAILED CALIBRATION RESULTS")
    print("=" * 90)

    print(
        "QUERY_ID,"
        "EXPECTED_SUPPORTED,"
        "EXPECTED_DOCUMENT_ID,"
        "CATEGORY,"
        "EXPECTED_RANK,"
        "RANK1_DOCUMENT_ID,"
        "RANK1_SCORE,"
        "RANK2_DOCUMENT_ID,"
        "RANK2_SCORE,"
        "RANK1_RANK2_MARGIN,"
        "TOP5_DOCUMENTS,"
        "TOP1_CORRECT,"
        "TOP3_CORRECT,"
        "TOP5_CORRECT,"
        "RECIPROCAL_RANK,"
        "EMBEDDING_MS,"
        "HANA_QUERY_MS"
    )

    for result in results:
        print(
            f"{result['QUERY_ID']},"
            f"{result['EXPECTED_SUPPORTED']},"
            f"{result['EXPECTED_DOCUMENT_ID']},"
            f"{result['CATEGORY']},"
            f"{result['EXPECTED_RANK']},"
            f"{result['RANK1_DOCUMENT_ID']},"
            f"{result['RANK1_SCORE']},"
            f"{result['RANK2_DOCUMENT_ID']},"
            f"{result['RANK2_SCORE']},"
            f"{result['RANK1_RANK2_MARGIN']},"
            f"{result['TOP5_DOCUMENTS']},"
            f"{result['TOP1_CORRECT']},"
            f"{result['TOP3_CORRECT']},"
            f"{result['TOP5_CORRECT']},"
            f"{result['RECIPROCAL_RANK']},"
            f"{result['EMBEDDING_MS']},"
            f"{result['HANA_QUERY_MS']}"
        )


def main():
    queries = load_queries()

    print()
    print("SAP BTP Documentation Assistant")
    print("Version 2 Retrieval Calibration Baseline")
    print("=" * 90)

    print(
        "Calibration file:",
        CALIBRATION_FILE
    )

    print(
        "Target table:",
        TABLE_NAME
    )

    print(
        "Embedding model:",
        MODEL_NAME
    )

    print(
        "Questions:",
        len(queries)
    )

    print(
        "This script evaluates the existing vector-only baseline "
        "and does not write to HANA."
    )


    results = []

    for item in queries:
        query_id = item["QUERY_ID"]
        question = item["QUESTION"]
        expected_supported = item["EXPECTED_SUPPORTED"].strip()
        expected_document = item["EXPECTED_DOCUMENT_ID"].strip()
        category = item["CATEGORY"]

        (
            document_ranking,
            embedding_ms,
            hana_ms
        ) = retrieve_document_ranking(
            question
        )

        rank1 = (
            document_ranking[0]
            if len(document_ranking) >= 1
            else None
        )

        rank2 = (
            document_ranking[1]
            if len(document_ranking) >= 2
            else None
        )

        rank1_score = (
            rank1["score"]
            if rank1
            else None
        )

        rank2_score = (
            rank2["score"]
            if rank2
            else None
        )

        score_margin = (
            rank1_score - rank2_score
            if (
                rank1_score is not None
                and rank2_score is not None
            )
            else None
        )

        expected_rank = find_expected_rank(
            document_ranking,
            expected_document
        )

        if is_supported(item):
            reciprocal_rank = (
                1.0 / expected_rank
                if expected_rank is not None
                else 0.0
            )

            top1 = (
                expected_rank == 1
            )

            top3 = (
                expected_rank is not None
                and expected_rank <= 3
            )

            top5 = (
                expected_rank is not None
                and expected_rank <= 5
            )

        else:
            reciprocal_rank = 0.0
            top1 = False
            top3 = False
            top5 = False

        top5_documents = ";".join(
            result["document_id"]
            for result
            in document_ranking[:5]
        )

        result = {
            "QUERY_ID":
                query_id,

            "EXPECTED_SUPPORTED":
                expected_supported,

            "EXPECTED_DOCUMENT_ID":
                expected_document,

            "CATEGORY":
                category,

            "EXPECTED_RANK":
                (
                    expected_rank
                    if expected_rank is not None
                    else 0
                ),

            "RANK1_DOCUMENT_ID":
                (
                    rank1["document_id"]
                    if rank1
                    else ""
                ),

            "RANK1_SCORE":
                (
                    round(rank1_score, 4)
                    if rank1_score is not None
                    else ""
                ),

            "RANK2_DOCUMENT_ID":
                (
                    rank2["document_id"]
                    if rank2
                    else ""
                ),

            "RANK2_SCORE":
                (
                    round(rank2_score, 4)
                    if rank2_score is not None
                    else ""
                ),

            "RANK1_RANK2_MARGIN":
                (
                    round(score_margin, 4)
                    if score_margin is not None
                    else ""
                ),

            "TOP5_DOCUMENTS":
                top5_documents,

            "TOP1_CORRECT":
                int(top1),

            "TOP3_CORRECT":
                int(top3),

            "TOP5_CORRECT":
                int(top5),

            "RECIPROCAL_RANK":
                round(
                    reciprocal_rank,
                    4
                ),

            "EMBEDDING_MS":
                round(
                    embedding_ms,
                    2
                ),

            "HANA_QUERY_MS":
                round(
                    hana_ms,
                    2
                )
        }

        results.append(
            result
        )

        print(
            f"{query_id:<8} "
            f"Supported={expected_supported:<1} "
            f"Expected={expected_document or '-':<7} "
            f"Rank={result['EXPECTED_RANK']:<3} "
            f"Rank1={result['RANK1_DOCUMENT_ID'] or '-':<7} "
            f"Score1={result['RANK1_SCORE']} "
            f"Rank2={result['RANK2_DOCUMENT_ID'] or '-':<7} "
            f"Score2={result['RANK2_SCORE']} "
            f"Margin={result['RANK1_RANK2_MARGIN']} "
            f"Top5={top5_documents}"
        )

    summarize_supported(
        results
    )

    print_detailed_results(
        results
    )


if __name__ == "__main__":
    main()
