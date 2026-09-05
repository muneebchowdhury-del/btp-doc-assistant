import json
from types import SimpleNamespace
import unittest
from unittest.mock import patch

from llm_provider import (
    GEMINI_API_KEY_ENV_VAR,
    GEMINI_MODEL,
    GROQ_API_KEY_ENV_VAR,
    GROQ_MODEL,
    VCAP_SERVICES_ENV_VAR,
    LLMProviderNotConfigured,
    LLMProviderCredentialError,
    _extract_groq_response_text,
    _extract_response_text,
    _resolve_gemini_api_key,
    _resolve_groq_api_key,
    build_grounded_prompt,
    generate_grounded_answer,
    generate_grounded_answer_groq,
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
        prompt_text = "\n".join(
            [
                payload.system,
                payload.user
            ]
        )

        self.assertIn(
            "Use only the supplied retrieved SAP documentation evidence.",
            prompt_text
        )
        self.assertIn(
            "semantically equivalent evidence",
            prompt_text
        )
        self.assertIn(
            "exact wording",
            prompt_text
        )
        self.assertIn(
            "follows reasonably from the supplied evidence",
            prompt_text
        )
        self.assertIn(
            "label the inferential part",
            prompt_text
        )
        self.assertIn(
            "neither stated in nor reasonably supported",
            prompt_text
        )
        self.assertIn(
            "available documentation is insufficient",
            prompt_text
        )
        self.assertIn(
            "core answer",
            prompt_text
        )
        self.assertIn(
            "additional requested details",
            prompt_text
        )
        self.assertIn(
            "Cite each SAP source used with its document ID and source URL.",
            prompt_text
        )
        self.assertIn(
            "Do not invent URLs",
            prompt_text
        )
        self.assertIn(
            "Answer directly first",
            prompt_text
        )
        self.assertIn(
            "Do not enumerate unrelated retrieved documents",
            prompt_text
        )
        self.assertIn(
            "DOC001",
            prompt_text
        )
        self.assertIn(
            "https://help.sap.com/docs/example/doc001",
            prompt_text
        )

    def test_missing_credentials_fail_before_provider_call(self):
        self.assertEqual(
            "gemini-3.5-flash",
            GEMINI_MODEL
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

    def test_extract_response_text_uses_gemini_text_field(self):
        class GeminiResponse:
            text = " Grounded answer from Gemini. "

        self.assertEqual(
            "Grounded answer from Gemini.",
            _extract_response_text(
                GeminiResponse()
            )
        )

    def test_direct_gemini_api_key_resolves(self):
        with patch.dict(
            "os.environ",
            {
                GEMINI_API_KEY_ENV_VAR: "direct-key"
            },
            clear=True
        ):
            self.assertEqual(
                "direct-key",
                _resolve_gemini_api_key()
            )

    def test_direct_gemini_api_key_takes_precedence_over_vcap(self):
        vcap_services = {
            "user-provided": [
                {
                    "name": "gemini-rag-dev",
                    "credentials": {
                        GEMINI_API_KEY_ENV_VAR: "vcap-key"
                    }
                }
            ]
        }

        with patch.dict(
            "os.environ",
            {
                GEMINI_API_KEY_ENV_VAR: "direct-key",
                VCAP_SERVICES_ENV_VAR: json.dumps(
                    vcap_services
                )
            },
            clear=True
        ):
            self.assertEqual(
                "direct-key",
                _resolve_gemini_api_key()
            )

    def test_vcap_services_fallback_resolves_gemini_service_key(self):
        vcap_services = {
            "hana": [
                {
                    "name": "not-gemini",
                    "credentials": {
                        GEMINI_API_KEY_ENV_VAR: "wrong-key"
                    }
                }
            ],
            "user-provided": [
                {
                    "name": "gemini-rag-dev",
                    "credentials": {
                        GEMINI_API_KEY_ENV_VAR: "vcap-key"
                    }
                }
            ]
        }

        with patch.dict(
            "os.environ",
            {
                VCAP_SERVICES_ENV_VAR: json.dumps(
                    vcap_services
                )
            },
            clear=True
        ):
            self.assertEqual(
                "vcap-key",
                _resolve_gemini_api_key()
            )

    def test_missing_gemini_credential_raises_credential_error(self):
        with patch.dict(
            "os.environ",
            {},
            clear=True
        ):
            with self.assertRaises(LLMProviderCredentialError):
                _resolve_gemini_api_key()

    def test_malformed_vcap_services_raises_non_secret_credential_error(self):
        with patch.dict(
            "os.environ",
            {
                VCAP_SERVICES_ENV_VAR: "{malformed-json"
            },
            clear=True
        ):
            with self.assertRaises(LLMProviderCredentialError) as context:
                _resolve_gemini_api_key()

        self.assertNotIn(
            "{malformed-json",
            str(
                context.exception
            )
        )
        self.assertIn(
            GEMINI_API_KEY_ENV_VAR,
            str(
                context.exception
            )
        )

    def test_direct_groq_api_key_resolves(self):
        with patch.dict(
            "os.environ",
            {
                GROQ_API_KEY_ENV_VAR: "direct-groq-key"
            },
            clear=True
        ):
            self.assertEqual(
                "direct-groq-key",
                _resolve_groq_api_key()
            )

    def test_direct_groq_api_key_takes_precedence_over_vcap(self):
        vcap_services = {
            "user-provided": [
                {
                    "name": "groq-rag-dev",
                    "credentials": {
                        GROQ_API_KEY_ENV_VAR: "vcap-groq-key"
                    }
                }
            ]
        }

        with patch.dict(
            "os.environ",
            {
                GROQ_API_KEY_ENV_VAR: "direct-groq-key",
                VCAP_SERVICES_ENV_VAR: json.dumps(
                    vcap_services
                )
            },
            clear=True
        ):
            self.assertEqual(
                "direct-groq-key",
                _resolve_groq_api_key()
            )

    def test_vcap_services_fallback_resolves_exact_groq_service_key(self):
        vcap_services = {
            "user-provided": [
                {
                    "name": "not-groq-rag-dev",
                    "credentials": {
                        GROQ_API_KEY_ENV_VAR: "wrong-key"
                    }
                },
                {
                    "name": "groq-rag-dev",
                    "credentials": {
                        GROQ_API_KEY_ENV_VAR: "vcap-groq-key"
                    }
                }
            ]
        }

        with patch.dict(
            "os.environ",
            {
                VCAP_SERVICES_ENV_VAR: json.dumps(
                    vcap_services
                )
            },
            clear=True
        ):
            self.assertEqual(
                "vcap-groq-key",
                _resolve_groq_api_key()
            )

    def test_wrong_groq_cups_service_is_ignored(self):
        vcap_services = {
            "user-provided": [
                {
                    "name": "wrong-groq-service",
                    "credentials": {
                        GROQ_API_KEY_ENV_VAR: "wrong-key"
                    }
                }
            ]
        }

        with patch.dict(
            "os.environ",
            {
                VCAP_SERVICES_ENV_VAR: json.dumps(
                    vcap_services
                )
            },
            clear=True
        ):
            with self.assertRaises(LLMProviderCredentialError):
                _resolve_groq_api_key()

    def test_missing_groq_credential_raises_credential_error(self):
        with patch.dict(
            "os.environ",
            {},
            clear=True
        ):
            with self.assertRaises(LLMProviderCredentialError):
                _resolve_groq_api_key()

    def test_malformed_vcap_services_raises_non_secret_groq_credential_error(self):
        with patch.dict(
            "os.environ",
            {
                VCAP_SERVICES_ENV_VAR: "{malformed-json"
            },
            clear=True
        ):
            with self.assertRaises(LLMProviderCredentialError) as context:
                _resolve_groq_api_key()

        self.assertNotIn(
            "{malformed-json",
            str(
                context.exception
            )
        )
        self.assertIn(
            GROQ_API_KEY_ENV_VAR,
            str(
                context.exception
            )
        )

    def test_extract_groq_response_text_uses_assistant_message_content(self):
        response = SimpleNamespace(
            choices=[
                SimpleNamespace(
                    message=SimpleNamespace(
                        content=" Grounded Groq answer. "
                    )
                )
            ]
        )

        self.assertEqual(
            "Grounded Groq answer.",
            _extract_groq_response_text(
                response
            )
        )

    def test_groq_receives_existing_grounded_prompt_and_fixed_configuration(self):
        captured = {}

        class FakeCompletions:
            def create(self, **kwargs):
                captured.update(
                    kwargs
                )
                return SimpleNamespace(
                    choices=[
                        SimpleNamespace(
                            message=SimpleNamespace(
                                content="Grounded Groq answer."
                            )
                        )
                    ]
                )

        class FakeGroq:
            def __init__(self, **kwargs):
                captured["client_kwargs"] = kwargs
                self.chat = SimpleNamespace(
                    completions=FakeCompletions()
                )

        fake_module = SimpleNamespace(
            Groq=FakeGroq
        )

        with patch.dict(
            "os.environ",
            {
                GROQ_API_KEY_ENV_VAR: "direct-groq-key"
            },
            clear=True
        ), patch.dict(
            "sys.modules",
            {
                "groq": fake_module
            }
        ):
            answer = generate_grounded_answer_groq(
                "What is supported?",
                self.sample_contexts()
            )

        self.assertEqual(
            "Grounded Groq answer.",
            answer
        )
        self.assertEqual(
            {
                "api_key": "direct-groq-key",
                "max_retries": 0
            },
            captured["client_kwargs"]
        )
        self.assertEqual(
            GROQ_MODEL,
            captured["model"]
        )
        self.assertEqual(
            "openai/gpt-oss-120b",
            captured["model"]
        )
        self.assertEqual(
            "medium",
            captured["reasoning_effort"]
        )
        self.assertFalse(
            captured["include_reasoning"]
        )
        self.assertEqual(
            "system",
            captured["messages"][0]["role"]
        )
        self.assertIn(
            "Use only the supplied retrieved SAP documentation evidence.",
            captured["messages"][0]["content"]
        )
        self.assertEqual(
            "user",
            captured["messages"][1]["role"]
        )
        self.assertIn(
            "Retrieved SAP documentation evidence:",
            captured["messages"][1]["content"]
        )
        self.assertIn(
            "DOC001",
            captured["messages"][1]["content"]
        )

    def test_empty_groq_provider_response_raises_no_text_error(self):
        class FakeCompletions:
            def create(self, **kwargs):
                return SimpleNamespace(
                    choices=[
                        SimpleNamespace(
                            message=SimpleNamespace(
                                content=" "
                            )
                        )
                    ]
                )

        class FakeGroq:
            def __init__(self, **kwargs):
                self.chat = SimpleNamespace(
                    completions=FakeCompletions()
                )

        with patch.dict(
            "os.environ",
            {
                GROQ_API_KEY_ENV_VAR: "direct-groq-key"
            },
            clear=True
        ), patch.dict(
            "sys.modules",
            {
                "groq": SimpleNamespace(
                    Groq=FakeGroq
                )
            }
        ):
            with self.assertRaises(LLMProviderNotConfigured):
                generate_grounded_answer_groq(
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
