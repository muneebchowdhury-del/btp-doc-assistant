import csv
import os
import sys
import time

PROJECT_ROOT = os.path.dirname(
    os.path.dirname(
        os.path.abspath(__file__)
    )
)

if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from llm_provider import (  # noqa: E402
    GROQ_MODEL,
    generate_grounded_answer_groq
)
from scripts.evaluate_rag_development_v2 import (  # noqa: E402
    evaluate_question,
    format_result_row
)
from scripts.evaluate_retrieval_variants_v2 import (  # noqa: E402
    build_bm25_index,
    fetch_corpus_chunks
)


HELDOUT_FILE = "data/retrieval_abstention_heldout_v2.csv"
SYSTEM_FREEZE_REF = "v2-rag-final-dev-freeze"
LLM_PROVIDER = "GROQ"


def load_heldout_queries():
    with open(
        HELDOUT_FILE,
        newline="",
        encoding="utf-8"
    ) as file:
        return list(
            csv.DictReader(file)
        )


def normalize_final_row(result):
    row = format_result_row(result)

    row["SYSTEM_FREEZE_REF"] = SYSTEM_FREEZE_REF
    row["LLM_PROVIDER"] = LLM_PROVIDER
    row["MODEL"] = GROQ_MODEL

    row["LLM_CALLED"] = row.pop(
        "GEMINI_CALLED"
    )
    row["LLM_ANSWER_OR_REFUSAL"] = row.pop(
        "GEMINI_ANSWER_OR_REFUSAL"
    )

    return row


def main():
    queries = load_heldout_queries()

    corpus_chunks, _ = fetch_corpus_chunks()
    bm25_index = build_bm25_index(
        corpus_chunks
    )

    results = []

    for index, item in enumerate(queries):
        result = evaluate_question(
            item,
            corpus_chunks,
            bm25_index,
            answer_provider=generate_grounded_answer_groq
        )
        results.append(
            normalize_final_row(result)
        )

        if (
            result["GEMINI_CALLED"]
            and index < len(queries) - 1
        ):
            time.sleep(30.0)

    fieldnames = list(
        results[0].keys()
    )

    writer = csv.DictWriter(
        sys.stdout,
        fieldnames=fieldnames,
        lineterminator="\n"
    )

    writer.writeheader()
    writer.writerows(results)


if __name__ == "__main__":
    main()
