#!/usr/bin/env python3
"""Validate Hugo post front matter and SEO basics."""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

from blog_config import CATEGORIES, CONTENT_DIR


FRONT_MATTER_RE = re.compile(r"^---\s*\n(.*?)\n---", re.DOTALL)
FIELD_RE = re.compile(r"^(\w+):\s*(.+)$", re.MULTILINE)


def parse_front_matter(text: str) -> dict[str, str]:
    match = FRONT_MATTER_RE.match(text)
    if not match:
        return {}

    fields: dict[str, str] = {}
    for key, value in FIELD_RE.findall(match.group(1)):
        fields[key] = value.strip().strip('"').strip("'")
    return fields


def check_post(path: Path) -> list[str]:
    issues: list[str] = []
    text = path.read_text(encoding="utf-8")
    fm = parse_front_matter(text)

    if not fm:
        issues.append("front matter가 없습니다.")
        return issues

    title = fm.get("title", "")
    description = fm.get("description", "")
    categories = fm.get("categories", "")
    tags = fm.get("tags", "")

    if not title:
        issues.append("title이 비어 있습니다.")
    elif len(title) > 40:
        issues.append(f"title이 깁니다 ({len(title)}자). 40자 이내 권장.")

    if not description:
        issues.append("description이 비어 있습니다.")
    elif len(description) < 80:
        issues.append(f"description이 짧습니다 ({len(description)}자). 120~160자 권장.")
    elif len(description) > 180:
        issues.append(f"description이 깁니다 ({len(description)}자). 160자 이내 권장.")

    if not categories:
        issues.append("categories가 비어 있습니다.")
    else:
        for cat in re.findall(r'"([^"]+)"', categories):
            if cat not in CATEGORIES:
                issues.append(f"알 수 없는 category: {cat}")

    if not tags or tags == "[]":
        issues.append("tags가 비어 있습니다. 2~5개 권장.")

    body = FRONT_MATTER_RE.sub("", text).strip()
    if not body:
        issues.append("본문이 비어 있습니다.")
    if re.search(r"^#\s", body, re.MULTILINE):
        issues.append("본문에 H1(#)이 있습니다. H2(##)부터 사용하세요.")

    if fm.get("draft") == "true":
        issues.append("draft: true 상태입니다. 발행 전 false로 변경하세요.")

    return issues


def collect_posts(target: Path) -> list[Path]:
    if target.is_file():
        return [target]
    return sorted(target.rglob("index.md"))


def main() -> int:
    parser = argparse.ArgumentParser(description="Check SEO and front matter for Hugo posts.")
    parser.add_argument(
        "path",
        nargs="?",
        default=str(CONTENT_DIR),
        help="Post file or directory (default: content/)",
    )
    parser.add_argument("--drafts-only", action="store_true", help="Only check draft: true posts")
    args = parser.parse_args()

    target = Path(args.path)
    if not target.is_absolute():
        target = (CONTENT_DIR.parent / target).resolve()
    if not target.exists():
        print(f"Error: path not found: {target}", file=sys.stderr)
        return 1

    posts = collect_posts(target)
    if not posts:
        print("No posts found.")
        return 0

    total_issues = 0
    for post in posts:
        if "drafts" in post.parts and post != target:
            continue

        rel = post.relative_to(CONTENT_DIR.parent.resolve())
        issues = check_post(post)
        if args.drafts_only:
            text = post.read_text(encoding="utf-8")
            if 'draft: true' not in text:
                continue

        if issues:
            total_issues += len(issues)
            print(f"\n[{rel}]")
            for issue in issues:
                print(f"  - {issue}")

    if total_issues:
        print(f"\n{total_issues} issue(s) found.")
        return 1

    print("All checks passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
