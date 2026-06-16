#!/usr/bin/env python3
"""Create a new Hugo post scaffold in a category section."""

from __future__ import annotations

import argparse
import re
import sys
from datetime import datetime
from pathlib import Path

from blog_config import CATEGORIES, CONTENT_DIR


def slugify(text: str) -> str:
    slug = text.lower().strip()
    slug = re.sub(r"[^a-z0-9\s-]", "", slug)
    slug = re.sub(r"[\s_]+", "-", slug)
    slug = re.sub(r"-+", "-", slug).strip("-")
    if slug:
        return slug
    return datetime.now().strftime("post-%Y%m%d-%H%M%S")


def build_front_matter(title: str, category: str, draft: bool = True) -> str:
    now = datetime.now().strftime("%Y-%m-%dT%H:%M:%S+09:00")
    draft_value = "true" if draft else "false"
    return f"""---
title: "{title}"
date: {now}
draft: {draft_value}
tags: []
categories: ["{category}"]
description: ""
ShowToc: true
TocOpen: false
---

"""


def create_post(category: str, slug: str, title: str, draft: bool = True) -> Path:
    if category not in CATEGORIES:
        raise ValueError(f"Unknown category: {category}. Choose from: {', '.join(CATEGORIES)}")

    post_dir = CONTENT_DIR / category / slug
    post_file = post_dir / "index.md"

    if post_file.exists():
        raise FileExistsError(f"Post already exists: {post_file}")

    post_dir.mkdir(parents=True, exist_ok=False)
    post_file.write_text(build_front_matter(title, category, draft), encoding="utf-8")
    return post_file


def main() -> int:
    parser = argparse.ArgumentParser(description="Create a new Hugo post scaffold.")
    parser.add_argument("category", choices=CATEGORIES, help="Post section/category")
    parser.add_argument("slug", nargs="?", help="URL slug (e.g. asyncio-basics)")
    parser.add_argument("--title", "-t", help="Post title")
    parser.add_argument("--publish", action="store_true", help="Create as draft: false")
    args = parser.parse_args()

    title = args.title or (args.slug or "").replace("-", " ").title()
    if not title:
        print("Error: provide --title or slug.", file=sys.stderr)
        return 1

    slug = args.slug or slugify(title)
    draft = not args.publish

    try:
        post_file = create_post(args.category, slug, title, draft=draft)
    except FileExistsError as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 1

    print(f"Created: {post_file}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
