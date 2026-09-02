import csv
import sys

from scripts.evaluate_rag_development_v2 import (
    build_bm25_index,
    evaluate_question,
    fetch_corpus_chunks,
    format_result_row,
    load_development_queries
)


PRIMARY_RESULTS_FILE = "data/rag_development_primary_results_v2.csv"
EXPECTED_PROVIDER_ERROR_IDS = (
    "RAGDEV008",
    "RAGDEV009",
    "RAGDEV011",
    "RAGDEV012",
    "RAGDEV013",
    "RAGDEV014",
    "RAGDEV015",
    "RAGDEV016",
    "RAGDEV019"
)


def read_primary_results(path=PRIMARY_RESULTS_FILE):
    with open(
        path,
        newline="",
        encoding="utf-8"
    ) as file:
        return list(
            csv.DictReader(
                file
            )
        )


def select_provider_error_rows(primary_rows):
    return [
        row
        for row in primary_rows
        if row.get(
            "OUTCOME",
            ""
        ).strip()
        == "PROVIDER_ERROR"
    ]


def selected_query_ids(rows):
    return tuple(
        row.get(
            "QUERY_ID",
            ""
        ).strip()
        for row in rows
    )


def validate_provider_error_selection(rows):
    actual_ids = selected_query_ids(
        rows
    )

    if actual_ids != EXPECTED_PROVIDER_ERROR_IDS:
        raise ValueError(
            "Primary provider-error retry selection does not match the pre-registered query IDs."
        )


def load_retry_questions(development_rows, retry_ids=EXPECTED_PROVIDER_ERROR_IDS):
    by_query_id = {
        row["QUERY_ID"]: row
        for row in development_rows
    }
    missing_ids = [
        query_id
        for query_id in retry_ids
        if query_id not in by_query_id
    ]

    if missing_ids:
        raise ValueError(
            "Retry query IDs are missing from the frozen RAG development dataset: "
            + ", ".join(
                missing_ids
            )
        )

    return [
        by_query_id[query_id]
        for query_id in retry_ids
    ]


def prepare_retry_questions(primary_path=PRIMARY_RESULTS_FILE):
    primary_rows = read_primary_results(
        primary_path
    )
    provider_error_rows = select_provider_error_rows(
        primary_rows
    )
    validate_provider_error_selection(
        provider_error_rows
    )

    return load_retry_questions(
        load_development_queries(),
        selected_query_ids(
            provider_error_rows
        )
    )


def run_retry():
    retry_questions = prepare_retry_questions()
    corpus_chunks, corpus_read_ms = fetch_corpus_chunks()
    bm25_index = build_bm25_index(
        corpus_chunks
    )

    return [
        evaluate_question(
            item,
            corpus_chunks,
            bm25_index
        )
        for item in retry_questions
    ]


def write_results(results, output=sys.stdout):
    if not results:
        return

    fieldnames = list(
        format_result_row(
            results[0]
        ).keys()
    )
    writer = csv.DictWriter(
        output,
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


def main():
    write_results(
        run_retry()
    )


if __name__ == "__main__":
    main()
