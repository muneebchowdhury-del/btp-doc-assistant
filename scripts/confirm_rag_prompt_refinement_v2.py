import ast
import csv
import sys
import time
from typing import Any, Callable

from llm_provider import generate_grounded_answer
from scripts.rag_generation_outcomes_v2 import classify_provider_answer


PRIMARY_RESULTS_FILE = "data/rag_development_primary_results_v2.csv"
PROVIDER_REQUEST_SPACING_SECONDS = 15.0
EXPECTED_CONFIRMATION_QUERY_IDS = (
    "RAGDEV001",
    "RAGDEV002",
    "RAGDEV003",
    "RAGDEV004",
    "RAGDEV005",
    "RAGDEV006",
    "RAGDEV007",
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
CONFIRMATION_FIELDNAMES = (
    "QUERY_ID",
    "QUESTION",
    "PRIMARY_CONTEXT_DOCUMENT_IDS",
    "CONTEXTS",
    "CONFIRMATION_OUTCOME",
    "CONFIRMATION_GEMINI_ANSWER_OR_REFUSAL",
    "CONFIRMATION_PROVIDER_ERROR",
    "CONFIRMATION_GENERATION_MS"
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


def selected_query_ids(rows):
    return tuple(
        row.get(
            "QUERY_ID",
            ""
        ).strip()
        for row in rows
    )


def select_confirmation_rows(primary_rows):
    return [
        row
        for row in primary_rows
        if row.get(
            "ACCEPT_DECISION",
            ""
        ).strip()
        == "ACCEPT"
    ]


def validate_unique_query_ids(rows):
    query_ids = selected_query_ids(
        rows
    )

    if len(
        query_ids
    ) != len(
        set(
            query_ids
        )
    ):
        raise ValueError(
            "Primary confirmation selection contains duplicate QUERY_ID values."
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


def validate_confirmation_selection(rows):
    validate_unique_query_ids(
        rows
    )
    actual_ids = selected_query_ids(
        rows
    )

    if actual_ids != EXPECTED_CONFIRMATION_QUERY_IDS:
        raise ValueError(
            "Prompt-refinement confirmation selection does not match the pre-registered accepted primary query IDs."
        )

    if "RAGDEV019" not in actual_ids:
        raise ValueError(
            "Prompt-refinement confirmation selection must include RAGDEV019."
        )

    for row in rows:
        query_id = row.get(
            "QUERY_ID",
            ""
        ).strip()
        question = row.get(
            "QUESTION",
            ""
        ).strip()

        if not question:
            raise ValueError(
                f"Primary QUESTION field is required for {query_id}."
            )

        parse_primary_contexts(
            row
        )


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


def confirm_primary_row(
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
        "PRIMARY_CONTEXT_DOCUMENT_IDS": context_document_ids(
            contexts
        ),
        "CONTEXTS": repr(
            contexts
        ),
        "CONFIRMATION_OUTCOME": outcome,
        "CONFIRMATION_GEMINI_ANSWER_OR_REFUSAL": answer,
        "CONFIRMATION_PROVIDER_ERROR": provider_error,
        "CONFIRMATION_GENERATION_MS": generation_ms
    }


def prepare_confirmation_rows(primary_path=PRIMARY_RESULTS_FILE):
    primary_rows = read_primary_results(
        primary_path
    )
    confirmation_rows = select_confirmation_rows(
        primary_rows
    )
    validate_confirmation_selection(
        confirmation_rows
    )
    return confirmation_rows


def run_confirmation(
    primary_path=PRIMARY_RESULTS_FILE,
    answer_provider: Callable[[str, list[dict[str, Any]]], str] = generate_grounded_answer,
    sleep_func: Callable[[float], None] = time.sleep
):
    rows = prepare_confirmation_rows(
        primary_path
    )
    results = []

    for index, row in enumerate(
        rows
    ):
        if index > 0:
            sleep_func(
                PROVIDER_REQUEST_SPACING_SECONDS
            )

        results.append(
            confirm_primary_row(
                row,
                answer_provider=answer_provider
            )
        )

    return results


def format_result_row(result):
    row = dict(
        result
    )
    row["CONFIRMATION_GENERATION_MS"] = f"{float(row['CONFIRMATION_GENERATION_MS']):.2f}"
    return row


def write_results(results, output=sys.stdout):
    writer = csv.DictWriter(
        output,
        fieldnames=CONFIRMATION_FIELDNAMES,
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
        run_confirmation()
    )


if __name__ == "__main__":
    main()
