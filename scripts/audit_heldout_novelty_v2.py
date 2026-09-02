import csv
import math
import re
from pathlib import Path


HELDOUT_FILE = Path("data/retrieval_abstention_heldout_v2.csv")
ASSESSMENT_FILE = Path("data/retrieval_abstention_heldout_v2_assessments.csv")
PRIOR_FILES = [
    Path("data/evaluation_queries.csv"),
    Path("data/evaluation_queries_v2_foundation.csv"),
    Path("data/retrieval_calibration_v2.csv")
]
OUTPUT_FILE = Path("docs/V2_HELDOUT_NOVELTY_AUDIT.md")
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
    "before",
    "by",
    "can",
    "do",
    "does",
    "for",
    "from",
    "how",
    "i",
    "in",
    "is",
    "it",
    "my",
    "of",
    "or",
    "our",
    "should",
    "that",
    "the",
    "this",
    "to",
    "use",
    "what",
    "when",
    "where",
    "which",
    "with"
}


def load_rows(path):
    with path.open(
        newline="",
        encoding="utf-8"
    ) as file:
        return list(
            csv.DictReader(
                file
            )
        )


def normalized_tokens(text):
    return {
        token.lower()
        for token in TOKEN_PATTERN.findall(
            text or ""
        )
        if token.lower() not in STOPWORDS
    }


def overlap_score(left, right):
    left_tokens = normalized_tokens(
        left
    )
    right_tokens = normalized_tokens(
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


def nearest_lexical_prior(question, prior_rows):
    scored = [
        (
            overlap_score(
                question,
                prior["QUESTION"]
            ),
            prior
        )
        for prior in prior_rows
    ]
    scored.sort(
        key=lambda item: item[0],
        reverse=True
    )

    return scored[0]


def load_embedding_model():
    from fastembed import TextEmbedding

    return TextEmbedding(
        model_name=MODEL_NAME
    )


def embed_questions(model, rows):
    questions = [
        row["QUESTION"]
        for row in rows
    ]
    embeddings = list(
        model.query_embed(
            questions
        )
    )

    return {
        row["QUERY_ID"]: [
            float(value)
            for value in embedding
        ]
        for row, embedding in zip(
            rows,
            embeddings
        )
    }


def cosine_similarity(left, right):
    dot_product = sum(
        left_value * right_value
        for left_value, right_value in zip(
            left,
            right
        )
    )
    left_norm = math.sqrt(
        sum(
            value * value
            for value in left
        )
    )
    right_norm = math.sqrt(
        sum(
            value * value
            for value in right
        )
    )

    if (
        not left_norm
        or not right_norm
    ):
        return 0.0

    return dot_product / (
        left_norm * right_norm
    )


def nearest_embedding_prior(question_id, prior_rows, heldout_embeddings, prior_embeddings):
    heldout_embedding = heldout_embeddings[question_id]
    scored = [
        (
            cosine_similarity(
                heldout_embedding,
                prior_embeddings[prior["QUERY_ID"]]
            ),
            prior
        )
        for prior in prior_rows
    ]
    scored.sort(
        key=lambda item: item[0],
        reverse=True
    )

    return scored[0]


def load_assessments():
    rows = load_rows(
        ASSESSMENT_FILE
    )
    assessments = {}

    for row in rows:
        query_id = row["QUERY_ID"].strip()
        assessment = row["ASSESSMENT"].strip()
        rationale = row["RATIONALE"].strip()

        if assessment not in {
            "DISTINCT",
            "TOO_SIMILAR"
        }:
            raise SystemExit(
                f"Invalid assessment for {query_id}: {assessment}"
            )

        if not rationale:
            raise SystemExit(
                f"Missing rationale for {query_id}"
            )

        assessments[query_id] = {
            "ASSESSMENT": assessment,
            "RATIONALE": rationale
        }

    return assessments


def markdown_escape(value):
    return (
        value.replace(
            "|",
            "\\|"
        )
        .replace(
            "\n",
            " "
        )
        .strip()
    )


def main():
    heldout_rows = load_rows(
        HELDOUT_FILE
    )
    assessments = load_assessments()
    prior_rows = []

    for path in PRIOR_FILES:
        for row in load_rows(
            path
        ):
            row["SOURCE_FILE"] = str(
                path
            )
            prior_rows.append(
                row
            )

    heldout_ids = {
        row["QUERY_ID"]
        for row in heldout_rows
    }
    assessment_ids = set(
        assessments
    )
    missing_assessments = sorted(
        heldout_ids - assessment_ids
    )
    extra_assessments = sorted(
        assessment_ids - heldout_ids
    )

    if missing_assessments:
        raise SystemExit(
            "Missing manual assessments: "
            + ", ".join(
                missing_assessments
            )
        )

    if extra_assessments:
        raise SystemExit(
            "Manual assessments without held-out question: "
            + ", ".join(
                extra_assessments
            )
        )

    model = load_embedding_model()
    heldout_embeddings = embed_questions(
        model,
        heldout_rows
    )
    prior_embeddings = embed_questions(
        model,
        prior_rows
    )

    lines = [
        "# Version 2 Held-Out Novelty Audit",
        "",
        "## Purpose",
        "",
        "This pre-execution audit checks the proposed held-out questions against prior Version 1, Version 2 foundation, and Version 2 calibration questions. It uses two independent local diagnostics: normalized lexical Jaccard overlap and local question-to-question embedding cosine similarity with FastEmbed `BAAI/bge-small-en-v1.5`. It does not query HANA, retrieve corpus documents, inspect retrieval scores, or execute the held-out evaluator.",
        "",
        "## Inputs",
        "",
        f"- Held-out dataset: `{HELDOUT_FILE}`",
        f"- Manual assessment file: `{ASSESSMENT_FILE}`",
        f"- Local embedding model: `{MODEL_NAME}`",
        "- Prior question files:",
        *[
            f"  - `{path}`"
            for path in PRIOR_FILES
        ],
        "",
        "## Method",
        "",
        "For each held-out question, the audit tokenizes text, lowercases tokens, removes common question stopwords, computes lexical Jaccard overlap against every prior question, and reports the nearest lexical prior question. It also embeds every held-out and prior question locally and reports the nearest prior question by cosine similarity. Manual assessments are maintained explicitly in a separate CSV and are not inferred by the script.",
        "",
        "## Results",
        "",
        "| Held-Out ID | Lexical Prior ID | Lexical Similarity | Embedding Prior ID | Embedding Similarity | Manual Assessment | Rationale | Held-Out Question | Lexical Prior Question | Embedding Prior Question |",
        "| --- | --- | ---: | --- | ---: | --- | --- | --- | --- | --- |"
    ]

    exact_duplicates = []
    too_similar = []

    for row in heldout_rows:
        lexical_score, lexical_prior = nearest_lexical_prior(
            row["QUESTION"],
            prior_rows
        )
        embedding_score, embedding_prior = nearest_embedding_prior(
            row["QUERY_ID"],
            prior_rows,
            heldout_embeddings,
            prior_embeddings
        )
        manual = assessments[row["QUERY_ID"]]
        assessment = manual["ASSESSMENT"]

        if (
            row["QUESTION"].strip().lower()
            == lexical_prior["QUESTION"].strip().lower()
            or row["QUESTION"].strip().lower()
            == embedding_prior["QUESTION"].strip().lower()
        ):
            exact_duplicates.append(
                row["QUERY_ID"]
            )

        lines.append(
            "| "
            + " | ".join(
                [
                    row["QUERY_ID"],
                    lexical_prior["QUERY_ID"],
                    f"{lexical_score:.4f}",
                    embedding_prior["QUERY_ID"],
                    f"{embedding_score:.4f}",
                    assessment,
                    markdown_escape(
                        manual["RATIONALE"]
                    ),
                    markdown_escape(
                        row["QUESTION"]
                    ),
                    markdown_escape(
                        lexical_prior["QUESTION"]
                    ),
                    markdown_escape(
                        embedding_prior["QUESTION"]
                    )
                ]
            )
            + " |"
        )

        if assessment == "TOO_SIMILAR":
            too_similar.append(
                row["QUERY_ID"]
            )

    lines.extend(
        [
            "",
            "## Summary",
            "",
            f"- Held-out questions checked: {len(heldout_rows)}",
            f"- Prior questions checked: {len(prior_rows)}",
            "- Novelty diagnostics: normalized lexical Jaccard overlap and local FastEmbed question-to-question cosine similarity",
            f"- Exact duplicates found: {len(exact_duplicates)}",
            f"- Manual `TOO_SIMILAR` assessments remaining: {len(too_similar)}",
            "- HANA retrieval executed: no",
            "- Held-out evaluator executed: no",
            "",
            "Unsupported near-domain families were checked against the active source catalog by title/topic. The current source list covers SAP BTP platform overview, Cloud Foundry, services, routes, roles, logs, events, account model, entitlements, regions, tools, trial/free tier, and getting started. It does not include SAP Build Process Automation, SAP AI Core, SAP Mobile Services, SAP Cloud Transport Management, SAP Analytics Cloud, SAP Cloud ALM, Alert Notification, or SAP Document Management service-specific documentation."
        ]
    )

    OUTPUT_FILE.write_text(
        "\n".join(
            lines
        )
        + "\n",
        encoding="utf-8"
    )

    if too_similar:
        raise SystemExit(
            "TOO_SIMILAR questions remain: "
            + ", ".join(
                too_similar
            )
        )

    if exact_duplicates:
        raise SystemExit(
            "Exact duplicate questions remain: "
            + ", ".join(
                exact_duplicates
            )
        )

    print(
        f"Novelty audit written to {OUTPUT_FILE}"
    )


if __name__ == "__main__":
    main()
