import csv
import inspect
from io import StringIO
import os
import tempfile
import unittest
from unittest.mock import Mock

from llm_provider import GROQ_MODEL
import scripts.compare_rag_generation_provider_groq_v2 as comparison


def contexts_text(document_id="DOC001"):
    return repr(
        [
            {
                "document_id": document_id,
                "title": f"{document_id} title",
                "source_url": f"https://help.sap.com/docs/example/{document_id.lower()}",
                "chunk_text": f"{document_id} preserved confirmation context",
                "retrieval_rank": 1
            }
        ]
    )


def confirmation_row(query_id, context_document_id="DOC001"):
    return {
        "QUERY_ID": query_id,
        "QUESTION": f"{query_id} exact confirmation question?",
        "PRIMARY_CONTEXT_DOCUMENT_IDS": context_document_id,
        "CONTEXTS": contexts_text(
            context_document_id
        ),
        "CONFIRMATION_OUTCOME": "GENERATED_ANSWER"
    }


def comparison_rows():
    return [
        confirmation_row(
            query_id
        )
        for query_id in comparison.EXPECTED_COMPARISON_QUERY_IDS
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


class RAGGenerationProviderGroqComparisonTests(unittest.TestCase):
    def test_exact_16_ids_and_order_are_selected(self):
        rows = comparison_rows() + [
            confirmation_row(
                "RAGDEV010"
            )
        ]

        selected = comparison.select_comparison_rows(
            rows
        )

        comparison.validate_comparison_selection(
            selected
        )
        self.assertEqual(
            comparison.EXPECTED_COMPARISON_QUERY_IDS,
            comparison.selected_query_ids(
                selected
            )
        )

    def test_exact_question_and_contexts_are_preserved(self):
        row = confirmation_row(
            "RAGDEV001",
            "DOC009"
        )
        provider = Mock(
            return_value="Grounded answer."
        )
        contexts = comparison.parse_confirmation_contexts(
            row
        )

        result = comparison.compare_row_with_groq(
            row,
            answer_provider=provider
        )

        provider.assert_called_once_with(
            "RAGDEV001 exact confirmation question?",
            contexts
        )
        self.assertEqual(
            contexts_text(
                "DOC009"
            ),
            result["CONTEXTS"]
        )
        self.assertEqual(
            "DOC009",
            result["PRIMARY_CONTEXT_DOCUMENT_IDS"]
        )

    def test_exactly_16_provider_calls_and_15_pacing_sleeps(self):
        path = write_confirmation_file(
            comparison_rows()
        )
        provider = Mock(
            return_value="Grounded answer."
        )
        sleep_func = Mock()

        try:
            results = comparison.run_comparison(
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
                    comparison.PROVIDER_REQUEST_SPACING_SECONDS,
                )
                for call in sleep_func.call_args_list
            )
        )

    def test_no_sleep_before_first_request_or_after_last_request(self):
        path = write_confirmation_file(
            comparison_rows()
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
            comparison.run_comparison(
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
        self.assertTrue(
            all(
                event
                == (
                    "sleep",
                    30.0
                )
                for event in events
                if event[0] == "sleep"
            )
        )

    def test_provider_error_continues_to_later_cases_without_retry(self):
        path = write_confirmation_file(
            comparison_rows()
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
            results = comparison.run_comparison(
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
            results[1]["GROQ_OUTCOME"]
        )
        self.assertIn(
            "synthetic provider failure",
            results[1]["GROQ_PROVIDER_ERROR"]
        )
        self.assertEqual(
            "GENERATED_ANSWER",
            results[2]["GROQ_OUTCOME"]
        )

    def test_generated_answer_and_llm_refusal_classification(self):
        generated = comparison.compare_row_with_groq(
            confirmation_row(
                "RAGDEV001"
            ),
            answer_provider=Mock(
                return_value="Grounded answer."
            )
        )
        refusal = comparison.compare_row_with_groq(
            confirmation_row(
                "RAGDEV002"
            ),
            answer_provider=Mock(
                return_value="The available documentation is insufficient."
            )
        )

        self.assertEqual(
            "GENERATED_ANSWER",
            generated["GROQ_OUTCOME"]
        )
        self.assertEqual(
            "LLM_REFUSAL",
            refusal["GROQ_OUTCOME"]
        )

    def test_source_confirmation_csv_is_not_mutated(self):
        path = write_confirmation_file(
            comparison_rows()
        )

        try:
            with open(
                path,
                "rb"
            ) as file:
                before = file.read()

            comparison.prepare_comparison_rows(
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

    def test_no_retrieval_or_hana_imports_are_required(self):
        source = inspect.getsource(
            comparison
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

    def test_required_output_columns_and_provider_model_labels(self):
        result = comparison.compare_row_with_groq(
            confirmation_row(
                "RAGDEV001"
            ),
            answer_provider=Mock(
                return_value="Grounded answer."
            )
        )
        output = StringIO()

        comparison.write_results(
            [
                result
            ],
            output=output
        )

        header = output.getvalue().splitlines()[0].split(
            ","
        )
        self.assertEqual(
            list(
                comparison.GROQ_COMPARISON_FIELDNAMES
            ),
            header
        )
        self.assertEqual(
            "GROQ",
            result["PROVIDER"]
        )
        self.assertEqual(
            GROQ_MODEL,
            result["MODEL"]
        )
        self.assertEqual(
            "openai/gpt-oss-120b",
            result["MODEL"]
        )

    def test_malformed_contexts_fail_before_provider_call(self):
        row = confirmation_row(
            "RAGDEV001"
        )
        row["CONTEXTS"] = "{malformed"
        provider = Mock(
            return_value="should not be called"
        )

        with self.assertRaises(ValueError):
            comparison.compare_row_with_groq(
                row,
                answer_provider=provider
            )

        provider.assert_not_called()


if __name__ == "__main__":
    unittest.main()
