import os
import re

import requests


REPO_OWNER = "SAP-docs"
REPO_NAME = "btp-cloud-platform"
BRANCH = "main"

TITLE = "Cloud Foundry Environment"


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

    return response.json()


if __name__ == "__main__":

    target_slug = slugify(TITLE)

    tree = get_repository_tree()

    matches = []

    for item in tree.get("tree", []):

        path = item.get("path", "")

        if (
            item.get("type") == "blob"
            and path.endswith(".md")
        ):

            filename = os.path.basename(path).lower()

            if filename.startswith(
                target_slug + "-"
            ):
                matches.append(path)

    print("Title:", TITLE)
    print("Search slug:", target_slug)
    print("Matches found:", len(matches))
    print()

    for path in matches:

        raw_url = (
            f"https://raw.githubusercontent.com/"
            f"{REPO_OWNER}/{REPO_NAME}/"
            f"{BRANCH}/{path}"
        )

        print("Repository path:")
        print(path)

        print()

        print("Raw content URL:")
        print(raw_url)

        print("-" * 70)