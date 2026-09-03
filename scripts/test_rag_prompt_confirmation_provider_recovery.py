import csv
import inspect
from io import StringIO
import os
import tempfile
import unittest
from unittest.mock import Mock

import scripts.recover_rag_prompt_confirmation_provider_errors_v2 as recovery


def contexts_text(document_id="DOC001"):
    return repr(
        [
            {
                "document_id": document_id,
                "title": f"{document_id} title",
                "source_url": f"https://help.sap.com/docs/example/{document_id.lower()}",
                "chunk_text": f"{document_id} confirmation context",
                "retrieval_rank": 1
            }
        ]
    )


def confirmation_row(
    query_id,
    outcome="PROVIDER_ERROR",
    context_document_id="DOC001"
):
    return {
        "QUERY_ID": query_id,
        "QUESTION": f"{query_id} exact confirmation question?",
        "PRIMARY_CONTEXT_DOCUMENT_IDS": context_document_id,
        "CONTEXTS": contexts_text(
            context_document_id
        ),
        "CONFIRMATION_OUTCOME": outcome
    }


def expected_recovery_rows():
    return [
        confirmation_row(
            query_id
        )
        for query_id in recovery.EXPECTED_RECOVERY_QUERY_IDS
    ]


def write_confirmation_file(rows):
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
                "PRIMARY_CONTEXT_DOCUMENT_IDS",
                "CONTEXTS",
                "CONFIRMATION_OUTCOME"
            ],
            lineterminator="\n"
        )
        writer.writeheader()
        writer.writerows(
            rows
        )
        return file.name


class RAGPromptConfirmationProviderRecoveryTests(unittest.TestCase):
    def test_exactly_three_expected_ids_are_selected_in_order(self):
        rows = [
            confirmation_row(
                "RAGDEV001",
                "GENERATED_ANSWER"
            ),
            confirmation_row(
                "RAGDEV015"
            ),
            confirmation_row(
                "RAGDEV016"
            ),
            confirmation_row(
                "RAGDEV019"
            )
        ]

        selected = recovery.select_recovery_rows(
            rows
        )

        recovery.validate_recovery_selection(
            selected
        )
        self.assertEqual(
            recovery.EXPECTED_RECOVERY_QUERY_IDS,
            recovery.selected_query_ids(
                selected
            )
        )

    def test_rows_not_in_expected_set_are_excluded(self):
        rows = expected_recovery_rows() + [
            confirmation_row(
                "RAGDEV008"
            )
        ]

        selected = recovery.select_recovery_rows(
            rows
        )

        self.assertEqual(
            recovery.EXPECTED_RECOVERY_QUERY_IDS,
            recovery.selected_query_ids(
                selected
            )
        )

    def test_selected_rows_must_have_original_provider_error(self):
        rows = expected_recovery_rows()
        rows[1]["CONFIRMATION_OUTCOME"] = "GENERATED_ANSWER"

        with self.assertRaises(ValueError):
            recovery.validate_recovery_selection(
                rows
            )

    def test_exact_question_and_contexts_are_reused(self):
        row = confirmation_row(
            "RAGDEV015",
            context_document_id="DOC015"
        )
        provider = Mock(
            return_value="Grounded answer."
        )
        contexts = recovery.parse_confirmation_contexts(
            row
        )

        result = recovery.recover_confirmation_row(
            row,
            answer_provider=provider
        )

        provider.assert_called_once_with(
            "RAGDEV015 exact confirmation question?",
            contexts
        )
        self.assertEqual(
            contexts_text(
                "DOC015"
            ),
            result["CONTEXTS"]
        )
        self.assertEqual(
            "DOC015",
            result["PRIMARY_CONTEXT_DOCUMENT_IDS"]
        )

    def test_one_provider_call_per_row(self):
        path = write_confirmation_file(
            expected_recovery_rows()
        )
        provider = Mock(
            return_value="Grounded answer."
        )

        try:
            results = recovery.run_recovery(
                path,
                answer_provider=provider
            )
        finally:
            os.unlink(
                path
            )

        self.assertEqual(
            3,
            provider.call_count
        )
        self.assertEqual(
            3,
            len(
                results
            )
        )

    def test_provider_exception_remains_provider_error_without_retry_and_continues(self):
        path = write_confirmation_file(
            expected_recovery_rows()
        )
        calls = []

        def provider(question, contexts):
            calls.append(
                question
            )

            if len(
                calls
            ) == 2:
                raise RuntimeError(
                    "synthetic provider failure"
                )

            return "Grounded answer."

        try:
            results = recovery.run_recovery(
                path,
                answer_provider=provider
            )
        finally:
            os.unlink(
                path
            )

        self.assertEqual(
            3,
            len(
                calls
            )
        )
        self.assertEqual(
            "PROVIDER_ERROR",
            results[1]["RECOVERY_OUTCOME"]
        )
        self.assertIn(
            "synthetic provider failure",
            results[1]["RECOVERY_PROVIDER_ERROR"]
        )
        self.assertEqual(
            "GENERATED_ANSWER",
            results[2]["RECOVERY_OUTCOME"]
        )

    def test_existing_classifier_is_used_for_refusal(self):
        result = recovery.recover_confirmation_row(
            confirmation_row(
                "RAGDEV015"
            ),
            answer_provider=Mock(
                return_value="The available documentation is insufficient."
            )
        )

        self.assertEqual(
            "LLM_REFUSAL",
            result["RECOVERY_OUTCOME"]
        )

    def test_canonical_input_file_is_not_mutated(self):
        path = write_confirmation_file(
            expected_recovery_rows()
        )

        try:
            with open(
                path,
                "rb"
            ) as file:
                before = file.read()

            recovery.prepare_recovery_rows(
                path
            )

            with open(
                path,
                "rb"
            ) as file:
                after = file.read()
        finally:
            os.unlink(
                path
            )

        self.assertEqual(
            before,
            after
        )

    def test_no_retrieval_or_hana_modules_are_required(self):
        source = inspect.getsource(
            recovery
        )

        self.assertNotIn(
            "evaluate_rag_development_v2",
            source
        )
        self.assertNotIn(
            "evaluate_retrieval_variants_v2",
            source
        )
        self.assertNotIn(
            "fetch_dense_chunks",
            source
        )
        self.assertNotIn(
            "build_rag_contexts_from_hybrid_results",
            source
        )

    def test_expected_output_columns_are_produced(self):
        output = StringIO()
        recovery.write_results(
            [
                recovery.recover_confirmation_row(
                    confirmation_row(
                        "RAGDEV015"
                    ),
                    answer_provider=Mock(
                        return_value="Grounded answer."
                    )
                )
            ],
            output=output
        )

        header = output.getvalue().splitlines()[0].split(
            ","
        )
        self.assertEqual(
            list(
                recovery.RECOVERY_FIELDNAMES
            ),
            header
        )

    def test_malformed_contexts_fail_before_provider_call(self):
        row = confirmation_row(
            "RAGDEV015"
        )
        row["CONTEXTS"] = "{malformed"
        provider = Mock(
            return_value="should not be called"
        )

        with self.assertRaises(ValueError):
            recovery.recover_confirmation_row(
                row,
                answer_provider=provider
            )

        provider.assert_not_called()


if __name__ == "__main__":
    unittest.main()
