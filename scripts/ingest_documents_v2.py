import csv
import json
import os
import re

import requests
from fastembed import TextEmbedding
from hdbcli import dbapi


SOURCE_FILE = "data/document_sources_v2.csv"

MODEL_NAME = "BAAI/bge-small-en-v1.5"

HDI_SERVICE_NAME = "btp-doc-assistant-hdi"

TABLE_NAME = "DOCUMENT_CHUNKS_V2"

CHUNK_SIZE_WORDS = 120
CHUNK_OVERLAP_WORDS = 25


def get_hana_credentials():
    raw_services = os.environ.get("VCAP_SERVICES")

    if not raw_services:
        raise RuntimeError(
            "VCAP_SERVICES is not available. "
            "Run this script inside the bound Cloud Foundry application."
        )

    services = json.loads(raw_services)

    hana_services = services.get("hana", [])

    for service in hana_services:
        if service.get("name") == HDI_SERVICE_NAME:
            return service["credentials"]

    raise RuntimeError(
        f"HDI service '{HDI_SERVICE_NAME}' "
        "was not found in VCAP_SERVICES."
    )


def get_hana_connection():
    credentials = get_hana_credentials()

    connection = dbapi.connect(
        address=credentials["host"],
        port=int(credentials["port"]),
        user=credentials["user"],
        password=credentials["password"]
    )

    schema = credentials.get("schema")

    if not schema:
        connection.close()
        raise RuntimeError(
            "HDI container schema missing "
            "from service binding."
        )

    cursor = connection.cursor()

    try:
        cursor.execute(
            f'SET SCHEMA "{schema}"'
        )
    finally:
        cursor.close()

    return connection


def download_markdown(url):
    response = requests.get(
        url,
        timeout=30,
        headers={
            "User-Agent": "btp-doc-assistant"
        }
    )

    response.raise_for_status()

    return response.text


def clean_markdown(text):
    # Remove SAP LOIO metadata comments.
    text = re.sub(
        r"<!--.*?-->",
        "",
        text,
        flags=re.DOTALL
    )

    # Remove Markdown images.
    text = re.sub(
        r"!\[[^\]]*\]\([^)]+\)",
        "",
        text
    )

    # Keep link text while removing link targets.
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

    # Exclude navigation-heavy Related Information section.
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


def vector_to_string(vector):
    return json.dumps(
        [float(value) for value in vector]
    )


def load_sources():
    with open(
        SOURCE_FILE,
        newline="",
        encoding="utf-8"
    ) as file:
        return list(csv.DictReader(file))


def main():
    print("Loading V2 embedding model...")
    model = TextEmbedding(
        model_name=MODEL_NAME
    )

    sources = load_sources()

    records = []

    print("Preparing V2 documentation chunks...")

    for source in sources:
        content_url = (
            source.get("CONTENT_URL") or ""
        ).strip()

        if not content_url:
            print(
                f"Skipping {source['DOCUMENT_ID']} "
                "- no CONTENT_URL"
            )
            continue

        print(
            f"Processing {source['DOCUMENT_ID']}: "
            f"{source['TITLE']}"
        )

        markdown = download_markdown(
            content_url
        )

        cleaned = clean_markdown(
            markdown
        )

        chunks = chunk_text(
            cleaned
        )

        for chunk_index, chunk in enumerate(chunks):
            records.append({
                "document_id":
                    source["DOCUMENT_ID"],

                "chunk_index":
                    chunk_index,

                "title":
                    source["TITLE"],

                "topic":
                    source["TOPIC"],

                "source_url":
                    source["SOURCE_URL"],

                "chunk_text":
                    chunk
            })

    print(
        f"Total V2 chunks prepared: {len(records)}"
    )

    passages = [
        record["chunk_text"]
        for record in records
    ]

    print("Generating V2 passage embeddings...")

    vectors = list(
        model.passage_embed(passages)
    )

    if len(vectors) != len(records):
        raise RuntimeError(
            "Embedding count does not match "
            "chunk count."
        )

    print(
        f"V2 embeddings generated: {len(vectors)}"
    )

    print("Connecting to SAP HANA Cloud...")

    connection = get_hana_connection()
    cursor = connection.cursor()

    try:
        cursor.execute(
            f'DELETE FROM "{TABLE_NAME}"'
        )

        insert_sql = f"""
            INSERT INTO "{TABLE_NAME}" (
                "CHUNK_ID",
                "DOCUMENT_ID",
                "CHUNK_INDEX",
                "TITLE",
                "TOPIC",
                "SOURCE_URL",
                "CHUNK_TEXT",
                "EMBEDDING",
                "INGESTED_AT"
            )
            VALUES (
                ?, ?, ?, ?, ?, ?, ?,
                TO_REAL_VECTOR(?),
                CURRENT_UTCTIMESTAMP
            )
        """

        for chunk_id, (record, vector) in enumerate(
            zip(records, vectors),
            start=1
        ):
            cursor.execute(
                insert_sql,
                (
                    chunk_id,
                    record["document_id"],
                    record["chunk_index"],
                    record["title"],
                    record["topic"],
                    record["source_url"],
                    record["chunk_text"],
                    vector_to_string(vector)
                )
            )

        connection.commit()

        cursor.execute(
            f'SELECT COUNT(*) FROM "{TABLE_NAME}"'
        )

        row_count = cursor.fetchone()[0]

        print()
        print("V2 ingestion completed successfully.")
        print(
            f"Rows in {TABLE_NAME}:",
            row_count
        )
        print(
            "Embedding model:",
            MODEL_NAME
        )
        print(
            "Vector dimension:",
            len(vectors[0])
        )

    except Exception:
        connection.rollback()
        raise

    finally:
        cursor.close()
        connection.close()


if __name__ == "__main__":
    main()
