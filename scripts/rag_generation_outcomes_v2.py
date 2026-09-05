import re


def classify_provider_answer(answer):
    normalized = " ".join(
        str(answer or "").lower().split()
    )

    if not normalized:
        return "LLM_REFUSAL"

    first_sentence = re.split(
        r"(?<=[.!?])\s+",
        normalized,
        maxsplit=1
    )[0]

    refusal_openers = (
        "the available documentation",
        "the supplied documentation",
        "the supplied sap documentation",
        "the provided documentation",
        "the provided sap documentation",
        "the retrieved documentation",
        "the retrieved sap documentation",
        "based on the provided documentation",
        "based on the provided documents",
        "based on the retrieved evidence",
        "the supplied evidence",
        "the available evidence",
        "none of the retrieved"
    )

    no_support_markers = (
        "is insufficient",
        "does not contain",
        "do not contain",
        "not supported by the supplied",
        "not supported by the provided",
        "cannot answer",
        "can't answer"
    )

    if (
        first_sentence.startswith(refusal_openers)
        and any(
            marker in first_sentence
            for marker in no_support_markers
        )
    ):
        return "LLM_REFUSAL"

    scoped_limitation_markers = (
        "available documentation is insufficient",
        "documentation is insufficient",
        "supplied evidence is insufficient",
        "evidence is insufficient",
        "insufficient evidence",
        "not supported by the supplied sources",
        "not supported by the supplied evidence",
        "does not contain detailed",
        "does not contain step-by-step",
        "further documentation would be needed"
    )

    if any(
        marker in normalized
        for marker in scoped_limitation_markers
    ):
        return "PARTIAL_ANSWER_SCOPED_ABSTENTION"

    return "GENERATED_ANSWER"
