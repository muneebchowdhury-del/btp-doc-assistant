import argparse
import csv
import sys


PRIMARY_RESULTS_FILE = "data/rag_development_primary_results_v2.csv"
DEFAULT_RETRY_RESULTS_FILE = "data/rag_development_provider_retry_results_v2.csv"
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

PRIMARY_FIELDS_TO_PRESERVE = (
    "QUERY_ID",
    "QUESTION",
    "EXPECTED_SUPPORTED",
    "EXPECTED_DOCUMENT_ID",
    "CATEGORY",
    "REFERENCE_FACT",
    "DENSE_RANK1_DOCUMENT_ID",
    "DENSE_RANK1_SCORE",
    "ACCEPT_DECISION",
    "HYBRID_TOP5_DOCUMENTS",
    "CONTEXT_DOCUMENT_IDS",
    "CONTEXTS",
    "OUTCOME",
    "GEMINI_ANSWER_OR_REFUSAL",
    "PROVIDER_ERROR",
    "EMBEDDING_MS",
    "DENSE_HANA_MS",
    "LEXICAL_MS",
    "HYBRID_FUSION_MS",
    "RETRIEVAL_MS",
    "GENERATION_MS",
    "TOTAL_END_TO_END_MS"
)

MANUAL_SCORE_FIELDS = (
    "GROUNDEDNESS",
    "ANSWER_CORRECTNESS",
    "CITATION_CORRECTNESS",
    "HALLUCINATION",
    "EVIDENCE_BASED_REFUSAL",
    "CONCISION",
    "EVALUATOR_NOTES",
    "SCORING_STATUS"
)

OUTPUT_FIELDS = (
    "EVIDENCE_SOURCE",
    *PRIMARY_FIELDS_TO_PRESERVE,
    "PRIMARY_OUTCOME",
    "PRIMARY_GEMINI_ANSWER_OR_REFUSAL",
    "PRIMARY_PROVIDER_ERROR",
    "SECONDARY_RETRY_OUTCOME",
    "SECONDARY_RETRY_GEMINI_ANSWER_OR_REFUSAL",
    "SECONDARY_RETRY_PROVIDER_ERROR",
    "SECONDARY_RETRY_GENERATION_MS",
    "PIPELINE_DECISION_ASSESSMENT",
    "GENERATION_OBSERVABILITY",
    "EXPECTED_DOC_IN_CONTEXT",
    "EXPECTED_DOC_CONTEXT_RANK",
    *MANUAL_SCORE_FIELDS
)


def read_csv_rows(path):
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


def write_csv_rows(rows, output):
    writer = csv.DictWriter(
        output,
        fieldnames=OUTPUT_FIELDS,
        lineterminator="\n"
    )
    writer.writeheader()
    writer.writerows(
        rows
    )


def context_document_ids(row):
    return [
        item.strip()
        for item in row.get(
            "CONTEXT_DOCUMENT_IDS",
            ""
        ).split(
            ";"
        )
        if item.strip()
    ]


def expected_doc_context_diagnostics(row):
    expected_supported = row.get(
        "EXPECTED_SUPPORTED",
        ""
    ).strip()
    expected_document = row.get(
        "EXPECTED_DOCUMENT_ID",
        ""
    ).strip()

    if (
        expected_supported != "1"
        or not expected_document
    ):
        return (
            "",
            ""
        )

    document_ids = context_document_ids(
        row
    )

    if expected_document not in document_ids:
        return (
            "0",
            ""
        )

    return (
        "1",
        str(
            document_ids.index(
                expected_document
            )
            + 1
        )
    )


def pipeline_decision_assessment(row):
    expected_supported = row.get(
        "EXPECTED_SUPPORTED",
        ""
    ).strip()
    accept_decision = row.get(
        "ACCEPT_DECISION",
        ""
    ).strip()

    if expected_supported not in {
        "0",
        "1"
    }:
        return "NOT_ASSESSED"

    if accept_decision == "ACCEPT":
        return (
            "CORRECT_ACCEPT"
            if expected_supported == "1"
            else "INCORRECT_ACCEPT"
        )

    if accept_decision == "ABSTAIN":
        return (
            "CORRECT_ABSTAIN"
            if expected_supported == "0"
            else "INCORRECT_ABSTAIN"
        )

    return "NOT_ASSESSED"


def generation_observability(outcome):
    clean_outcome = str(
        outcome or ""
    ).strip()

    if clean_outcome == "PIPELINE_ABSTAIN":
        return "NOT_CALLED"

    if clean_outcome == "PROVIDER_ERROR":
        return "PROVIDER_ERROR"

    if clean_outcome in {
        "GENERATED_ANSWER",
        "LLM_REFUSAL"
    }:
        return "OBSERVED"

    return "NOT_CALLED"


def empty_manual_scores():
    return {
        "GROUNDEDNESS": "",
        "ANSWER_CORRECTNESS": "",
        "CITATION_CORRECTNESS": "",
        "HALLUCINATION": "",
        "EVIDENCE_BASED_REFUSAL": "",
        "CONCISION": "",
        "EVALUATOR_NOTES": "",
        "SCORING_STATUS": "UNSCORED"
    }


def primary_scoring_row(primary_row):
    expected_doc_in_context, expected_doc_context_rank = (
        expected_doc_context_diagnostics(
            primary_row
        )
    )
    output_row = {
        field: primary_row.get(
            field,
            ""
        )
        for field in PRIMARY_FIELDS_TO_PRESERVE
    }
    outcome = primary_row.get(
        "OUTCOME",
        ""
    ).strip()
    output_row.update(
        {
            "EVIDENCE_SOURCE": "PRIMARY",
            "PRIMARY_OUTCOME": outcome,
            "PRIMARY_GEMINI_ANSWER_OR_REFUSAL": primary_row.get(
                "GEMINI_ANSWER_OR_REFUSAL",
                ""
            ),
            "PRIMARY_PROVIDER_ERROR": primary_row.get(
                "PROVIDER_ERROR",
                ""
            ),
            "SECONDARY_RETRY_OUTCOME": "",
            "SECONDARY_RETRY_GEMINI_ANSWER_OR_REFUSAL": "",
            "SECONDARY_RETRY_PROVIDER_ERROR": "",
            "SECONDARY_RETRY_GENERATION_MS": "",
            "PIPELINE_DECISION_ASSESSMENT": pipeline_decision_assessment(
                primary_row
            ),
            "GENERATION_OBSERVABILITY": generation_observability(
                outcome
            ),
            "EXPECTED_DOC_IN_CONTEXT": expected_doc_in_context,
            "EXPECTED_DOC_CONTEXT_RANK": expected_doc_context_rank
        }
    )
    output_row.update(
        empty_manual_scores()
    )
    return output_row


def validate_retry_rows(retry_rows):
    actual_ids = tuple(
        row.get(
            "QUERY_ID",
            ""
        ).strip()
        for row in retry_rows
    )

    if actual_ids != EXPECTED_PROVIDER_ERROR_IDS:
        raise ValueError(
            "Secondary retry file does not contain exactly the pre-registered provider-error query IDs."
        )


def retry_scoring_row(retry_row, primary_by_query_id):
    query_id = retry_row.get(
        "QUERY_ID",
        ""
    ).strip()
    primary_row = primary_by_query_id[query_id]
    expected_doc_in_context, expected_doc_context_rank = (
        expected_doc_context_diagnostics(
            primary_row
        )
    )
    retry_outcome = retry_row.get(
        "RETRY_OUTCOME",
        ""
    ).strip()
    output_row = {
        field: primary_row.get(
            field,
            ""
        )
        for field in PRIMARY_FIELDS_TO_PRESERVE
    }
    output_row.update(
        {
            "EVIDENCE_SOURCE": "SECONDARY_RETRY",
            "PRIMARY_OUTCOME": primary_row.get(
                "OUTCOME",
                ""
            ).strip(),
            "PRIMARY_GEMINI_ANSWER_OR_REFUSAL": primary_row.get(
                "GEMINI_ANSWER_OR_REFUSAL",
                ""
            ),
            "PRIMARY_PROVIDER_ERROR": primary_row.get(
                "PROVIDER_ERROR",
                ""
            ),
            "SECONDARY_RETRY_OUTCOME": retry_outcome,
            "SECONDARY_RETRY_GEMINI_ANSWER_OR_REFUSAL": retry_row.get(
                "RETRY_GEMINI_ANSWER_OR_REFUSAL",
                ""
            ),
            "SECONDARY_RETRY_PROVIDER_ERROR": retry_row.get(
                "RETRY_PROVIDER_ERROR",
                ""
            ),
            "SECONDARY_RETRY_GENERATION_MS": retry_row.get(
                "RETRY_GENERATION_MS",
                ""
            ),
            "PIPELINE_DECISION_ASSESSMENT": pipeline_decision_assessment(
                primary_row
            ),
            "GENERATION_OBSERVABILITY": generation_observability(
                retry_outcome
            ),
            "EXPECTED_DOC_IN_CONTEXT": expected_doc_in_context,
            "EXPECTED_DOC_CONTEXT_RANK": expected_doc_context_rank
        }
    )
    output_row.update(
        empty_manual_scores()
    )
    return output_row


def prepare_scoring_rows(primary_path, retry_path=None):
    primary_rows = read_csv_rows(
        primary_path
    )
    rows = [
        primary_scoring_row(
            row
        )
        for row in primary_rows
    ]

    if retry_path:
        retry_rows = read_csv_rows(
            retry_path
        )
        validate_retry_rows(
            retry_rows
        )
        primary_by_query_id = {
            row["QUERY_ID"]: row
            for row in primary_rows
        }
        rows.extend(
            retry_scoring_row(
                row,
                primary_by_query_id
            )
            for row in retry_rows
        )

    return rows


def parse_args():
    parser = argparse.ArgumentParser(
        description="Prepare manual scoring rows for V2 RAG development evidence."
    )
    parser.add_argument(
        "--primary",
        default=PRIMARY_RESULTS_FILE
    )
    parser.add_argument(
        "--retry",
        default=None
    )
    parser.add_argument(
        "--output",
        default=None
    )
    return parser.parse_args()


def main():
    args = parse_args()
    rows = prepare_scoring_rows(
        args.primary,
        args.retry
    )

    if args.output:
        with open(
            args.output,
            "w",
            newline="",
            encoding="utf-8"
        ) as file:
            write_csv_rows(
                rows,
                file
            )
    else:
        write_csv_rows(
            rows,
            sys.stdout
        )


if __name__ == "__main__":
    main()
