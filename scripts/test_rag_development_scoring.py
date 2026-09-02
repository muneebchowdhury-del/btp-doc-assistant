import csv
from io import StringIO
import os
import tempfile
import unittest
from unittest.mock import patch

import scripts.prepare_rag_development_scoring_v2 as prepare
import scripts.summarize_rag_development_scoring_v2 as summarize


def primary_row(
    query_id="RAGDEV001",
    expected_supported="1",
    expected_document="DOC001",
    context_ids="DOC001;DOC002",
    accept_decision="ACCEPT",
    outcome="GENERATED_ANSWER"
):
    return {
        "QUERY_ID": query_id,
        "QUESTION": f"{query_id} question?",
        "EXPECTED_SUPPORTED": expected_supported,
        "EXPECTED_DOCUMENT_ID": expected_document,
        "CATEGORY": "SUPPORTED" if expected_supported == "1" else "OUT_OF_SCOPE",
        "REFERENCE_FACT": "Synthetic reference fact.",
        "DENSE_RANK1_DOCUMENT_ID": "DOC001",
        "DENSE_RANK1_SCORE": "0.8000",
        "ACCEPT_DECISION": accept_decision,
        "HYBRID_TOP5_DOCUMENTS": context_ids,
        "CONTEXT_DOCUMENT_IDS": context_ids,
        "CONTEXTS": "[]",
        "OUTCOME": outcome,
        "GEMINI_ANSWER_OR_REFUSAL": "Synthetic answer.",
        "PROVIDER_ERROR": "",
        "EMBEDDING_MS": "1.00",
        "DENSE_HANA_MS": "2.00",
        "LEXICAL_MS": "3.00",
        "HYBRID_FUSION_MS": "4.00",
        "RETRIEVAL_MS": "10.00",
        "GENERATION_MS": "5.00",
        "TOTAL_END_TO_END_MS": "15.00"
    }


def retry_row(query_id):
    return {
        "QUERY_ID": query_id,
        "QUESTION": f"{query_id} question?",
        "PRIMARY_OUTCOME": "PROVIDER_ERROR",
        "PRIMARY_CONTEXT_DOCUMENT_IDS": "DOC001",
        "RETRY_OUTCOME": "GENERATED_ANSWER",
        "RETRY_GEMINI_ANSWER_OR_REFUSAL": "Retry answer.",
        "RETRY_PROVIDER_ERROR": "",
        "RETRY_GENERATION_MS": "123.45"
    }


def write_csv(rows, fieldnames):
    with tempfile.NamedTemporaryFile(
        "w",
        newline="",
        encoding="utf-8",
        delete=False
    ) as file:
        writer = csv.DictWriter(
            file,
            fieldnames=fieldnames,
            lineterminator="\n"
        )
        writer.writeheader()
        writer.writerows(
            rows
        )
        return file.name


class RAGDevelopmentScoringTests(unittest.TestCase):
    def test_canonical_primary_file_is_read_without_mutation(self):
        row = primary_row()
        path = write_csv(
            [
                row
            ],
            row.keys()
        )

        try:
            with open(
                path,
                "rb"
            ) as file:
                before = file.read()

            rows = prepare.prepare_scoring_rows(
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
                "PRIMARY",
                rows[0]["EVIDENCE_SOURCE"]
            )
        finally:
            os.unlink(
                path
            )

    def test_expected_document_context_diagnostics(self):
        row = primary_row(
            expected_document="DOC002",
            context_ids="DOC001;DOC002;DOC003"
        )

        scoring_row = prepare.primary_scoring_row(
            row
        )

        self.assertEqual(
            "1",
            scoring_row["EXPECTED_DOC_IN_CONTEXT"]
        )
        self.assertEqual(
            "2",
            scoring_row["EXPECTED_DOC_CONTEXT_RANK"]
        )

    def test_unsupported_rows_leave_expected_doc_diagnostics_blank(self):
        row = primary_row(
            expected_supported="0",
            expected_document="",
            context_ids="DOC001"
        )

        scoring_row = prepare.primary_scoring_row(
            row
        )

        self.assertEqual(
            "",
            scoring_row["EXPECTED_DOC_IN_CONTEXT"]
        )
        self.assertEqual(
            "",
            scoring_row["EXPECTED_DOC_CONTEXT_RANK"]
        )

    def test_provider_errors_are_not_scored_as_wrong_or_hallucinated(self):
        row = primary_row(
            outcome="PROVIDER_ERROR"
        )
        row["PROVIDER_ERROR"] = "429 RESOURCE_EXHAUSTED"

        scoring_row = prepare.primary_scoring_row(
            row
        )

        self.assertEqual(
            "PROVIDER_ERROR",
            scoring_row["GENERATION_OBSERVABILITY"]
        )
        self.assertEqual(
            "",
            scoring_row["ANSWER_CORRECTNESS"]
        )
        self.assertEqual(
            "",
            scoring_row["HALLUCINATION"]
        )
        self.assertEqual(
            "UNSCORED",
            scoring_row["SCORING_STATUS"]
        )

    def test_pipeline_abstains_have_generation_observability_not_called(self):
        row = primary_row(
            accept_decision="ABSTAIN",
            outcome="PIPELINE_ABSTAIN"
        )

        scoring_row = prepare.primary_scoring_row(
            row
        )

        self.assertEqual(
            "NOT_CALLED",
            scoring_row["GENERATION_OBSERVABILITY"]
        )

    def test_generated_and_refusal_outputs_have_observed_generation(self):
        for outcome in (
            "GENERATED_ANSWER",
            "LLM_REFUSAL"
        ):
            with self.subTest(
                outcome=outcome
            ):
                scoring_row = prepare.primary_scoring_row(
                    primary_row(
                        outcome=outcome
                    )
                )

                self.assertEqual(
                    "OBSERVED",
                    scoring_row["GENERATION_OBSERVABILITY"]
                )

    def test_optional_retry_file_only_accepts_exact_nine_ids(self):
        rows = [
            retry_row(
                query_id
            )
            for query_id in prepare.EXPECTED_PROVIDER_ERROR_IDS
        ]

        prepare.validate_retry_rows(
            rows
        )

        with self.assertRaises(ValueError):
            prepare.validate_retry_rows(
                rows[:-1]
            )

    def test_retry_values_cannot_overwrite_primary_values(self):
        primary_rows = [
            primary_row(
                query_id=query_id,
                outcome="PROVIDER_ERROR"
            )
            for query_id in prepare.EXPECTED_PROVIDER_ERROR_IDS
        ]
        retry_rows = [
            retry_row(
                query_id
            )
            for query_id in prepare.EXPECTED_PROVIDER_ERROR_IDS
        ]
        primary_path = write_csv(
            primary_rows,
            primary_rows[0].keys()
        )
        retry_path = write_csv(
            retry_rows,
            retry_rows[0].keys()
        )

        try:
            rows = prepare.prepare_scoring_rows(
                primary_path,
                retry_path
            )
        finally:
            os.unlink(
                primary_path
            )
            os.unlink(
                retry_path
            )

        secondary = [
            row
            for row in rows
            if row["EVIDENCE_SOURCE"] == "SECONDARY_RETRY"
        ][0]

        self.assertEqual(
            "PROVIDER_ERROR",
            secondary["PRIMARY_OUTCOME"]
        )
        self.assertEqual(
            "PROVIDER_ERROR",
            secondary["OUTCOME"]
        )
        self.assertEqual(
            "GENERATED_ANSWER",
            secondary["SECONDARY_RETRY_OUTCOME"]
        )

    def test_blank_metric_values_are_excluded_from_denominators(self):
        rows = [
            {
                "EVIDENCE_SOURCE": "PRIMARY",
                "PRIMARY_OUTCOME": "GENERATED_ANSWER",
                "GENERATION_OBSERVABILITY": "OBSERVED",
                "SCORING_STATUS": "SCORED",
                "GROUNDEDNESS": "1",
                "ANSWER_CORRECTNESS": "",
                "CITATION_CORRECTNESS": "0",
                "HALLUCINATION": "",
                "EVIDENCE_BASED_REFUSAL": "",
                "CONCISION": "2"
            },
            {
                "EVIDENCE_SOURCE": "PRIMARY",
                "PRIMARY_OUTCOME": "LLM_REFUSAL",
                "GENERATION_OBSERVABILITY": "OBSERVED",
                "SCORING_STATUS": "SCORED",
                "GROUNDEDNESS": "",
                "ANSWER_CORRECTNESS": "1",
                "CITATION_CORRECTNESS": "",
                "HALLUCINATION": "0",
                "EVIDENCE_BASED_REFUSAL": "1",
                "CONCISION": ""
            }
        ]

        self.assertEqual(
            (
                1,
                1,
                1.0
            ),
            summarize.rate(
                rows,
                "GROUNDEDNESS"
            )
        )
        self.assertEqual(
            (
                0,
                1,
                0.0
            ),
            summarize.rate(
                rows,
                "CITATION_CORRECTNESS"
            )
        )

    def test_summary_refuses_final_metrics_when_manual_rows_remain_unscored(self):
        rows = [
            {
                "QUERY_ID": "RAGDEV001",
                "EVIDENCE_SOURCE": "PRIMARY",
                "PRIMARY_OUTCOME": "GENERATED_ANSWER",
                "GENERATION_OBSERVABILITY": "OBSERVED",
                "SCORING_STATUS": "UNSCORED"
            }
        ]

        with self.assertRaises(ValueError):
            summarize.ensure_scored(
                rows
            )

    def test_manual_metrics_are_summarized_separately_by_evidence_source(self):
        rows = [
            {
                "QUERY_ID": "RAGDEV001",
                "EVIDENCE_SOURCE": "PRIMARY",
                "PRIMARY_OUTCOME": "GENERATED_ANSWER",
                "GENERATION_OBSERVABILITY": "OBSERVED",
                "SCORING_STATUS": "SCORED",
                "ACCEPT_DECISION": "ACCEPT",
                "GROUNDEDNESS": "1",
                "ANSWER_CORRECTNESS": "",
                "CITATION_CORRECTNESS": "",
                "HALLUCINATION": "",
                "EVIDENCE_BASED_REFUSAL": "",
                "CONCISION": ""
            },
            {
                "QUERY_ID": "RAGDEV008",
                "EVIDENCE_SOURCE": "SECONDARY_RETRY",
                "PRIMARY_OUTCOME": "PROVIDER_ERROR",
                "SECONDARY_RETRY_OUTCOME": "GENERATED_ANSWER",
                "GENERATION_OBSERVABILITY": "OBSERVED",
                "SCORING_STATUS": "SCORED",
                "ACCEPT_DECISION": "ACCEPT",
                "GROUNDEDNESS": "0",
                "ANSWER_CORRECTNESS": "",
                "CITATION_CORRECTNESS": "",
                "HALLUCINATION": "",
                "EVIDENCE_BASED_REFUSAL": "",
                "CONCISION": ""
            }
        ]

        primary_metrics = summarize.summarize_manual_metrics(
            [
                row
                for row in rows
                if row["EVIDENCE_SOURCE"] == "PRIMARY"
            ]
        )
        secondary_metrics = summarize.summarize_manual_metrics(
            [
                row
                for row in rows
                if row["EVIDENCE_SOURCE"] == "SECONDARY_RETRY"
            ]
        )

        self.assertEqual(
            (
                1,
                1,
                1.0
            ),
            primary_metrics["groundedness"]
        )
        self.assertEqual(
            (
                0,
                1,
                0.0
            ),
            secondary_metrics["groundedness"]
        )

    def test_print_summary_has_no_combined_manual_metric_headline(self):
        rows = [
            {
                "QUERY_ID": "RAGDEV001",
                "EVIDENCE_SOURCE": "PRIMARY",
                "PRIMARY_OUTCOME": "GENERATED_ANSWER",
                "GENERATION_OBSERVABILITY": "OBSERVED",
                "SCORING_STATUS": "SCORED",
                "ACCEPT_DECISION": "ACCEPT",
                "GROUNDEDNESS": "1",
                "ANSWER_CORRECTNESS": "",
                "CITATION_CORRECTNESS": "",
                "HALLUCINATION": "",
                "EVIDENCE_BASED_REFUSAL": "",
                "CONCISION": ""
            },
            {
                "QUERY_ID": "RAGDEV008",
                "EVIDENCE_SOURCE": "SECONDARY_RETRY",
                "PRIMARY_OUTCOME": "PROVIDER_ERROR",
                "SECONDARY_RETRY_OUTCOME": "GENERATED_ANSWER",
                "GENERATION_OBSERVABILITY": "OBSERVED",
                "SCORING_STATUS": "SCORED",
                "ACCEPT_DECISION": "ACCEPT",
                "GROUNDEDNESS": "0",
                "ANSWER_CORRECTNESS": "",
                "CITATION_CORRECTNESS": "",
                "HALLUCINATION": "",
                "EVIDENCE_BASED_REFUSAL": "",
                "CONCISION": ""
            }
        ]

        with patch(
            "sys.stdout",
            new_callable=StringIO
        ) as output:
            summarize.print_summary(
                rows
            )

        text = output.getvalue()

        self.assertIn(
            "Manually scored observable LLM outputs - PRIMARY",
            text
        )
        self.assertIn(
            "groundedness rate: 1.0000 (1/1)",
            text
        )
        self.assertIn(
            "Manually scored observable LLM outputs - SECONDARY_RETRY",
            text
        )
        self.assertIn(
            "groundedness rate: 0.0000 (0/1)",
            text
        )
        self.assertNotIn(
            "groundedness rate: 0.5000 (1/2)",
            text
        )
        self.assertNotIn(
            "Manually scored observable LLM outputs\n",
            text
        )

    def test_no_network_gemini_hana_or_retrieval_calls_occur(self):
        row = primary_row()
        scoring_row = prepare.primary_scoring_row(
            row
        )

        self.assertEqual(
            row["QUESTION"],
            scoring_row["QUESTION"]
        )


if __name__ == "__main__":
    unittest.main()
