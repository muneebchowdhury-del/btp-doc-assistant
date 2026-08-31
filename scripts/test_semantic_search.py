import json
import os
import sys


PROJECT_ROOT = os.path.dirname(
    os.path.dirname(
        os.path.abspath(__file__)
    )
)

if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)


from app import (
    get_embedding_model,
    get_hana_connection
)


QUESTION = (
    "How do I bind my Cloud Foundry application "
    "to a service?"
)

TOP_K = 5


def vector_to_string(vector):
    return json.dumps(
        [float(value) for value in vector]
    )


def main():
    print("Question:")
    print(QUESTION)
    print()

    print("Generating query embedding...")

    model = get_embedding_model()

    query_vector = list(
        model.query_embed([QUESTION])
    )[0]

    print(
        "Query vector dimension:",
        len(query_vector)
    )

    connection = get_hana_connection()
    cursor = connection.cursor()

    try:
        sql = f"""
            SELECT TOP {TOP_K}
                "CHUNK_ID",
                "DOCUMENT_ID",
                "TITLE",
                "TOPIC",
                "SOURCE_URL",
                "CHUNK_TEXT",
                COSINE_SIMILARITY(
                    "EMBEDDING",
                    TO_REAL_VECTOR(?)
                ) AS "SCORE"
            FROM "DOCUMENT_CHUNKS"
            WHERE "EMBEDDING" IS NOT NULL
            ORDER BY "SCORE" DESC
        """

        cursor.execute(
            sql,
            (
                vector_to_string(
                    query_vector
                ),
            )
        )

        rows = cursor.fetchall()

        print()
        print(
            f"Top {TOP_K} semantic results:"
        )
        print("=" * 80)

        for rank, row in enumerate(
            rows,
            start=1
        ):
            (
                chunk_id,
                document_id,
                title,
                topic,
                source_url,
                chunk_text,
                score
            ) = row

            print()
            print(f"Rank: {rank}")
            print(
                f"Score: {float(score):.4f}"
            )
            print(
                f"Document: {document_id}"
            )
            print(
                f"Title: {title}"
            )
            print(
                f"Topic: {topic}"
            )
            print(
                f"Chunk ID: {chunk_id}"
            )
            print(
                f"Source: {source_url}"
            )
            print()
            print(
                chunk_text[:500]
            )
            print("-" * 80)

    finally:
        cursor.close()
        connection.close()


if __name__ == "__main__":
    main()