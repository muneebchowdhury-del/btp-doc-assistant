import csv
import re
import requests


SOURCE_FILE = "data/document_sources.csv"

CHUNK_SIZE_WORDS = 120
CHUNK_OVERLAP_WORDS = 25


def download_markdown(url):
    response = requests.get(
        url,
        timeout=30,
        headers={"User-Agent": "btp-doc-assistant"}
    )

    response.raise_for_status()

    return response.text


def clean_markdown(text):
    # Remove SAP metadata comments.
    text = re.sub(
        r"<!--.*?-->",
        "",
        text,
        flags=re.DOTALL
    )

    # Remove images.
    text = re.sub(
        r"!\[[^\]]*\]\([^)]+\)",
        "",
        text
    )

    # Keep link text, remove link target.
    text = re.sub(
        r"\[([^\]]+)\]\([^)]+\)",
        r"\1",
        text
    )

    # Remove Markdown headings.
    text = re.sub(
        r"^#{1,6}\s*",
        "",
        text,
        flags=re.MULTILINE
    )

    text = text.replace("**", "")
    text = text.replace("__", "")
    text = text.replace("`", "")

    # Remove Related Information section.
    text = re.split(
        r"\n\s*Related Information\s*\n",
        text,
        flags=re.IGNORECASE
    )[0]

    # Remove remaining HTML tags / anchors.
    text = re.sub(
        r"<[^>]+>",
        " ",
        text
    )

    # Remove Markdown escape backslashes.
    text = re.sub(
        r"\\([*#>\[\]()_`-])",
        r"\1",
        text
    )

    # Remove blockquote markers.
    text = re.sub(
        r"(?m)^\s*>\s*",
        "",
        text
    )
    # Normalize whitespace.
    text = re.sub(
        r"\s+",
        " ",
        text
    ).strip()

    return text


def chunk_text(text):
    words = text.split()

    chunks = []
    start = 0

    while start < len(words):

        end = start + CHUNK_SIZE_WORDS

        chunk = " ".join(
            words[start:end]
        ).strip()

        if chunk:
            chunks.append(chunk)

        if end >= len(words):
            break

        start = end - CHUNK_OVERLAP_WORDS

    return chunks


if __name__ == "__main__":

    total_chunks = 0
    total_words = 0

    print(
        f"{'ID':<8}"
        f"{'WORDS':<10}"
        f"{'CHUNKS':<10}"
        f"{'TITLE'}"
    )

    print("-" * 90)

    with open(
        SOURCE_FILE,
        newline="",
        encoding="utf-8"
    ) as file:

        reader = csv.DictReader(file)

        for source in reader:

            content_url = (
                source.get("CONTENT_URL") or ""
            ).strip()

            if not content_url:
                print(
                    f"{source['DOCUMENT_ID']:<8}"
                    f"{'-':<10}"
                    f"{'SKIPPED':<10}"
                    f"{source['TITLE']}"
                )
                continue

            markdown = download_markdown(
                content_url
            )

            cleaned = clean_markdown(
                markdown
            )

            word_count = len(
                cleaned.split()
            )

            chunks = chunk_text(
                cleaned
            )

            total_words += word_count
            total_chunks += len(chunks)

            print(
                f"{source['DOCUMENT_ID']:<8}"
                f"{word_count:<10}"
                f"{len(chunks):<10}"
                f"{source['TITLE']}"
            )

    print("-" * 90)

    print(
        "Total words:",
        total_words
    )

    print(
        "Total chunks:",
        total_chunks
    )