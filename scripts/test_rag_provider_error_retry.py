import csv
import os
import tempfile
import unittest
from unittest.mock import patch

import scripts.retry_rag_development_provider_errors_v2 as retry


def primary_row(query_id, outcome):
    return {
        "QUERY_ID": query_id,
        "OUTCOME": outcome
    }


class RAGProviderErrorRetryTests(unittest.TestCase):
    def test_only_primary_provider_error_rows_are_selected(self):
        rows = [
            primary_row(
                "RAGDEV001",
                "GENERATED_ANSWER"
            ),
            primary_row(
                "RAGDEV008",
                "PROVIDER_ERROR"
            ),
            primary_row(
                "RAGDEV010",
                "LLM_REFUSAL"
            ),
            primary_row(
                "RAGDEV011",
                " PROVIDER_ERROR "
            )
        ]

        selected = retry.select_provider_error_rows(
            rows
        )

        self.assertEqual(
            (
                "RAGDEV008",
                "RAGDEV011"
            ),
            retry.selected_query_ids(
                selected
            )
        )

    def test_exact_nine_expected_ids_are_selected_from_primary_file(self):
        rows = [
            primary_row(
                query_id,
                "PROVIDER_ERROR"
            )
            for query_id in retry.EXPECTED_PROVIDER_ERROR_IDS
        ]

        selected = retry.select_provider_error_rows(
            rows
        )

        retry.validate_provider_error_selection(
            selected
        )
        self.assertEqual(
            retry.EXPECTED_PROVIDER_ERROR_IDS,
            retry.selected_query_ids(
                selected
            )
        )

    def test_non_provider_error_questions_cannot_be_retried(self):
        rows = [
            primary_row(
                "RAGDEV008",
                "GENERATED_ANSWER"
            )
        ]

        with self.assertRaises(ValueError):
            retry.validate_provider_error_selection(
                retry.select_provider_error_rows(
                    rows
                )
            )

    def test_primary_file_is_not_mutated_when_preparing_retry_questions(self):
        primary_rows = [
            primary_row(
                query_id,
                "PROVIDER_ERROR"
            )
            for query_id in retry.EXPECTED_PROVIDER_ERROR_IDS
        ]
        development_rows = [
            {
                "QUERY_ID": query_id,
                "QUESTION": f"{query_id} question",
                "EXPECTED_SUPPORTED": "1",
                "EXPECTED_DOCUMENT_ID": "DOC001",
                "CATEGORY": "SUPPORTED",
                "REFERENCE_FACT": "Synthetic fact.",
                "NOTES": "Synthetic note."
            }
            for query_id in retry.EXPECTED_PROVIDER_ERROR_IDS
        ]

        with tempfile.NamedTemporaryFile(
            "w",
            newline="",
            encoding="utf-8",
            delete=False
        ) as file:
            path = file.name
            writer = csv.DictWriter(
                file,
                fieldnames=[
                    "QUERY_ID",
                    "OUTCOME"
                ],
                lineterminator="\n"
            )
            writer.writeheader()
            writer.writerows(
                primary_rows
            )

        try:
            with open(
                path,
                "rb"
            ) as file:
                before = file.read()

            with patch.object(
                retry,
                "load_development_queries",
                return_value=development_rows
            ):
                questions = retry.prepare_retry_questions(
                    path
                )

            with open(
                path,
                "rb"
            ) as file:
                after = file.read()

            self.assertEqual(
                before,
                after
            )
            self.assertEqual(
                list(
                    retry.EXPECTED_PROVIDER_ERROR_IDS
                ),
                [
                    row["QUERY_ID"]
                    for row in questions
                ]
            )
        finally:
            os.unlink(
                path
            )


if __name__ == "__main__":
    unittest.main()
