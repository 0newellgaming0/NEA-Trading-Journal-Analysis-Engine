#!/usr/bin/env python3

"""
NEA28V1 GitHub Discussions Publisher

Repository:
    0newellgaming0/NEA-Trading-Journal-Analysis-Engine

Reads GitHub Discussions through the GitHub GraphQL API.

Writes:
    modules/signals_trading_web/dashboard/data/community.json
"""

from __future__ import annotations

import json
import os
import sys
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen


REPOSITORY = os.getenv(
    "GITHUB_REPOSITORY",
    "0newellgaming0/NEA-Trading-Journal-Analysis-Engine",
)

GRAPHQL_URL = "https://api.github.com/graphql"

FEATURED_LIMIT = int(
    os.getenv("COMMUNITY_FEATURED_LIMIT", "4")
)

RECENT_LIMIT = int(
    os.getenv("COMMUNITY_RECENT_LIMIT", "8")
)

CATEGORY_LIMIT = int(
    os.getenv("COMMUNITY_CATEGORY_LIMIT", "25")
)

DISCUSSION_FETCH_LIMIT = max(
    RECENT_LIMIT,
    FEATURED_LIMIT,
    25,
)

SCRIPT_DIR = Path(__file__).resolve().parent

DASHBOARD_DIR = (
    SCRIPT_DIR.parent /
    "dashboard"
)

OUTPUT_PATH = (
    DASHBOARD_DIR /
    "data" /
    "community.json"
)


QUERY = """
query CommunityData(
  $owner: String!,
  $name: String!,
  $discussionFirst: Int!,
  $categoryFirst: Int!
) {

  repository(
    owner: $owner,
    name: $name
  ) {

    name
    url

    discussions(
      first: $discussionFirst
      orderBy: {
        field: UPDATED_AT
        direction: DESC
      }
    ) {

      totalCount

      nodes {

        number
        title
        url
        bodyText
        createdAt
        updatedAt
        closed
        upvoteCount

        author {
          login
        }

        category {
          name
          emoji
          description
          slug
          isAnswerable
        }

        answer {
          id
        }

        comments {
          totalCount
        }
      }
    }

    pinnedDiscussions(
      first: 10
    ) {

      nodes {

        discussion {

          number
          title
          url
          bodyText
          createdAt
          updatedAt
          closed
          upvoteCount

          author {
            login
          }

          category {
            name
            emoji
            description
            slug
            isAnswerable
          }

          answer {
            id
          }

          comments {
            totalCount
          }
        }
      }
    }

    discussionCategories(
      first: $categoryFirst
    ) {

      nodes {

        id
        name
        emoji
        description
        slug
        isAnswerable
      }
    }
  }
}
"""


def fail(message: str, code: int = 1) -> None:
    print(
        f"[community] ERROR: {message}",
        file=sys.stderr,
    )
    raise SystemExit(code)


def parse_repository(value: str) -> tuple[str, str]:
    parts = value.strip().split("/", 1)

    if len(parts) != 2 or not all(parts):
        fail(
            "GITHUB_REPOSITORY must use owner/name format. "
            f"Received: {value!r}"
        )

    return parts[0], parts[1]


def github_graphql(
    token: str,
    query: str,
    variables: dict[str, Any],
) -> dict[str, Any]:

    payload = json.dumps(
        {
            "query": query,
            "variables": variables,
        }
    ).encode("utf-8")

    request = Request(
        GRAPHQL_URL,
        data=payload,
        headers={
            "Authorization": f"Bearer {token}",
            "Accept": "application/vnd.github+json",
            "Content-Type": "application/json",
            "User-Agent": "NEA28V1-Community-Publisher",
            "X-GitHub-Api-Version": "2022-11-28",
        },
        method="POST",
    )

    try:
        with urlopen(request, timeout=30) as response:
            raw = response.read().decode("utf-8")

    except HTTPError as exc:
        detail = exc.read().decode(
            "utf-8",
            errors="replace",
        )

        fail(
            f"GitHub GraphQL HTTP {exc.code}: {detail}"
        )

    except URLError as exc:
        fail(
            f"Unable to reach GitHub GraphQL API: {exc}"
        )

    try:
        payload = json.loads(raw)

    except json.JSONDecodeError as exc:
        fail(
            f"GitHub returned invalid JSON: {exc}"
        )

    if payload.get("errors"):

        messages = "; ".join(
            str(
                error.get(
                    "message",
                    "Unknown GraphQL error",
                )
            )
            for error in payload["errors"]
        )

        fail(
            f"GitHub GraphQL error: {messages}"
        )

    if "data" not in payload:
        fail(
            "GitHub GraphQL response did not contain data."
        )

    return payload["data"]


def clean_text(
    value: str | None,
    limit: int = 260,
) -> str:

    if not value:
        return ""

    text = " ".join(value.split())

    if len(text) <= limit:
        return text

    return (
        text[:limit - 1].rstrip()
        + "…"
    )


def normalize_discussion(
    node: dict[str, Any],
) -> dict[str, Any]:

    category = node.get("category") or {}
    author = node.get("author") or {}
    comments = node.get("comments") or {}

    return {
        "number": node.get("number"),
        "title": (
            node.get("title")
            or "Untitled discussion"
        ),
        "url": node.get("url"),
        "excerpt": clean_text(
            node.get("bodyText")
        ),
        "createdAt": node.get("createdAt"),
        "updatedAt": (
            node.get("updatedAt")
            or node.get("createdAt")
        ),
        "closed": bool(
            node.get("closed")
        ),
        "upvotes": int(
            node.get("upvoteCount")
            or 0
        ),
        "comments": int(
            comments.get("totalCount")
            or 0
        ),
        "answered": bool(
            node.get("answer")
        ),
        "author": author.get("login"),
        "category": (
            category.get("name")
            or "General"
        ),
        "categoryEmoji": (
            category.get("emoji")
            or ""
        ),
        "categorySlug": (
            category.get("slug")
            or ""
        ),
    }


def unique_discussions(
    items: list[dict[str, Any]],
) -> list[dict[str, Any]]:

    seen: set[int] = set()
    result: list[dict[str, Any]] = []

    for item in items:

        number = item.get("number")

        if number in seen:
            continue

        seen.add(number)
        result.append(item)

    return result


def choose_featured(
    pinned: list[dict[str, Any]],
    recent: list[dict[str, Any]],
) -> list[dict[str, Any]]:

    featured = unique_discussions(
        pinned
    )

    if len(featured) < FEATURED_LIMIT:

        existing = {
            item["number"]
            for item in featured
        }

        for item in recent:

            if len(featured) >= FEATURED_LIMIT:
                break

            if item["number"] not in existing:

                featured.append(item)

                existing.add(
                    item["number"]
                )

    return featured[:FEATURED_LIMIT]


def build_categories(
    repository: dict[str, Any],
    recent: list[dict[str, Any]],
) -> list[dict[str, Any]]:

    category_nodes = (
        repository
        .get("discussionCategories", {})
        .get("nodes")
        or []
    )

    counts = Counter(
        (
            item.get("category")
            or "General"
        )
        for item in recent
    )

    categories: list[dict[str, Any]] = []

    for node in category_nodes:

        if not node:
            continue

        name = (
            node.get("name")
            or "General"
        )

        categories.append(
            {
                "id": node.get("id"),
                "name": name,
                "emoji": (
                    node.get("emoji")
                    or ""
                ),
                "description": (
                    node.get("description")
                    or "Community discussion category."
                ),
                "slug": (
                    node.get("slug")
                    or ""
                ),
                "isAnswerable": bool(
                    node.get("isAnswerable")
                ),
                "discussionCount": counts.get(
                    name,
                    0,
                ),
            }
        )

    categories.sort(
        key=lambda item: (
            -item["discussionCount"],
            item["name"].lower(),
        )
    )

    return categories[:CATEGORY_LIMIT]


def calculate_topic_count(
    discussions: list[dict[str, Any]],
    names: set[str],
    slugs: set[str],
) -> int:

    count = 0

    for item in discussions:

        category_name = (
            item.get("category")
            or ""
        ).strip().lower()

        category_slug = (
            item.get("categorySlug")
            or ""
        ).strip().lower()

        if (
            category_name in names
            or category_slug in slugs
        ):
            count += 1

    return count


def build_payload(
    data: dict[str, Any],
) -> dict[str, Any]:

    repository = data["repository"]

    recent = [
        normalize_discussion(node)
        for node in (
            repository
            .get("discussions", {})
            .get("nodes")
            or []
        )
        if node
    ]

    pinned = [
        normalize_discussion(
            node.get("discussion") or {}
        )
        for node in (
            repository
            .get("pinnedDiscussions", {})
            .get("nodes")
            or []
        )
        if (
            node
            and node.get("discussion")
        )
    ]

    categories = build_categories(
        repository,
        recent,
    )

    question_count = calculate_topic_count(
        recent,
        names={
            "q&a",
            "q and a",
            "questions",
            "question",
        },
        slugs={
            "q-a",
            "qna",
            "questions",
            "question",
        },
    )

    idea_count = calculate_topic_count(
        recent,
        names={
            "ideas",
            "idea",
        },
        slugs={
            "ideas",
            "idea",
        },
    )

    total_discussions = int(
        repository
        .get("discussions", {})
        .get("totalCount")
        or 0
    )

    return {
        "repository": {
            "name": repository.get("name"),
            "url": repository.get("url"),
        },

        "updatedAt": datetime.now(
            timezone.utc
        ).isoformat(),

        "stats": {
            "total": total_discussions,
            "questions": question_count,
            "ideas": idea_count,
            "categories": len(categories),
        },

        "categories": categories,

        "featured": choose_featured(
            pinned,
            recent,
        ),

        "recent": recent[:RECENT_LIMIT],
    }


def write_json(
    payload: dict[str, Any],
) -> None:

    OUTPUT_PATH.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    temporary = OUTPUT_PATH.with_suffix(
        ".json.tmp"
    )

    with temporary.open(
        "w",
        encoding="utf-8",
        newline="\n",
    ) as handle:

        json.dump(
            payload,
            handle,
            indent=2,
            ensure_ascii=False,
        )

        handle.write("\n")

    temporary.replace(
        OUTPUT_PATH
    )


def main() -> None:

    token = os.getenv(
        "GITHUB_TOKEN",
        "",
    ).strip()

    if not token:
        fail(
            "GITHUB_TOKEN is not set. "
            "Set a GitHub token before running "
            "this publisher."
        )

    owner, name = parse_repository(
        REPOSITORY
    )

    print(
        f"[community] Repository: "
        f"{owner}/{name}"
    )

    print(
        "[community] Retrieving GitHub Discussions..."
    )

    data = github_graphql(
        token=token,
        query=QUERY,
        variables={
            "owner": owner,
            "name": name,
            "discussionFirst": DISCUSSION_FETCH_LIMIT,
            "categoryFirst": CATEGORY_LIMIT,
        },
    )

    payload = build_payload(
        data
    )

    write_json(
        payload
    )

    stats = payload["stats"]

    print(
        "[community] Published: "
        f"{stats['total']} discussions, "
        f"{stats['categories']} categories, "
        f"{len(payload['featured'])} featured, "
        f"{len(payload['recent'])} recent."
    )

    print(
        f"[community] Output: "
        f"{OUTPUT_PATH}"
    )


if __name__ == "__main__":
    main()