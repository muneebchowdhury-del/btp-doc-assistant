import argparse
import csv
from statistics import mean


OBSERVABLE_OUTCOMES = {
    "GENERATED_ANSWER",
    "LLM_REFUSAL"
}
MANUAL_METRIC_FIELDS = (
    "GROUNDEDNESS",
    "ANSWER_CORRECTNESS",
    "CITATION_CORRECTNESS",
    "HALLUCINATION",
    "EVIDENCE_BASED_REFUSAL",
    "CONCISION"
)


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


def evidence_outcome(row):
    if row.get(
        "EVIDENCE_SOURCE",
        ""
    ) == "SECONDARY_RETRY":
        return row.get(
            "SECONDARY_RETRY_OUTCOME",
            ""
        ).strip()

    return row.get(
        "PRIMARY_OUTCOME",
        row.get(
            "OUTCOME",
            ""
        )
    ).strip()


def is_observable(row):
    return evidence_outcome(
        row
    ) in OBSERVABLE_OUTCOMES


def ensure_scored(rows):
    unscored = [
        row.get(
            "QUERY_ID",
            ""
        )
        for row in rows
        if is_observable(
            row
        )
        and row.get(
            "SCORING_STATUS",
            ""
        ).strip()
        != "SCORED"
    ]

    if unscored:
        raise ValueError(
            "Manual scoring is incomplete for observable row(s): "
            + ", ".join(
                unscored
            )
        )


def rate(rows, field, positive_value="1"):
    applicable = [
        row
        for row in rows
        if str(
            row.get(
                field,
                ""
            )
        ).strip()
        != ""
    ]

    if not applicable:
        return (
            0,
            0,
            None
        )

    positive = sum(
        1
        for row in applicable
        if row.get(
            field,
            ""
        ).strip()
        == positive_value
    )

    return (
        positive,
        len(
            applicable
        ),
        positive
        / len(
            applicable
        )
    )


def numeric_mean(rows, field):
    values = [
        float(
            row[field]
        )
        for row in rows
        if str(
            row.get(
                field,
                ""
            )
        ).strip()
        != ""
    ]

    if not values:
        return (
            0,
            None
        )

    return (
        len(
            values
        ),
        mean(
            values
        )
    )


def count_outcomes(rows):
    counts = {}

    for row in rows:
        outcome = evidence_outcome(
            row
        )
        counts[outcome] = counts.get(
            outcome,
            0
        ) + 1

    return counts


def summarize_pipeline(primary_rows):
    counts = count_outcomes(
        primary_rows
    )
    return {
        "total_queries": len(
            primary_rows
        ),
        "accepts": sum(
            1
            for row in primary_rows
            if row.get(
                "ACCEPT_DECISION",
                ""
            )
            == "ACCEPT"
        ),
        "abstains": sum(
            1
            for row in primary_rows
            if row.get(
                "ACCEPT_DECISION",
                ""
            )
            == "ABSTAIN"
        ),
        "provider_calls": sum(
            1
            for row in primary_rows
            if row.get(
                "GENERATION_OBSERVABILITY",
                ""
            )
            != "NOT_CALLED"
        ),
        "provider_errors": counts.get(
            "PROVIDER_ERROR",
            0
        ),
        "generated_answers": counts.get(
            "GENERATED_ANSWER",
            0
        ),
        "llm_refusals": counts.get(
            "LLM_REFUSAL",
            0
        )
    }


def summarize_reliability(rows):
    attempted = [
        row
        for row in rows
        if row.get(
            "GENERATION_OBSERVABILITY",
            ""
        )
        != "NOT_CALLED"
    ]
    observable = [
        row
        for row in attempted
        if is_observable(
            row
        )
    ]
    provider_errors = [
        row
        for row in attempted
        if evidence_outcome(
            row
        )
        == "PROVIDER_ERROR"
    ]

    return {
        "attempted_generations": len(
            attempted
        ),
        "successful_observable_generations": len(
            observable
        ),
        "provider_error_count": len(
            provider_errors
        ),
        "provider_error_rate": (
            None
            if not attempted
            else len(
                provider_errors
            )
            / len(
                attempted
            )
        )
    }


def format_rate(item):
    positive, total, value = item

    if value is None:
        return f"n/a ({positive}/{total})"

    return f"{value:.4f} ({positive}/{total})"


def format_optional_float(value):
    if value is None:
        return "n/a"

    return f"{value:.4f}"


def summarize_manual_metrics(rows):
    scored_observable = [
        row
        for row in rows
        if is_observable(
            row
        )
    ]
    concision_count, concision_mean = numeric_mean(
        scored_observable,
        "CONCISION"
    )

    return {
        "groundedness": rate(
            scored_observable,
            "GROUNDEDNESS"
        ),
        "answer_correctness": rate(
            scored_observable,
            "ANSWER_CORRECTNESS"
        ),
        "citation_correctness": rate(
            scored_observable,
            "CITATION_CORRECTNESS"
        ),
        "hallucination": rate(
            scored_observable,
            "HALLUCINATION"
        ),
        "evidence_based_refusal": rate(
            scored_observable,
            "EVIDENCE_BASED_REFUSAL"
        ),
        "concision_count": concision_count,
        "concision_mean": concision_mean
    }


def print_summary(rows):
    ensure_scored(
        rows
    )

    primary_rows = [
        row
        for row in rows
        if row.get(
            "EVIDENCE_SOURCE",
            ""
        )
        == "PRIMARY"
    ]
    secondary_rows = [
        row
        for row in rows
        if row.get(
            "EVIDENCE_SOURCE",
            ""
        )
        == "SECONDARY_RETRY"
    ]

    pipeline = summarize_pipeline(
        primary_rows
    )
    print(
        "Primary pipeline outcomes"
    )
    for key, value in pipeline.items():
        print(
            f"- {key}: {value}"
        )

    print(
        "\nProvider reliability - PRIMARY"
    )
    primary_reliability = summarize_reliability(
        primary_rows
    )
    for key, value in primary_reliability.items():
        print(
            f"- {key}: {format_optional_float(value) if isinstance(value, float) else value}"
        )

    if secondary_rows:
        print(
            "\nProvider reliability - SECONDARY_RETRY"
        )
        secondary_reliability = summarize_reliability(
            secondary_rows
        )
        for key, value in secondary_reliability.items():
            print(
                f"- {key}: {format_optional_float(value) if isinstance(value, float) else value}"
            )

    print(
        "\nManually scored observable LLM outputs"
    )
    metrics = summarize_manual_metrics(
        rows
    )
    print(
        f"- groundedness rate: {format_rate(metrics['groundedness'])}"
    )
    print(
        f"- answer correctness rate: {format_rate(metrics['answer_correctness'])}"
    )
    print(
        f"- citation correctness rate: {format_rate(metrics['citation_correctness'])}"
    )
    print(
        f"- hallucination rate: {format_rate(metrics['hallucination'])}"
    )
    print(
        f"- evidence-based refusal correctness: {format_rate(metrics['evidence_based_refusal'])}"
    )
    print(
        "- mean concision score: "
        f"{format_optional_float(metrics['concision_mean'])} "
        f"({metrics['concision_count']} applicable)"
    )


def parse_args():
    parser = argparse.ArgumentParser(
        description="Summarize completed manual V2 RAG development scoring."
    )
    parser.add_argument(
        "scored_file"
    )
    return parser.parse_args()


def main():
    args = parse_args()
    print_summary(
        read_csv_rows(
            args.scored_file
        )
    )


if __name__ == "__main__":
    main()
