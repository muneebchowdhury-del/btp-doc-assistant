import csv
import math
import os
import re
import sys


# Allow imports from project root.
PROJECT_ROOT = os.path.dirname(
    os.path.dirname(
        os.path.abspath(__file__)
    )
)

if PROJECT_ROOT not in sys.path:
    sys.path.insert(
        0,
        PROJECT_ROOT
    )


DEVELOPMENT_FILE = "data/rag_development_v2.csv"
PRIOR_FILES = (
    (
        "V1",
        "data/evaluation_queries.csv"
    ),
    (
        "V2_FOUNDATION",
        "data/evaluation_queries_v2_foundation.csv"
    ),
    (
        "V2_CALIBRATION",
        "data/retrieval_calibration_v2.csv"
    ),
    (
        "V2_HELDOUT",
        "data/retrieval_abstention_heldout_v2.csv"
    )
)
AUDIT_OUTPUT = "docs/V2_RAG_DEVELOPMENT_NOVELTY_AUDIT.md"
MODEL_NAME = "BAAI/bge-small-en-v1.5"
TOKEN_PATTERN = re.compile(
    r"[A-Za-z0-9]+"
)
STOPWORDS = {
    "a",
    "an",
    "and",
    "are",
    "as",
    "at",
    "be",
    "by",
    "can",
    "do",
    "does",
    "for",
    "from",
    "how",
    "i",
    "if",
    "in",
    "is",
    "it",
    "of",
    "on",
    "or",
    "should",
    "that",
    "the",
    "this",
    "to",
    "what",
    "when",
    "where",
    "which",
    "why",
    "with"
}


def read_csv_rows(path):
    with open(
        path,
        newline="",
        encoding="utf-8"
    ) as file:
        return list(
            csv.DictReader(
                file
            )
        )


def load_prior_questions():
    rows = []

    for label, path in PRIOR_FILES:
        for row in read_csv_rows(
            path
        ):
            rows.append(
                {
                    "source": label,
                    "query_id": row["QUERY_ID"],
                    "question": row["QUESTION"]
                }
            )

    return rows


def normalize_question(text):
    return " ".join(
        TOKEN_PATTERN.findall(
            text.lower()
        )
    )


def tokens(text):
    return {
        token
        for token in TOKEN_PATTERN.findall(
            text.lower()
        )
        if token not in STOPWORDS
    }


def jaccard(left, right):
    left_tokens = tokens(
        left
    )
    right_tokens = tokens(
        right
    )

    if (
        not left_tokens
        and not right_tokens
    ):
        return 1.0

    union = left_tokens | right_tokens

    if not union:
        return 0.0

    return len(
        left_tokens & right_tokens
    ) / len(
        union
    )


def nearest_lexical(question, prior_rows):
    return max(
        (
            (
                jaccard(
                    question,
                    prior["question"]
                ),
                prior
            )
            for prior in prior_rows
        ),
        key=lambda item: item[0]
    )


def dot(left, right):
    return sum(
        float(a) * float(b)
        for a, b in zip(
            left,
            right
        )
    )


def norm(vector):
    return math.sqrt(
        dot(
            vector,
            vector
        )
    )


def cosine(left, right):
    denominator = norm(
        left
    ) * norm(
        right
    )

    if denominator == 0:
        return 0.0

    return dot(
        left,
        right
    ) / denominator


def embed_questions(questions):
    from fastembed import TextEmbedding

    model = TextEmbedding(
        model_name=MODEL_NAME
    )
    return list(
        model.embed(
            questions
        )
    )


def nearest_semantic(question_embedding, prior_rows, prior_embeddings):
    best_score = float(
        "-inf"
    )
    best_prior = None

    for prior, prior_embedding in zip(
        prior_rows,
        prior_embeddings
    ):
        score = cosine(
            question_embedding,
            prior_embedding
        )
        if score > best_score:
            best_score = score
            best_prior = prior

    return (
        best_score,
        best_prior
    )


def category_counts(rows):
    counts = {}

    for row in rows:
        category = row["CATEGORY"]
        counts[category] = counts.get(
            category,
            0
        ) + 1

    return counts


def write_audit(results, duplicate_ids, development_rows, prior_rows):
    lines = [
        "# Version 2 RAG Development Novelty Audit",
        "",
        "## Scope",
        "",
        "This local-only audit checks the pre-registered RAG development questions against all prior Version 1, Version 2 foundation, Version 2 calibration, and Version 2 retrieval/abstention held-out questions.",
        "",
        "The audit uses exact duplicate detection, normalized lexical Jaccard overlap, and local question-to-question embedding cosine similarity with FastEmbed `BAAI/bge-small-en-v1.5`. It does not query HANA, retrieve corpus documents, call Gemini, inspect retrieval scores, or execute the RAG development harness.",
        "",
        "No arbitrary semantic-similarity rejection threshold is applied. Same-domain similarity is treated as acceptable when the question is substantively distinct and not an exact duplicate.",
        "",
        "## Dataset Composition",
        "",
        f"- RAG development questions: `{len(development_rows)}`",
        f"- Prior questions compared: `{len(prior_rows)}`"
    ]

    for category, count in sorted(
        category_counts(
            development_rows
        ).items()
    ):
        lines.append(
            f"- `{category}`: `{count}`"
        )

    lines.extend(
        [
            "",
            "## Exact Duplicate Check",
            ""
        ]
    )

    if duplicate_ids:
        lines.append(
            "Exact duplicates found: "
            + ", ".join(
                duplicate_ids
            )
        )
    else:
        lines.append(
            "No exact duplicate questions were found."
        )

    lines.extend(
        [
            "",
            "## Per-Question Nearest Prior Diagnostics",
            "",
            "| Query ID | Category | Nearest Lexical Prior | Lexical Jaccard | Nearest Semantic Prior | Embedding Cosine | Assessment |",
            "| --- | --- | --- | ---: | --- | ---: | --- |"
        ]
    )

    for result in results:
        lines.append(
            "| {query_id} | {category} | {lexical_id}: {lexical_question} | {lexical_score:.4f} | {semantic_id}: {semantic_question} | {semantic_score:.4f} | {assessment} |".format(
                **result
            )
        )

    lines.extend(
        [
            "",
            "## Result",
            "",
            "The pre-execution RAG development dataset passes the exact duplicate check. Lexical and semantic nearest-neighbor diagnostics are recorded for review before any RAG development execution.",
            ""
        ]
    )

    with open(
        AUDIT_OUTPUT,
        "w",
        encoding="utf-8",
        newline="\n"
    ) as file:
        file.write(
            "\n".join(
                lines
            )
        )


def run_audit():
    development_rows = read_csv_rows(
        DEVELOPMENT_FILE
    )
    prior_rows = load_prior_questions()

    prior_by_normalized_question = {
        normalize_question(
            prior["question"]
        ): prior
        for prior in prior_rows
    }
    duplicate_ids = []

    prior_embeddings = embed_questions(
        [
            prior["question"]
            for prior in prior_rows
        ]
    )
    development_embeddings = embed_questions(
        [
            row["QUESTION"]
            for row in development_rows
        ]
    )

    results = []

    for row, development_embedding in zip(
        development_rows,
        development_embeddings
    ):
        query_id = row["QUERY_ID"]
        question = row["QUESTION"]
        normalized_question = normalize_question(
            question
        )

        if normalized_question in prior_by_normalized_question:
            duplicate_ids.append(
                query_id
            )

        lexical_score, lexical_prior = nearest_lexical(
            question,
            prior_rows
        )
        semantic_score, semantic_prior = nearest_semantic(
            development_embedding,
            prior_rows,
            prior_embeddings
        )

        results.append(
            {
                "query_id": query_id,
                "category": row["CATEGORY"],
                "lexical_id": lexical_prior["query_id"],
                "lexical_question": lexical_prior["question"].replace(
                    "|",
                    "\\|"
                ),
                "lexical_score": lexical_score,
                "semantic_id": semantic_prior["query_id"],
                "semantic_question": semantic_prior["question"].replace(
                    "|",
                    "\\|"
                ),
                "semantic_score": semantic_score,
                "assessment": (
                    "EXACT_DUPLICATE"
                    if normalized_question in prior_by_normalized_question
                    else "NO_EXACT_DUPLICATE_REVIEW_REQUIRED"
                )
            }
        )

    write_audit(
        results,
        duplicate_ids,
        development_rows,
        prior_rows
    )

    print(
        f"Wrote {AUDIT_OUTPUT}"
    )

    if duplicate_ids:
        raise SystemExit(
            "Exact duplicate RAG development questions found: "
            + ", ".join(
                duplicate_ids
            )
        )

    print(
        "No exact duplicate RAG development questions found."
    )


if __name__ == "__main__":
    run_audit()
