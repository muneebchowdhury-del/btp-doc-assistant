import csv
import re
import requests


SOURCE_FILE = "data/document_sources.csv"

CHUNK_SIZE_WORDS = 160
CHUNK_OVERLAP_WORDS = 30


def load_first_source():
    with open(SOURCE_FILE, newline="", encoding="utf-8") as file:
        reader = csv.DictReader(file)
        return next(reader)


def download_markdown(url):
    response = requests.get(
        url,
        timeout=30,
        headers={"User-Agent": "btp-doc-assistant"}
    )
    response.raise_for_status()
    return response.text


def clean_markdown(text):
    # Remove SAP LOIO metadata comments.
    text = re.sub(r"<!--.*?-->", "", text, flags=re.DOTALL)

    # Remove images but keep ordinary link text.
    text = re.sub(r"!\[[^\]]*\]\([^)]+\)", "", text)
    text = re.sub(r"\[([^\]]+)\]\([^)]+\)", r"\1", text)

    # Remove common Markdown formatting characters.
    text = re.sub(r"^#{1,6}\s*", "", text, flags=re.MULTILINE)
    text = text.replace("**", "")
    text = text.replace("__", "")
    text = text.replace("`", "")

    # Remove the Related Information section.
    text = re.split(
        r"\n\s*Related Information\s*\n",
        text,
        flags=re.IGNORECASE
    )[0]

    # Normalize whitespace.
    text = re.sub(r"\s+", " ", text).strip()

    return text


def chunk_text(text):
    words = text.split()

    chunks = []
    start = 0

    while start < len(words):
        end = start + CHUNK_SIZE_WORDS

        chunk = " ".join(words[start:end]).strip()

        if chunk:
            chunks.append(chunk)

        if end >= len(words):
            break

        start = end - CHUNK_OVERLAP_WORDS

    return chunks


if __name__ == "__main__":
    source = load_first_source()

    markdown = download_markdown(
        source["CONTENT_URL"]
    )

    cleaned = clean_markdown(markdown)

    chunks = chunk_text(cleaned)

    print("Document:", source["DOCUMENT_ID"])
    print("Title:", source["TITLE"])
    print("Original characters:", len(markdown))
    print("Cleaned characters:", len(cleaned))
    print("Chunks created:", len(chunks))
    print()

    for index, chunk in enumerate(chunks, start=1):
        print("=" * 70)
        print(f"CHUNK {index}")
        print("=" * 70)
        print(chunk)
        print()