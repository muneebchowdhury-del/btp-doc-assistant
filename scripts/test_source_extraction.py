import csv

import requests
from bs4 import BeautifulSoup


SOURCE_FILE = "data/document_sources.csv"


def load_first_source():
    with open(SOURCE_FILE, newline="", encoding="utf-8") as file:
        reader = csv.DictReader(file)
        return next(reader)


def extract_text(url):
    response = requests.get(
        url,
        timeout=30,
        headers={
            "User-Agent": "Mozilla/5.0"
        }
    )

    response.raise_for_status()

    soup = BeautifulSoup(
        response.text,
        "html.parser"
    )

    for element in soup(
        ["script", "style", "nav", "footer", "header"]
    ):
        element.decompose()

    text = soup.get_text(
        separator=" ",
        strip=True
    )

    return text


if __name__ == "__main__":

    source = load_first_source()

    print("Document:", source["DOCUMENT_ID"])
    print("Title:", source["TITLE"])
    print("URL:", source["SOURCE_URL"])

    text = extract_text(
        source["SOURCE_URL"]
    )

    print("Characters extracted:", len(text))
    print()
    print("First 1000 characters:")
    print("-" * 60)
    print(text[:1000])