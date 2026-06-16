#!/usr/bin/env python3
"""Prepare an agent prompt and draft scaffold for AI article generation."""

from __future__ import annotations

import argparse
import sys
from datetime import datetime
from pathlib import Path

from blog_config import CATEGORIES, DRAFTS_DIR, PROMPTS_DIR
from create_post import build_front_matter, slugify


def render_prompt(template: str, category: str, topic: str, slug: str) -> str:
    today = datetime.now().strftime("%Y-%m-%dT%H:%M:%S+09:00")
    return (
        template.replace("{{CATEGORY}}", category)
        .replace("{{TOPIC}}", topic)
        .replace("{{SLUG}}", slug)
        .replace("{{DATE}}", today)
    )


def main() -> int:
    parser = argparse.ArgumentParser(description="Generate agent prompt for a blog article.")
    parser.add_argument("--category", "-c", required=True, choices=CATEGORIES)
    parser.add_argument("--topic", "-t", required=True, help="Article topic")
    parser.add_argument("--slug", "-s", help="URL slug (auto-generated if omitted)")
    parser.add_argument(
        "--output",
        "-o",
        type=Path,
        help="Write prompt to this file (default: content/drafts/<slug>/agent-prompt.md)",
    )
    parser.add_argument(
        "--scaffold",
        action="store_true",
        help="Also create draft index.md scaffold",
    )
    parser.add_argument("--print", dest="print_prompt", action="store_true", help="Print prompt to stdout")
    args = parser.parse_args()

    slug = args.slug or slugify(args.topic)
    prompt_template = (PROMPTS_DIR / "article.md").read_text(encoding="utf-8")
    prompt = render_prompt(prompt_template, args.category, args.topic, slug)

    draft_dir = DRAFTS_DIR / slug
    draft_dir.mkdir(parents=True, exist_ok=True)

    prompt_path = args.output or (draft_dir / "agent-prompt.md")
    prompt_path.parent.mkdir(parents=True, exist_ok=True)
    prompt_path.write_text(prompt, encoding="utf-8")

    if args.scaffold:
        scaffold_path = draft_dir / "index.md"
        if not scaffold_path.exists():
            title = args.topic
            scaffold_path.write_text(
                build_front_matter(title, args.category, draft=True),
                encoding="utf-8",
            )
            print(f"Scaffold: {scaffold_path}")

    print(f"Prompt: {prompt_path}")
    if args.print_prompt:
        print("\n---\n")
        print(prompt)

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
