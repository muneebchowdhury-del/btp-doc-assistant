import csv
import os
import re

import requests


SOURCE_FILE = "data/document_sources.csv"

REPO_OWNER = "SAP-docs"
REPO_NAME = "btp-cloud-platform"
BRANCH = "main"


def slugify(text):
    text = text.lower()
    text = re.sub(r"[^a-z0-9]+", "-", text)
    return text.strip("-")


def get_repository_tree():
    url = (
        f"https://api.github.com/repos/"
        f"{REPO_OWNER}/{REPO_NAME}/git/trees/"
        f"{BRANCH}?recursive=1"
    )

    response = requests.get(
        url,
        timeout=30,
        headers={
            "Accept": "application/vnd.github+json",
            "User-Agent": "btp-doc-assistant"
        }
    )

    response.raise_for_status()

    return response.json().get("tree", [])


def find_matches(title, tree):
    target_slug = slugify(title)

    matches = []

    for item in tree:

        path = item.get("path", "")

        if (
            item.get("type") == "blob"
            and path.endswith(".md")
        ):

            filename = os.path.basename(path).lower()

            if filename.startswith(target_slug + "-"):
                matches.append(path)

    return matches


def raw_url(path):
    return (
        f"https://raw.githubusercontent.com/"
        f"{REPO_OWNER}/{REPO_NAME}/"
        f"{BRANCH}/{path}"
    )


if __name__ == "__main__":

    tree = get_repository_tree()

    with open(
        SOURCE_FILE,
        newline="",
        encoding="utf-8"
    ) as file:

        rows = list(
            csv.DictReader(file)
        )
    for row in rows:
        row["CONTENT_URL"] = row.get("CONTENT_URL") or ""

    fieldnames = [
        "DOCUMENT_ID",
        "TITLE",
        "TOPIC",
        "SOURCE_URL",
        "CONTENT_URL"
    ]

    for row in rows:

        # Keep URLs we already resolved.
        if (row.get("CONTENT_URL") or "").strip():
            print(
                row["DOCUMENT_ID"],
                "already resolved"
            )
            continue

        # Only resolve SAP BTP documentation here.
        if "/btp/" not in row["SOURCE_URL"].lower():
            print(
                row["DOCUMENT_ID"],
                "skipped - separate repository"
            )
            continue

        matches = find_matches(
            row["TITLE"],
            tree
        )

        if len(matches) == 1:

            row["CONTENT_URL"] = raw_url(
                matches[0]
            )

            print(
                row["DOCUMENT_ID"],
                "resolved:",
                matches[0]
            )

        elif len(matches) == 0:

            print(
                row["DOCUMENT_ID"],
                "UNRESOLVED"
            )

        else:

            print(
                row["DOCUMENT_ID"],
                "AMBIGUOUS:",
                matches
            )

    with open(
        SOURCE_FILE,
        "w",
        newline="",
        encoding="utf-8"
    ) as file:

        writer = csv.DictWriter(
            file,
            fieldnames=fieldnames
        )

        writer.writeheader()
        writer.writerows(rows)

    print()
    print("Source file updated.")