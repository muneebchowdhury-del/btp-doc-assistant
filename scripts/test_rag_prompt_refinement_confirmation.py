import csv
import inspect
from io import StringIO
import os
import tempfile
import unittest
from unittest.mock import Mock

import scripts.confirm_rag_prompt_refinement_v2 as confirm


def contexts_text(document_id="DOC001", rank=1):
    return repr(
        [
            {
                "document_id": document_id,
                "title": f"{document_id} title",
                "source_url": f"https://help.sap.com/docs/example/{document_id.lower()}",
                "chunk_text": f"{document_id} preserved primary context",
                "retrieval_rank": rank
            }
        ]
    )


def primary_row(query_id, accept_decision="ACCEPT", context_document_id="DOC001"):
    return {
        "QUERY_ID": query_id,
        "QUESTION": f"{query_id} exact primary question?",
        "ACCEPT_DECISION": accept_decision,
        "CONTEXTS": contexts_text(
            context_document_id
        )
    }


def accepted_primary_rows():
    return [
        primary_row(
            query_id
        )
        for query_id in confirm.EXPECTED_CONFIRMATION_QUERY_IDS
    ]


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
                "ACCEPT_DECISION",
                "CONTEXTS"
            ],
            lineterminator="\n"
        )
        writer.writeheader()
        writer.writerows(
            rows
        )
        return file.name


class RAGPromptRefinementConfirmationTests(unittest.TestCase):
    def test_exactly_16_canonical_accept_rows_are_selected(self):
        rows = accepted_primary_rows() + [
            primary_row(
                "RAGDEV010",
                "ABSTAIN"
            )
        ]

        selected = confirm.select_confirmation_rows(
            rows
        )

        confirm.validate_confirmation_selection(
            selected
        )
        self.assertEqual(
            confirm.EXPECTED_CONFIRMATION_QUERY_IDS,
            confirm.selected_query_ids(
                selected
            )
        )
        self.assertEqual(
            16,
            len(
                selected
            )
        )

    def test_ragdev019_is_included(self):
        selected = confirm.select_confirmation_rows(
            accepted_primary_rows()
        )

        self.assertIn(
            "RAGDEV019",
            confirm.selected_query_ids(
                selected
            )
        )

    def test_non_accepted_rows_are_excluded(self):
        rows = [
            primary_row(
                "RAGDEV001",
                "ACCEPT"
            ),
            primary_row(
                "RAGDEV010",
                "ABSTAIN"
            ),
            primary_row(
                "RAGDEV020",
                "PIPELINE_ABSTAIN"
            )
        ]

        selected = confirm.select_confirmation_rows(
            rows
        )

        self.assertEqual(
            (
                "RAGDEV001",
            ),
            confirm.selected_query_ids(
                selected
            )
        )

    def test_selection_validation_rejects_non_canonical_accept_set(self):
        with self.assertRaises(ValueError):
            confirm.validate_confirmation_selection(
                [
                    primary_row(
                        "RAGDEV001",
                        "ACCEPT"
                    )
                ]
            )

    def test_exact_primary_question_and_contexts_are_passed_to_provider(self):
        row = primary_row(
            "RAGDEV001",
            "ACCEPT",
            "DOC010"
        )
        provider = Mock(
            return_value="Grounded answer."
        )
        parsed_contexts = confirm.parse_primary_contexts(
            row
        )

        result = confirm.confirm_primary_row(
            row,
            answer_provider=provider
        )

        provider.assert_called_once_with(
            "RAGDEV001 exact primary question?",
            parsed_contexts
        )
        self.assertEqual(
            contexts_text(
                "DOC010"
            ),
            result["CONTEXTS"]
        )
        self.assertEqual(
            "DOC010",
            result["PRIMARY_CONTEXT_DOCUMENT_IDS"]
        )

    def test_no_retrieval_or_hana_modules_are_imported_by_confirmation_harness(self):
        source = inspect.getsource(
            confirm
        )

        self.assertNotIn(
            "evaluate_rag_development_v2",
            source
        )
        self.assertNotIn(
            "evaluate_retrieval_variants_v2",
            source
        )

    def test_one_provider_call_per_selected_row_and_pacing_between_calls(self):
        rows = accepted_primary_rows()
        path = write_primary_file(
            rows
        )
        provider = Mock(
            return_value="Grounded answer."
        )
        sleep_func = Mock()

        try:
            results = confirm.run_confirmation(
                path,
                answer_provider=provider,
                sleep_func=sleep_func
            )
        finally:
            os.unlink(
                path
            )

        self.assertEqual(
            16,
            provider.call_count
        )
        self.assertEqual(
            16,
            len(
                results
            )
        )
        self.assertEqual(
            15,
            sleep_func.call_count
        )
        self.assertTrue(
            all(
                call.args
                == (
                    confirm.PROVIDER_REQUEST_SPACING_SECONDS,
                )
                for call in sleep_func.call_args_list
            )
        )

    def test_no_sleep_before_first_request_or_after_last_request(self):
        path = write_primary_file(
            accepted_primary_rows()
        )
        events = []

        def provider(question, contexts):
            events.append(
                (
                    "provider",
                    question
                )
            )
            return "Grounded answer."

        def sleep_func(seconds):
            events.append(
                (
                    "sleep",
                    seconds
                )
            )

        try:
            confirm.run_confirmation(
                path,
                answer_provider=provider,
                sleep_func=sleep_func
            )
        finally:
            os.unlink(
                path
            )

        self.assertEqual(
            "provider",
            events[0][0]
        )
        self.assertEqual(
            "provider",
            events[-1][0]
        )
        self.assertEqual(
            15,
            len(
                [
                    event
                    for event in events
                    if event[0] == "sleep"
                ]
            )
        )

    def test_deterministic_query_order(self):
        path = write_primary_file(
            accepted_primary_rows()
        )
        provider = Mock(
            return_value="Grounded answer."
        )

        try:
            results = confirm.run_confirmation(
                path,
                answer_provider=provider,
                sleep_func=Mock()
            )
        finally:
            os.unlink(
                path
            )

        self.assertEqual(
            confirm.EXPECTED_CONFIRMATION_QUERY_IDS,
            tuple(
                result["QUERY_ID"]
                for result in results
            )
        )

    def test_provider_exception_produces_provider_error_without_retry_and_continues(self):
        path = write_primary_file(
            accepted_primary_rows()
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
            results = confirm.run_confirmation(
                path,
                answer_provider=provider,
                sleep_func=Mock()
            )
        finally:
            os.unlink(
                path
            )

        self.assertEqual(
            16,
            len(
                calls
            )
        )
        self.assertEqual(
            "PROVIDER_ERROR",
            results[1]["CONFIRMATION_OUTCOME"]
        )
        self.assertIn(
            "synthetic provider failure",
            results[1]["CONFIRMATION_PROVIDER_ERROR"]
        )
        self.assertEqual(
            "GENERATED_ANSWER",
            results[2]["CONFIRMATION_OUTCOME"]
        )

    def test_successful_answers_use_existing_classifier(self):
        generated = confirm.confirm_primary_row(
            primary_row(
                "RAGDEV001"
            ),
            answer_provider=Mock(
                return_value="This is a grounded answer."
            )
        )
        refusal = confirm.confirm_primary_row(
            primary_row(
                "RAGDEV002"
            ),
            answer_provider=Mock(
                return_value="The available documentation is insufficient."
            )
        )

        self.assertEqual(
            "GENERATED_ANSWER",
            generated["CONFIRMATION_OUTCOME"]
        )
        self.assertEqual(
            "LLM_REFUSAL",
            refusal["CONFIRMATION_OUTCOME"]
        )

    def test_output_has_expected_columns(self):
        output = StringIO()
        confirm.write_results(
            [
                confirm.confirm_primary_row(
                    primary_row(
                        "RAGDEV001"
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
                confirm.CONFIRMATION_FIELDNAMES
            ),
            header
        )

    def test_malformed_contexts_fail_before_provider_call(self):
        row = primary_row(
            "RAGDEV001"
        )
        row["CONTEXTS"] = "{malformed"
        provider = Mock(
            return_value="should not be called"
        )

        with self.assertRaises(ValueError):
            confirm.confirm_primary_row(
                row,
                answer_provider=provider
            )

        provider.assert_not_called()

    def test_primary_file_is_not_mutated(self):
        path = write_primary_file(
            accepted_primary_rows()
        )

        try:
            with open(
                path,
                "rb"
            ) as file:
                before = file.read()

            confirm.prepare_confirmation_rows(
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


if __name__ == "__main__":
    unittest.main()
