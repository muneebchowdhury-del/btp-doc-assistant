import ast
import csv
import sys
import time
from typing import Any, Callable

from llm_provider import generate_grounded_answer
from scripts.evaluate_rag_development_v2 import classify_provider_answer


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
RETRY_FIELDNAMES = (
    "QUERY_ID",
    "QUESTION",
    "PRIMARY_OUTCOME",
    "PRIMARY_CONTEXT_DOCUMENT_IDS",
    "RETRY_OUTCOME",
    "RETRY_GEMINI_ANSWER_OR_REFUSAL",
    "RETRY_PROVIDER_ERROR",
    "RETRY_GENERATION_MS"
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


def parse_primary_contexts(row):
    query_id = row.get(
        "QUERY_ID",
        ""
    ).strip()

    try:
        contexts = ast.literal_eval(
            row.get(
                "CONTEXTS",
                ""
            )
        )
    except (
        SyntaxError,
        ValueError
    ) as error:
        raise ValueError(
            f"Primary CONTEXTS field is malformed for {query_id}."
        ) from error

    if (
        not isinstance(
            contexts,
            list
        )
        or not contexts
        or not all(
            isinstance(
                context,
                dict
            )
            for context in contexts
        )
    ):
        raise ValueError(
            f"Primary CONTEXTS field must be a non-empty list of dictionaries for {query_id}."
        )

    return contexts


def context_document_ids(contexts):
    return ";".join(
        str(
            context.get(
                "document_id",
                ""
            )
        ).strip()
        for context in contexts
    )


def retry_primary_row(
    row: dict[str, str],
    answer_provider: Callable[[str, list[dict[str, Any]]], str] = generate_grounded_answer
) -> dict[str, Any]:
    question = row.get(
        "QUESTION",
        ""
    )
    contexts = parse_primary_contexts(
        row
    )
    generation_start = time.perf_counter()
    answer = ""
    provider_error = ""

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

    generation_ms = (
        time.perf_counter() - generation_start
    ) * 1000

    return {
        "QUERY_ID": row.get(
            "QUERY_ID",
            ""
        ).strip(),
        "QUESTION": question,
        "PRIMARY_OUTCOME": row.get(
            "OUTCOME",
            ""
        ).strip(),
        "PRIMARY_CONTEXT_DOCUMENT_IDS": context_document_ids(
            contexts
        ),
        "RETRY_OUTCOME": outcome,
        "RETRY_GEMINI_ANSWER_OR_REFUSAL": answer,
        "RETRY_PROVIDER_ERROR": provider_error,
        "RETRY_GENERATION_MS": generation_ms
    }


def prepare_retry_rows(primary_path=PRIMARY_RESULTS_FILE):
    primary_rows = read_primary_results(
        primary_path
    )
    provider_error_rows = select_provider_error_rows(
        primary_rows
    )
    validate_provider_error_selection(
        provider_error_rows
    )

    for row in provider_error_rows:
        parse_primary_contexts(
            row
        )

    return provider_error_rows


def run_retry(
    primary_path=PRIMARY_RESULTS_FILE,
    answer_provider: Callable[[str, list[dict[str, Any]]], str] = generate_grounded_answer
):
    return [
        retry_primary_row(
            row,
            answer_provider=answer_provider
        )
        for row in prepare_retry_rows(
            primary_path
        )
    ]


def format_result_row(result):
    row = dict(
        result
    )
    row["RETRY_GENERATION_MS"] = f"{float(row['RETRY_GENERATION_MS']):.2f}"
    return row


def write_results(results, output=sys.stdout):
    writer = csv.DictWriter(
        output,
        fieldnames=RETRY_FIELDNAMES,
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
