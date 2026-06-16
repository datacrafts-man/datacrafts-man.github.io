#!/usr/bin/env python3
"""Publish draft posts: move from drafts, set draft false, commit and push."""

from __future__ import annotations

import argparse
import re
import subprocess
import sys
from pathlib import Path

from blog_config import CATEGORIES, CONTENT_DIR, DRAFTS_DIR, ROOT


FRONT_MATTER_RE = re.compile(r"^---\s*\n(.*?)\n---", re.DOTALL)


def set_draft_false(path: Path) -> None:
    text = path.read_text(encoding="utf-8")
    updated = re.sub(r"^draft:\s*true\s*$", "draft: false", text, count=1, flags=re.MULTILINE)
    path.write_text(updated, encoding="utf-8")


def move_draft_to_category(draft_slug: str, category: str, slug: str | None = None) -> Path:
    draft_file = DRAFTS_DIR / draft_slug / "index.md"
    if not draft_file.exists():
        raise FileNotFoundError(f"Draft not found: {draft_file}")

    target_slug = slug or draft_slug
    target_file = CONTENT_DIR / category / target_slug / "index.md"

    if target_file.exists():
        raise FileExistsError(f"Target already exists: {target_file}")

    target_file.parent.mkdir(parents=True, exist_ok=True)
    target_file.write_text(draft_file.read_text(encoding="utf-8"), encoding="utf-8")
    set_draft_false(target_file)
    return target_file


def run_git(args: list[str]) -> None:
    subprocess.run(["git", *args], cwd=ROOT, check=True)


def main() -> int:
    parser = argparse.ArgumentParser(description="Publish blog posts via git.")
    sub = parser.add_subparsers(dest="command", required=True)

    move_cmd = sub.add_parser("move", help="Move draft to category and set draft: false")
    move_cmd.add_argument("draft_slug", help="Draft folder name under content/drafts/")
    move_cmd.add_argument("category", choices=CATEGORIES)
    move_cmd.add_argument("--slug", help="Target slug (default: same as draft_slug)")

    pub_cmd = sub.add_parser("commit", help="Git add, commit, and push")
    pub_cmd.add_argument("paths", nargs="*", help="Files/dirs to add (default: content/)")
    pub_cmd.add_argument("-m", "--message", required=True, help="Commit message")
    pub_cmd.add_argument("--no-push", action="store_true", help="Commit only, do not push")

    args = parser.parse_args()

    try:
        if args.command == "move":
            target = move_draft_to_category(args.draft_slug, args.category, args.slug)
            print(f"Published draft to: {target}")
            return 0

        paths = [str(p) for p in args.paths] if args.paths else ["content/"]
        run_git(["add", *paths])
        run_git(["commit", "-m", args.message])
        if not args.no_push:
            run_git(["push"])
            print("Pushed to origin.")
        else:
            print("Committed locally (not pushed).")
        return 0

    except (FileNotFoundError, FileExistsError, subprocess.CalledProcessError) as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
