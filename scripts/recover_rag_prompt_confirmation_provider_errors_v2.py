import ast
import csv
import sys
import time
from typing import Any, Callable

from llm_provider import generate_grounded_answer
from scripts.rag_generation_outcomes_v2 import classify_provider_answer


CONFIRMATION_RESULTS_FILE = "data/rag_prompt_refinement_confirmation_results_v2.csv"
EXPECTED_RECOVERY_QUERY_IDS = (
    "RAGDEV015",
    "RAGDEV016",
    "RAGDEV019"
)
RECOVERY_FIELDNAMES = (
    "QUERY_ID",
    "QUESTION",
    "PRIMARY_CONTEXT_DOCUMENT_IDS",
    "CONTEXTS",
    "ORIGINAL_CONFIRMATION_OUTCOME",
    "RECOVERY_OUTCOME",
    "RECOVERY_GEMINI_ANSWER_OR_REFUSAL",
    "RECOVERY_PROVIDER_ERROR",
    "RECOVERY_GENERATION_MS"
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


def select_recovery_rows(confirmation_rows):
    expected_ids = set(
        EXPECTED_RECOVERY_QUERY_IDS
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


def validate_recovery_selection(rows):
    actual_ids = selected_query_ids(
        rows
    )

    if actual_ids != EXPECTED_RECOVERY_QUERY_IDS:
        raise ValueError(
            "Prompt-confirmation provider recovery selection does not match the pre-registered query IDs."
        )

    if len(
        actual_ids
    ) != len(
        set(
            actual_ids
        )
    ):
        raise ValueError(
            "Prompt-confirmation provider recovery selection contains duplicate QUERY_ID values."
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

        if (
            row.get(
                "CONFIRMATION_OUTCOME",
                ""
            ).strip()
            != "PROVIDER_ERROR"
        ):
            raise ValueError(
                f"Confirmation row {query_id} is not a PROVIDER_ERROR."
            )

        parse_confirmation_contexts(
            row
        )


def prepare_recovery_rows(confirmation_path=CONFIRMATION_RESULTS_FILE):
    confirmation_rows = read_confirmation_results(
        confirmation_path
    )
    recovery_rows = select_recovery_rows(
        confirmation_rows
    )
    validate_recovery_selection(
        recovery_rows
    )
    return recovery_rows


def recover_confirmation_row(
    row: dict[str, str],
    answer_provider: Callable[[str, list[dict[str, Any]]], str] = generate_grounded_answer
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
        "ORIGINAL_CONFIRMATION_OUTCOME": row.get(
            "CONFIRMATION_OUTCOME",
            ""
        ).strip(),
        "RECOVERY_OUTCOME": outcome,
        "RECOVERY_GEMINI_ANSWER_OR_REFUSAL": answer,
        "RECOVERY_PROVIDER_ERROR": provider_error,
        "RECOVERY_GENERATION_MS": generation_ms
    }


def run_recovery(
    confirmation_path=CONFIRMATION_RESULTS_FILE,
    answer_provider: Callable[[str, list[dict[str, Any]]], str] = generate_grounded_answer
):
    rows = prepare_recovery_rows(
        confirmation_path
    )

    return [
        recover_confirmation_row(
            row,
            answer_provider=answer_provider
        )
        for row in rows
    ]


def format_result_row(result):
    row = dict(
        result
    )
    row["RECOVERY_GENERATION_MS"] = f"{float(row['RECOVERY_GENERATION_MS']):.2f}"
    return row


def write_results(results, output=sys.stdout):
    writer = csv.DictWriter(
        output,
        fieldnames=RECOVERY_FIELDNAMES,
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
        run_recovery()
    )


if __name__ == "__main__":
    main()
