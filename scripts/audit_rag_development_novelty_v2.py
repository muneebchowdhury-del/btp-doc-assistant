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
SUPPORTED_MANUAL_ASSESSMENTS = {
    "RAGDEV001": (
        "NEW_DEVELOPMENT_FORMULATION_OR_SCENARIO",
        "Uses a new development formulation focused on the Cloud Foundry platform basis; factual overlap with prior Cloud Foundry environment questions is expected."
    ),
    "RAGDEV002": (
        "NEW_DEVELOPMENT_FORMULATION_OR_SCENARIO",
        "Uses a new development scenario about development-phase responsibility before operations; overlap with prior Cloud Foundry development questions is expected."
    ),
    "RAGDEV003": (
        "NEW_DEVELOPMENT_FORMULATION_OR_SCENARIO",
        "Uses a new development formulation about deployment lifecycle documentation after development; overlap with prior deployment questions is expected."
    ),
    "RAGDEV004": (
        "NEW_DEVELOPMENT_FORMULATION_OR_SCENARIO",
        "Uses a new service-representation framing before credentials are attached; overlap with prior service-consumption questions is expected."
    ),
    "RAGDEV005": (
        "NEW_DEVELOPMENT_FORMULATION_OR_SCENARIO",
        "Uses a new formulation around the app-service relationship created by binding; overlap with prior binding and credential questions is expected."
    ),
    "RAGDEV006": (
        "NEW_DEVELOPMENT_FORMULATION_OR_SCENARIO",
        "Uses a new configuration-management framing around source-code separation; overlap with prior environment-variable questions is expected."
    ),
    "RAGDEV007": (
        "NEW_DEVELOPMENT_FORMULATION_OR_SCENARIO",
        "Uses a new route-administration formulation around reserving and managing addresses; overlap with prior route questions is expected."
    ),
    "RAGDEV008": (
        "NEW_DEVELOPMENT_FORMULATION_OR_SCENARIO",
        "Uses a new permission-assignment scenario across organization and space roles; overlap with prior roles questions is expected."
    ),
    "RAGDEV009": (
        "NEW_DEVELOPMENT_FORMULATION_OR_SCENARIO",
        "Uses a new troubleshooting formulation focused on recent instance output; overlap with prior application-log questions is expected."
    ),
    "RAGDEV010": (
        "NEW_DEVELOPMENT_FORMULATION_OR_SCENARIO",
        "Uses a new formulation focused on lifecycle record type for restaging or crashes; overlap with prior application-event questions is expected."
    ),
    "RAGDEV011": (
        "NEW_DEVELOPMENT_FORMULATION_OR_SCENARIO",
        "Uses a new credential-artifact scenario for access without a running bound app; overlap with prior service-key questions is expected."
    ),
    "RAGDEV012": (
        "NEW_DEVELOPMENT_FORMULATION_OR_SCENARIO",
        "Uses a new documentation-location formulation for assigning space resource limits; overlap with prior quota questions is expected."
    ),
    "RAGDEV013": (
        "NEW_DEVELOPMENT_FORMULATION_OR_SCENARIO",
        "Uses a new feature-identification formulation for container network traffic rules; overlap with prior security-group questions is expected."
    ),
    "RAGDEV014": (
        "NEW_DEVELOPMENT_FORMULATION_OR_SCENARIO",
        "Uses a new routes-and-destinations relationship formulation for backend access; overlap with prior routing/destination questions is expected."
    ),
    "RAGDEV015": (
        "NEW_DEVELOPMENT_FORMULATION_OR_SCENARIO",
        "Uses a new overview framing around extension and integration across SAP landscapes; overlap with prior SAP BTP overview questions is expected."
    ),
    "RAGDEV016": (
        "NEW_DEVELOPMENT_FORMULATION_OR_SCENARIO",
        "Uses a new terminology-before-service-guides scenario; overlap with prior basic platform concept questions is expected."
    )
}
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
        "No arbitrary semantic-similarity rejection threshold is applied. Same-domain factual or conceptual overlap is expected because this is a development set over the same frozen corpus, not an independent final holdout.",
        "",
        "The questions must not be interpreted as a fresh independent final evaluation set. Retrieval architecture and thresholds will not be tuned from these results. A completely fresh end-to-end RAG evaluation set will be created only after the generation architecture is finalized.",
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

    supported_results = [
        result
        for result in results
        if result["category"] == "SUPPORTED"
    ]

    lines.extend(
        [
            "",
            "## Supported Question Manual Development-Set Review",
            "",
            "| Query ID | Manual Assessment | Rationale |",
            "| --- | --- | --- |"
        ]
    )

    for result in supported_results:
        lines.append(
            "| {query_id} | {manual_assessment} | {manual_rationale} |".format(
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
    missing_supported_assessments = []
    same_fact_paraphrases = []

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
        manual_assessment = ""
        manual_rationale = ""

        if row["CATEGORY"] == "SUPPORTED":
            if query_id not in SUPPORTED_MANUAL_ASSESSMENTS:
                missing_supported_assessments.append(
                    query_id
                )
            else:
                manual_assessment, manual_rationale = SUPPORTED_MANUAL_ASSESSMENTS[
                    query_id
                ]
                if manual_assessment == "SAME_FACT_PARAPHRASE":
                    same_fact_paraphrases.append(
                        query_id
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
                ),
                "manual_assessment": manual_assessment,
                "manual_rationale": manual_rationale.replace(
                    "|",
                    "\\|"
                )
            }
        )

    if missing_supported_assessments:
        raise SystemExit(
            "Missing supported manual novelty assessments: "
            + ", ".join(
                missing_supported_assessments
            )
        )

    if same_fact_paraphrases:
        raise SystemExit(
            "Supported RAG development questions require rewrite: "
            + ", ".join(
                same_fact_paraphrases
            )
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
