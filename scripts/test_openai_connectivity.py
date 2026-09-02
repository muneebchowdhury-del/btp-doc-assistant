import os
import sys


# Allow imports from project root.
PROJECT_ROOT = os.path.dirname(
    os.path.dirname(
        os.path.abspath(__file__)
    )
)

if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)


from llm_provider import (  # noqa: E402
    OPENAI_API_KEY_ENV_VAR,
    OPENAI_MODEL,
    generate_grounded_answer
)


QUESTION = "What environment does this documentation describe?"
CONTEXTS = [
    {
        "document_id": "TEST-DOC",
        "title": "Test SAP BTP Documentation",
        "source_url": "https://help.sap.com/docs/example/test-doc",
        "chunk_text": (
            "This reviewed synthetic context describes SAP BTP documentation "
            "for an application runtime environment. It is used only for "
            "connectivity testing and is not part of any final RAG evaluation set."
        ),
        "retrieval_rank": 1
    }
]


def main():
    if not os.getenv(
        OPENAI_API_KEY_ENV_VAR
    ):
        print(
            f"{OPENAI_API_KEY_ENV_VAR} is not set; connectivity test was not run."
        )
        return 0

    print(
        "Running isolated OpenAI Responses API connectivity test "
        f"with model {OPENAI_MODEL}."
    )
    answer = generate_grounded_answer(
        QUESTION,
        CONTEXTS
    )
    print(
        answer
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(
        main()
    )
