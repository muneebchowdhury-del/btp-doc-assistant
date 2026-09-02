import unittest
from io import StringIO
from types import SimpleNamespace
from unittest.mock import Mock, patch

import scripts.evaluate_rag_development_v2 as harness


def chunk(
    document_id,
    chunk_id,
    dense_score=None,
    fused_score=0.0
):
    return SimpleNamespace(
        chunk_id=chunk_id,
        document_id=document_id,
        chunk_index=0,
        title=f"{document_id} title",
        topic="Synthetic topic",
        source_url=f"https://help.sap.com/docs/example/{document_id.lower()}",
        chunk_text=f"{document_id} synthetic chunk",
        dense_score=dense_score,
        lexical_score=0.0,
        fused_score=fused_score
    )


def item(query_id="RAGDEVTEST001"):
    return {
        "QUERY_ID": query_id,
        "QUESTION": "Synthetic development question?",
        "EXPECTED_SUPPORTED": "1",
        "EXPECTED_DOCUMENT_ID": "DOC001",
        "CATEGORY": "SUPPORTED"
    }


class RAGDevelopmentHarnessTests(unittest.TestCase):
    def test_below_gate_does_not_call_provider(self):
        provider = Mock(
            return_value="should not be called"
        )

        with patch.object(
            harness,
            "fetch_dense_chunks",
            return_value=(
                [
                    chunk(
                        "DOC001",
                        1,
                        dense_score=0.7499
                    )
                ],
                1.0,
                2.0
            )
        ), patch.object(
            harness,
            "bm25_rank",
            return_value=[]
        ), patch.object(
            harness,
            "reciprocal_rank_fusion",
            return_value=[
                chunk(
                    "DOC001",
                    1,
                    dense_score=0.7499,
                    fused_score=0.02
                )
            ]
        ):
            result = harness.evaluate_question(
                item(),
                [],
                {},
                answer_provider=provider
            )

        provider.assert_not_called()
        self.assertEqual(
            "ABSTAIN",
            result["ACCEPT_DECISION"]
        )
        self.assertEqual(
            "PIPELINE_ABSTAIN",
            result["OUTCOME"]
        )
        self.assertFalse(
            result["GEMINI_CALLED"]
        )

    def test_accepted_question_uses_context_bridge_default(self):
        provider = Mock(
            return_value="Grounded answer."
        )
        hybrid_chunks = [
            chunk(
                "DOC001",
                1,
                dense_score=0.80,
                fused_score=0.03
            )
        ]
        contexts = [
            {
                "document_id": "DOC001",
                "title": "DOC001 title",
                "source_url": "https://help.sap.com/docs/example/doc001",
                "chunk_text": "DOC001 synthetic chunk",
                "retrieval_rank": 1
            }
        ]

        with patch.object(
            harness,
            "fetch_dense_chunks",
            return_value=(
                [
                    chunk(
                        "DOC001",
                        1,
                        dense_score=0.80
                    )
                ],
                1.0,
                2.0
            )
        ), patch.object(
            harness,
            "bm25_rank",
            return_value=[]
        ), patch.object(
            harness,
            "reciprocal_rank_fusion",
            return_value=hybrid_chunks
        ), patch.object(
            harness,
            "build_rag_contexts_from_hybrid_results",
            return_value=contexts
        ) as bridge:
            result = harness.evaluate_question(
                item(),
                [],
                {},
                answer_provider=provider
            )

        bridge.assert_called_once_with(
            hybrid_chunks
        )
        provider.assert_called_once_with(
            "Synthetic development question?",
            contexts
        )
        self.assertEqual(
            "ACCEPT",
            result["ACCEPT_DECISION"]
        )
        self.assertEqual(
            "DOC001",
            result["CONTEXT_DOCUMENT_IDS"]
        )
        self.assertTrue(
            result["GEMINI_CALLED"]
        )

    def test_provider_refusal_is_distinct_from_pipeline_abstention(self):
        result = self.accepted_result_with_provider(
            Mock(
                return_value="The available documentation is insufficient."
            )
        )

        self.assertEqual(
            "LLM_REFUSAL",
            result["OUTCOME"]
        )
        self.assertEqual(
            "ACCEPT",
            result["ACCEPT_DECISION"]
        )

    def test_provider_exception_is_recorded_distinctly(self):
        result = self.accepted_result_with_provider(
            Mock(
                side_effect=RuntimeError(
                    "synthetic provider failure"
                )
            )
        )

        self.assertEqual(
            "PROVIDER_ERROR",
            result["OUTCOME"]
        )
        self.assertIn(
            "synthetic provider failure",
            result["PROVIDER_ERROR"]
        )

    def test_timing_fields_are_represented(self):
        result = self.accepted_result_with_provider(
            Mock(
                return_value="Grounded answer."
            )
        )

        for field in (
            "EMBEDDING_MS",
            "DENSE_HANA_MS",
            "LEXICAL_MS",
            "HYBRID_FUSION_MS",
            "RETRIEVAL_MS",
            "GENERATION_MS",
            "TOTAL_END_TO_END_MS"
        ):
            self.assertIn(
                field,
                result
            )
            self.assertIsInstance(
                result[field],
                float
            )

    def test_main_unpacks_corpus_chunks_before_building_bm25_index(self):
        corpus_chunks = [
            chunk(
                "DOC001",
                1
            )
        ]
        bm25_index = {
            "synthetic": 1
        }
        result = {
            "QUERY_ID": "RAGDEVTEST001",
            "QUESTION": "Synthetic development question?",
            "EXPECTED_SUPPORTED": "1",
            "EXPECTED_DOCUMENT_ID": "DOC001",
            "CATEGORY": "SUPPORTED",
            "REFERENCE_FACT": "Synthetic reference fact.",
            "DENSE_RANK1_DOCUMENT_ID": "DOC001",
            "DENSE_RANK1_SCORE": 0.80,
            "ACCEPT_DECISION": "ACCEPT",
            "HYBRID_TOP5_DOCUMENTS": "DOC001",
            "CONTEXT_DOCUMENT_IDS": "DOC001",
            "CONTEXTS": [],
            "GEMINI_CALLED": True,
            "OUTCOME": "GENERATED_ANSWER",
            "GEMINI_ANSWER_OR_REFUSAL": "Synthetic answer.",
            "PROVIDER_ERROR": "",
            "EMBEDDING_MS": 1.0,
            "DENSE_HANA_MS": 2.0,
            "LEXICAL_MS": 3.0,
            "HYBRID_FUSION_MS": 4.0,
            "RETRIEVAL_MS": 10.0,
            "GENERATION_MS": 5.0,
            "TOTAL_END_TO_END_MS": 15.0
        }

        with patch.object(
            harness,
            "load_development_queries",
            return_value=[
                item()
            ]
        ), patch.object(
            harness,
            "fetch_corpus_chunks",
            return_value=(
                corpus_chunks,
                12.0
            )
        ), patch.object(
            harness,
            "build_bm25_index",
            return_value=bm25_index
        ) as build_index, patch.object(
            harness,
            "evaluate_question",
            return_value=result
        ) as evaluate, patch(
            "sys.stdout",
            new_callable=StringIO
        ):
            harness.main()

        build_index.assert_called_once_with(
            corpus_chunks
        )
        evaluate.assert_called_once_with(
            item(),
            corpus_chunks,
            bm25_index
        )

    def test_reference_fact_is_recorded_without_provider_input(self):
        provider = Mock(
            return_value="Grounded answer."
        )
        input_item = item()
        input_item["REFERENCE_FACT"] = "Do not send this to Gemini."

        result = self.accepted_result_with_provider(
            provider,
            input_item=input_item
        )

        self.assertEqual(
            "Do not send this to Gemini.",
            result["REFERENCE_FACT"]
        )
        provider.assert_called_once()
        provider_question, provider_contexts = provider.call_args.args
        self.assertEqual(
            input_item["QUESTION"],
            provider_question
        )
        self.assertIsInstance(
            provider_contexts,
            list
        )

    def accepted_result_with_provider(self, provider, input_item=None):
        contexts = [
            {
                "document_id": "DOC001",
                "title": "DOC001 title",
                "source_url": "https://help.sap.com/docs/example/doc001",
                "chunk_text": "DOC001 synthetic chunk",
                "retrieval_rank": 1
            }
        ]

        with patch.object(
            harness,
            "fetch_dense_chunks",
            return_value=(
                [
                    chunk(
                        "DOC001",
                        1,
                        dense_score=0.80
                    )
                ],
                1.0,
                2.0
            )
        ), patch.object(
            harness,
            "bm25_rank",
            return_value=[]
        ), patch.object(
            harness,
            "reciprocal_rank_fusion",
            return_value=[
                chunk(
                    "DOC001",
                    1,
                    dense_score=0.80,
                    fused_score=0.03
                )
            ]
        ), patch.object(
            harness,
            "build_rag_contexts_from_hybrid_results",
            return_value=contexts
        ):
            return harness.evaluate_question(
                input_item or item(),
                [],
                {},
                answer_provider=provider
            )


if __name__ == "__main__":
    unittest.main()
