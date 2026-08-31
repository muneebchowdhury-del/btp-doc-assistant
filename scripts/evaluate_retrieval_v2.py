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

V1_REGRESSION_FILE = "data/evaluation_queries.csv"
V2_FOUNDATION_FILE = "data/evaluation_queries_v2_foundation.csv"

TABLE_NAME = "DOCUMENT_CHUNKS_V2"


def load_queries(path):
    with open(
        path,
        newline="",
        encoding="utf-8"
    ) as file:
        return list(csv.DictReader(file))


def retrieve_document_ranking(question):
    model = get_embedding_model()

    # -------------------------------------------------------------
    # Query embedding
    # -------------------------------------------------------------

    embedding_start = time.perf_counter()

    query_vector = list(
        model.query_embed(
            [question]
        )
    )[0]

    embedding_ms = (
        time.perf_counter() - embedding_start
    ) * 1000


    # -------------------------------------------------------------
    # HANA vector retrieval
    # -------------------------------------------------------------

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


    # -------------------------------------------------------------
    # Convert chunk ranking into unique document ranking
    # -------------------------------------------------------------

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


def evaluate_block(block_name, evaluation_file):
    queries = load_queries(
        evaluation_file
    )

    print()
    print("=" * 90)
    print(block_name)
    print("=" * 90)

    print(
        "Evaluation file:",
        evaluation_file
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
        "Evaluation queries:",
        len(queries)
    )

    print()


    results = []

    top1_correct = 0
    top3_correct = 0
    top5_correct = 0

    reciprocal_rank_sum = 0.0

    embedding_times = []
    hana_times = []


    for item in queries:

        query_id = item["QUERY_ID"]

        question = item["QUESTION"]

        expected_document = item[
            "EXPECTED_DOCUMENT_ID"
        ]


        (
            document_ranking,
            embedding_ms,
            hana_ms
        ) = retrieve_document_ranking(
            question
        )


        # ---------------------------------------------------------
        # Find rank of expected document
        # ---------------------------------------------------------

        expected_rank = None

        for rank, result in enumerate(
            document_ranking,
            start=1
        ):
            if (
                result["document_id"]
                == expected_document
            ):
                expected_rank = rank
                break


        if expected_rank is None:
            reciprocal_rank = 0.0

        else:
            reciprocal_rank = (
                1.0 / expected_rank
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


        top1_correct += int(top1)
        top3_correct += int(top3)
        top5_correct += int(top5)

        reciprocal_rank_sum += (
            reciprocal_rank
        )

        embedding_times.append(
            embedding_ms
        )

        hana_times.append(
            hana_ms
        )


        top_result = (
            document_ranking[0]
            if document_ranking
            else None
        )


        top5_documents = ";".join(
            result["document_id"]
            for result
            in document_ranking[:5]
        )


        results.append(
            {
                "QUERY_ID":
                    query_id,

                "QUESTION":
                    question,

                "EXPECTED_DOCUMENT_ID":
                    expected_document,

                "EXPECTED_RANK":
                    (
                        expected_rank
                        if expected_rank
                        is not None
                        else 0
                    ),

                "TOP_RESULT_DOCUMENT_ID":
                    (
                        top_result["document_id"]
                        if top_result
                        else ""
                    ),

                "TOP_RESULT_SCORE":
                    (
                        round(
                            top_result["score"],
                            4
                        )
                        if top_result
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
        )


        print(
            f"{query_id:<8} "
            f"Expected={expected_document:<7} "
            f"Rank={str(expected_rank):<4} "
            f"Top={top_result['document_id'] if top_result else '-':<7} "
            f"Score="
            f"{top_result['score']:.4f} "
            f"Top5={top5_documents}"
            if top_result
            else
            f"{query_id:<8} No results"
        )


    # -------------------------------------------------------------
    # Aggregate metrics
    # -------------------------------------------------------------

    total = len(queries)

    top1_accuracy = (
        top1_correct / total
    )

    top3_accuracy = (
        top3_correct / total
    )

    top5_accuracy = (
        top5_correct / total
    )

    mrr = (
        reciprocal_rank_sum / total
    )

    mean_embedding_ms = (
        sum(embedding_times)
        / len(embedding_times)
    )

    mean_hana_ms = (
        sum(hana_times)
        / len(hana_times)
    )


    print()
    print("-" * 90)
    print("AGGREGATE RESULTS")
    print("-" * 90)

    print(
        f"Queries evaluated: {total}"
    )

    print(
        f"Top-1 Accuracy: "
        f"{top1_accuracy:.4f} "
        f"({top1_correct}/{total})"
    )

    print(
        f"Top-3 Accuracy: "
        f"{top3_accuracy:.4f} "
        f"({top3_correct}/{total})"
    )

    print(
        f"Top-5 Accuracy: "
        f"{top5_accuracy:.4f} "
        f"({top5_correct}/{total})"
    )

    print(
        f"MRR: {mrr:.4f}"
    )

    print(
        f"Mean Query Embedding Time: "
        f"{mean_embedding_ms:.2f} ms"
    )

    print(
        f"Mean HANA Retrieval Time: "
        f"{mean_hana_ms:.2f} ms"
    )

    print(
        f"Mean Search Processing Time: "
        f"{mean_embedding_ms + mean_hana_ms:.2f} ms"
    )


    # -------------------------------------------------------------
    # Print machine-readable results
    # -------------------------------------------------------------

    print()
    print("DETAILED RESULTS")
    print("-" * 90)
    print(
        "QUERY_ID,"
        "EXPECTED_DOCUMENT_ID,"
        "EXPECTED_RANK,"
        "TOP_RESULT_DOCUMENT_ID,"
        "TOP_RESULT_SCORE,"
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
            f"{result['EXPECTED_DOCUMENT_ID']},"
            f"{result['EXPECTED_RANK']},"
            f"{result['TOP_RESULT_DOCUMENT_ID']},"
            f"{result['TOP_RESULT_SCORE']},"
            f"{result['TOP5_DOCUMENTS']},"
            f"{result['TOP1_CORRECT']},"
            f"{result['TOP3_CORRECT']},"
            f"{result['TOP5_CORRECT']},"
            f"{result['RECIPROCAL_RANK']},"
            f"{result['EMBEDDING_MS']},"
            f"{result['HANA_QUERY_MS']}"
        )

    return results


def main():
    print()
    print("SAP BTP Documentation Assistant")
    print("Version 2 Retrieval Evaluation")
    print("=" * 90)
    print(
        "This script reads from DOCUMENT_CHUNKS_V2 only "
        "and does not write to HANA."
    )

    evaluate_block(
        "A. V1 Regression Set",
        V1_REGRESSION_FILE
    )

    evaluate_block(
        "B. V2 Foundation Coverage Set",
        V2_FOUNDATION_FILE
    )

    print()
    print("=" * 90)
    print("Evaluation complete. Blocks are reported separately.")
    print("=" * 90)


if __name__ == "__main__":
    main()
