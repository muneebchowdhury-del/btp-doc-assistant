import ast
import csv
import sys
import time
from typing import Any, Callable

from llm_provider import GROQ_MODEL, generate_grounded_answer_groq
from scripts.rag_generation_outcomes_v2 import classify_provider_answer


CONFIRMATION_RESULTS_FILE = "data/rag_prompt_refinement_confirmation_results_v2.csv"
PROVIDER_REQUEST_SPACING_SECONDS = 30.0
PROVIDER_NAME = "GROQ"
EXPECTED_COMPARISON_QUERY_IDS = (
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
GROQ_COMPARISON_FIELDNAMES = (
    "QUERY_ID",
    "QUESTION",
    "PRIMARY_CONTEXT_DOCUMENT_IDS",
    "CONTEXTS",
    "PROVIDER",
    "MODEL",
    "GROQ_OUTCOME",
    "GROQ_ANSWER_OR_REFUSAL",
    "GROQ_PROVIDER_ERROR",
    "GROQ_GENERATION_MS"
)


def read_confirmation_results(path=CONFIRMATION_RESULTS_FILE):
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


def select_comparison_rows(confirmation_rows):
    expected_ids = set(
        EXPECTED_COMPARISON_QUERY_IDS
    )

    return [
        row
        for row in confirmation_rows
        if row.get(
            "QUERY_ID",
            ""
        ).strip()
        in expected_ids
    ]


def parse_confirmation_contexts(row):
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
            f"Confirmation CONTEXTS field is malformed for {query_id}."
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
            f"Confirmation CONTEXTS field must be a non-empty list of dictionaries for {query_id}."
        )

    return contexts


def validate_comparison_selection(rows):
    actual_ids = selected_query_ids(
        rows
    )

    if actual_ids != EXPECTED_COMPARISON_QUERY_IDS:
        raise ValueError(
            "Groq provider comparison selection does not match the pre-registered confirmation query IDs."
        )

    if len(
        actual_ids
    ) != len(
        set(
            actual_ids
        )
    ):
        raise ValueError(
            "Groq provider comparison selection contains duplicate QUERY_ID values."
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
                f"Confirmation QUESTION field is required for {query_id}."
            )

        parse_confirmation_contexts(
            row
        )


def prepare_comparison_rows(confirmation_path=CONFIRMATION_RESULTS_FILE):
    confirmation_rows = read_confirmation_results(
        confirmation_path
    )
    comparison_rows = select_comparison_rows(
        confirmation_rows
    )
    validate_comparison_selection(
        comparison_rows
    )
    return comparison_rows


def compare_row_with_groq(
    row: dict[str, str],
    answer_provider: Callable[[str, list[dict[str, Any]]], str] = generate_grounded_answer_groq
) -> dict[str, Any]:
    question = row.get(
        "QUESTION",
        ""
    )
    contexts = parse_confirmation_contexts(
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
        "PRIMARY_CONTEXT_DOCUMENT_IDS": row.get(
            "PRIMARY_CONTEXT_DOCUMENT_IDS",
            ""
        ).strip(),
        "CONTEXTS": repr(
            contexts
        ),
        "PROVIDER": PROVIDER_NAME,
        "MODEL": GROQ_MODEL,
        "GROQ_OUTCOME": outcome,
        "GROQ_ANSWER_OR_REFUSAL": answer,
        "GROQ_PROVIDER_ERROR": provider_error,
        "GROQ_GENERATION_MS": generation_ms
    }


def run_comparison(
    confirmation_path=CONFIRMATION_RESULTS_FILE,
    answer_provider: Callable[[str, list[dict[str, Any]]], str] = generate_grounded_answer_groq,
    sleep_func: Callable[[float], None] = time.sleep
):
    rows = prepare_comparison_rows(
        confirmation_path
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
            compare_row_with_groq(
                row,
                answer_provider=answer_provider
            )
        )

    return results


def format_result_row(result):
    row = dict(
        result
    )
    row["GROQ_GENERATION_MS"] = f"{float(row['GROQ_GENERATION_MS']):.2f}"
    return row


def write_results(results, output=sys.stdout):
    writer = csv.DictWriter(
        output,
        fieldnames=GROQ_COMPARISON_FIELDNAMES,
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
        run_comparison()
    )


if __name__ == "__main__":
    main()
