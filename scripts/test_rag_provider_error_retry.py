import csv
import os
import tempfile
import unittest
from unittest.mock import Mock, patch

import scripts.evaluate_rag_development_v2 as primary_harness
import scripts.retry_rag_development_provider_errors_v2 as retry


def contexts_text(document_id="DOC001"):
    return repr(
        [
            {
                "document_id": document_id,
                "title": f"{document_id} title",
                "source_url": f"https://help.sap.com/docs/example/{document_id.lower()}",
                "chunk_text": f"{document_id} primary context",
                "retrieval_rank": 1
            }
        ]
    )


def primary_row(query_id, outcome, context_document_id="DOC001"):
    return {
        "QUERY_ID": query_id,
        "QUESTION": f"{query_id} primary question?",
        "OUTCOME": outcome,
        "CONTEXTS": contexts_text(
            context_document_id
        )
    }


def write_primary_file(rows):
    with tempfile.NamedTemporaryFile(
        "w",
        newline="",
        encoding="utf-8",
        delete=False
    ) as file:
        writer = csv.DictWriter(
            file,
            fieldnames=[
                "QUERY_ID",
                "QUESTION",
                "OUTCOME",
                "CONTEXTS"
            ],
            lineterminator="\n"
        )
        writer.writeheader()
        writer.writerows(
            rows
        )
        return file.name


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

    def test_primary_non_provider_error_rows_are_rejected(self):
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

    def test_primary_contexts_are_parsed_and_reused_unchanged(self):
        provider = Mock(
            return_value="The available documentation is insufficient."
        )
        row = primary_row(
            "RAGDEV008",
            "PROVIDER_ERROR",
            "DOC010"
        )
        expected_contexts = retry.parse_primary_contexts(
            row
        )

        result = retry.retry_primary_row(
            row,
            answer_provider=provider
        )

        provider.assert_called_once_with(
            "RAGDEV008 primary question?",
            expected_contexts
        )
        self.assertEqual(
            "DOC010",
            result["PRIMARY_CONTEXT_DOCUMENT_IDS"]
        )
        self.assertEqual(
            "LLM_REFUSAL",
            result["RETRY_OUTCOME"]
        )

    def test_malformed_contexts_fail_before_provider_call(self):
        provider = Mock(
            return_value="should not be called"
        )
        row = primary_row(
            "RAGDEV008",
            "PROVIDER_ERROR"
        )
        row["CONTEXTS"] = "{malformed"

        with self.assertRaises(ValueError):
            retry.retry_primary_row(
                row,
                answer_provider=provider
            )

        provider.assert_not_called()

    def test_exactly_one_provider_call_occurs_per_selected_row(self):
        rows = [
            primary_row(
                query_id,
                "PROVIDER_ERROR"
            )
            for query_id in retry.EXPECTED_PROVIDER_ERROR_IDS
        ]
        path = write_primary_file(
            rows
        )
        provider = Mock(
            return_value="Grounded answer."
        )

        try:
            results = retry.run_retry(
                path,
                answer_provider=provider
            )
        finally:
            os.unlink(
                path
            )

        self.assertEqual(
            len(
                retry.EXPECTED_PROVIDER_ERROR_IDS
            ),
            provider.call_count
        )
        self.assertEqual(
            len(
                retry.EXPECTED_PROVIDER_ERROR_IDS
            ),
            len(
                results
            )
        )

    def test_no_retrieval_or_hana_functions_are_invoked(self):
        rows = [
            primary_row(
                query_id,
                "PROVIDER_ERROR"
            )
            for query_id in retry.EXPECTED_PROVIDER_ERROR_IDS
        ]
        path = write_primary_file(
            rows
        )
        provider = Mock(
            return_value="Grounded answer."
        )

        try:
            with patch.object(
                primary_harness,
                "fetch_corpus_chunks",
                side_effect=AssertionError(
                    "retrieval must not run"
                )
            ), patch.object(
                primary_harness,
                "fetch_dense_chunks",
                side_effect=AssertionError(
                    "HANA retrieval must not run"
                )
            ), patch.object(
                primary_harness,
                "bm25_rank",
                side_effect=AssertionError(
                    "BM25 must not run"
                )
            ), patch.object(
                primary_harness,
                "reciprocal_rank_fusion",
                side_effect=AssertionError(
                    "RRF must not run"
                )
            ), patch.object(
                primary_harness,
                "build_rag_contexts_from_hybrid_results",
                side_effect=AssertionError(
                    "context bridge must not run"
                )
            ), patch.object(
                primary_harness,
                "evaluate_question",
                side_effect=AssertionError(
                    "primary evaluator must not run"
                )
            ):
                retry.run_retry(
                    path,
                    answer_provider=provider
                )
        finally:
            os.unlink(
                path
            )

        self.assertEqual(
            len(
                retry.EXPECTED_PROVIDER_ERROR_IDS
            ),
            provider.call_count
        )

    def test_primary_file_is_not_mutated_when_preparing_retry_rows(self):
        path = write_primary_file(
            [
                primary_row(
                    query_id,
                    "PROVIDER_ERROR"
                )
                for query_id in retry.EXPECTED_PROVIDER_ERROR_IDS
            ]
        )

        try:
            with open(
                path,
                "rb"
            ) as file:
                before = file.read()

            rows = retry.prepare_retry_rows(
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
                retry.EXPECTED_PROVIDER_ERROR_IDS,
                retry.selected_query_ids(
                    rows
                )
            )
        finally:
            os.unlink(
                path
            )


if __name__ == "__main__":
    unittest.main()
