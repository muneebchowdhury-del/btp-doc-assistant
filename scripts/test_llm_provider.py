import unittest
from unittest.mock import patch

from llm_provider import (
    LLMProviderCredentialError,
    OPENAI_MODEL,
    build_grounded_prompt,
    generate_grounded_answer,
    normalize_contexts
)


class LLMProviderTests(unittest.TestCase):
    def sample_contexts(self):
        return [
            {
                "document_id": "DOC002",
                "title": "Development",
                "source_url": "https://help.sap.com/docs/example/doc002",
                "chunk_text": "Development guidance excerpt.",
                "retrieval_rank": 2
            },
            {
                "document_id": "DOC001",
                "title": "Cloud Foundry Environment",
                "source_url": "https://help.sap.com/docs/example/doc001",
                "chunk_text": "Runtime evidence excerpt.",
                "retrieval_rank": 1
            }
        ]

    def test_normalizes_contexts_by_rank(self):
        contexts = normalize_contexts(
            self.sample_contexts()
        )

        self.assertEqual(
            ["DOC001", "DOC002"],
            [
                context.document_id
                for context in contexts
            ]
        )

    def test_prompt_contains_grounding_contract(self):
        payload = build_grounded_prompt(
            "What is supported?",
            self.sample_contexts()
        )

        self.assertIn(
            "Use only the supplied retrieved SAP documentation evidence.",
            payload.system
        )
        self.assertIn(
            "available documentation is insufficient",
            payload.user
        )
        self.assertIn(
            "DOC001",
            payload.user
        )
        self.assertIn(
            "https://help.sap.com/docs/example/doc001",
            payload.user
        )

    def test_generate_does_not_call_provider_yet(self):
        self.assertEqual(
            "gpt-5.6-terra",
            OPENAI_MODEL
        )

        with patch.dict(
            "os.environ",
            {},
            clear=True
        ):
            with self.assertRaises(LLMProviderCredentialError):
                generate_grounded_answer(
                    "What is supported?",
                    self.sample_contexts()
                )

    def test_missing_context_field_fails(self):
        with self.assertRaises(ValueError):
            build_grounded_prompt(
                "What is supported?",
                [
                    {
                        "document_id": "DOC001",
                        "title": "Cloud Foundry Environment",
                        "source_url": "https://help.sap.com/docs/example/doc001",
                        "retrieval_rank": 1
                    }
                ]
            )


if __name__ == "__main__":
    unittest.main()
