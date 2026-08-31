import csv

import requests


SOURCE_FILE = "data/document_sources.csv"


def download_text(url):
    response = requests.get(
        url,
        timeout=30,
        headers={
            "User-Agent": "btp-doc-assistant"
        }
    )

    response.raise_for_status()

    return response.text


if __name__ == "__main__":

    with open(
        SOURCE_FILE,
        newline="",
        encoding="utf-8"
    ) as file:

        rows = list(csv.DictReader(file))

    print(
        f"{'ID':<8}"
        f"{'STATUS':<12}"
        f"{'CHARS':<10}"
        f"TITLE"
    )

    print("-" * 80)

    for row in rows:

        document_id = row["DOCUMENT_ID"]
        title = row["TITLE"]

        content_url = (
            row.get("CONTENT_URL") or ""
        ).strip()

        if not content_url:

            print(
                f"{document_id:<8}"
                f"{'SKIPPED':<12}"
                f"{'-':<10}"
                f"{title}"
            )

            continue

        try:

            text = download_text(
                content_url
            )

            status = (
                "OK"
                if len(text) > 500
                else "TOO SMALL"
            )

            print(
                f"{document_id:<8}"
                f"{status:<12}"
                f"{len(text):<10}"
                f"{title}"
            )

        except Exception as error:

            print(
                f"{document_id:<8}"
                f"{'ERROR':<12}"
                f"{'-':<10}"
                f"{title}"
            )

            print(
                f"         {error}"
            )