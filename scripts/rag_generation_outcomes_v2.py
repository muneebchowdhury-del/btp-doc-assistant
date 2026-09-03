def classify_provider_answer(answer):
    normalized = str(
        answer or ""
    ).lower()

    refusal_markers = (
        "available documentation is insufficient",
        "documentation is insufficient",
        "supplied evidence is insufficient",
        "evidence is insufficient",
        "insufficient evidence"
    )

    if any(
        marker in normalized
        for marker in refusal_markers
    ):
        return "LLM_REFUSAL"

    return "GENERATED_ANSWER"
