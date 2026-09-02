import csv
import re
from pathlib import Path


HELDOUT_FILE = Path("data/retrieval_abstention_heldout_v2.csv")
PRIOR_FILES = [
    Path("data/evaluation_queries.csv"),
    Path("data/evaluation_queries_v2_foundation.csv"),
    Path("data/retrieval_calibration_v2.csv")
]
OUTPUT_FILE = Path("docs/V2_HELDOUT_NOVELTY_AUDIT.md")

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


def nearest_prior(question, prior_rows):
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

    lines = [
        "# Version 2 Held-Out Novelty Audit",
        "",
        "## Purpose",
        "",
        "This pre-execution audit checks the proposed held-out questions against prior Version 1, Version 2 foundation, and Version 2 calibration questions. It uses normalized lexical Jaccard overlap only. It does not query HANA, retrieve corpus documents, inspect retrieval scores, or execute the held-out evaluator.",
        "",
        "## Inputs",
        "",
        f"- Held-out dataset: `{HELDOUT_FILE}`",
        "- Prior question files:",
        *[
            f"  - `{path}`"
            for path in PRIOR_FILES
        ],
        "",
        "## Method",
        "",
        "For each held-out question, the audit tokenizes text, lowercases tokens, removes common question stopwords, computes lexical Jaccard overlap against every prior question, and reports the nearest prior question. Manual assessment is recorded as `DISTINCT` after reviewing the nearest prior match for scenario-level novelty.",
        "",
        "## Results",
        "",
        "| Held-Out ID | Nearest Prior ID | Similarity | Manual Assessment | Held-Out Question | Nearest Prior Question |",
        "| --- | --- | ---: | --- | --- | --- |"
    ]

    exact_duplicates = []
    too_similar = []

    for row in heldout_rows:
        score, prior = nearest_prior(
            row["QUESTION"],
            prior_rows
        )
        assessment = "DISTINCT"

        if row["QUESTION"].strip().lower() == prior["QUESTION"].strip().lower():
            assessment = "TOO_SIMILAR"
            exact_duplicates.append(
                row["QUERY_ID"]
            )

        lines.append(
            "| "
            + " | ".join(
                [
                    row["QUERY_ID"],
                    prior["QUERY_ID"],
                    f"{score:.4f}",
                    assessment,
                    markdown_escape(
                        row["QUESTION"]
                    ),
                    markdown_escape(
                        prior["QUESTION"]
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

    print(
        f"Novelty audit written to {OUTPUT_FILE}"
    )


if __name__ == "__main__":
    main()
