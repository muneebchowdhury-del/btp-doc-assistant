import csv

import requests


SOURCE_FILE = "data/document_sources.csv"


def load_first_source():
    with open(SOURCE_FILE, newline="", encoding="utf-8") as file:
        reader = csv.DictReader(file)
        return next(reader)


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


if __name__ == "__main__":

    source = load_first_source()

    print("Document:", source["DOCUMENT_ID"])
    print("Title:", source["TITLE"])
    print("SAP Help URL:", source["SOURCE_URL"])
    print("Content URL:", source["CONTENT_URL"])
    print()

    markdown = download_markdown(
        source["CONTENT_URL"]
    )

    print("Characters extracted:", len(markdown))
    print()
    print("First 1000 characters:")
    print("-" * 60)
    print(markdown[:1000])