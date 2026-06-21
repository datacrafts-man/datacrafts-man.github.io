#!/usr/bin/env python3
"""Prepare an agent prompt and draft scaffold for AI article generation."""

from __future__ import annotations

import argparse
import sys
from datetime import datetime
from pathlib import Path

from blog_config import CATEGORIES, DRAFTS_DIR, PROMPTS_DIR
from create_post import build_front_matter, slugify


DEFAULT_READER = "과거의 나와 비슷한 사람 (이 주제를 처음 배우며 실무 적용을 고민하는 학습자)"
DEFAULT_REFERENCES = "블로그 운영자가 직접 고민하고 해결한 일화나 실제 경험담처럼 느껴지는 친근하고 진정성 있는 서술 방식 채택"
DEFAULT_INTENT = "정보형"


def render_prompt(
    template: str,
    category: str,
    topic: str,
    slug: str,
    reader: str | None = None,
    references: str | None = None,
    intent: str | None = None,
) -> str:
    today = datetime.now().strftime("%Y-%m-%dT%H:%M:%S+09:00")
    r_val = reader or DEFAULT_READER
    ref_val = references or DEFAULT_REFERENCES
    intent_val = intent or DEFAULT_INTENT
    return (
        template.replace("{{CATEGORY}}", category)
        .replace("{{TOPIC}}", topic)
        .replace("{{SLUG}}", slug)
        .replace("{{DATE}}", today)
        .replace("{{READER}}", r_val)
        .replace("{{REFERENCES}}", ref_val)
        .replace("{{INTENT}}", intent_val)
    )


def main() -> int:
    parser = argparse.ArgumentParser(description="Generate agent prompt for a blog article.")
    parser.add_argument("--category", "-c", choices=CATEGORIES, help="Article category")
    parser.add_argument("--topic", "-t", help="Article topic")
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
    parser.add_argument("--reader", "-r", help="Description of the target/expected reader")
    parser.add_argument("--references", "-ref", help="Reference notes or guidelines for the post")
    parser.add_argument("--intent", "-i", choices=["정보형", "비교형", "실행형", "이동형"], help="Search intent of the keyword")
    parser.add_argument("--csv", type=Path, help="Path to keywords.csv database")
    parser.add_argument("--keyword", help="Keyword to look up in the CSV database")
    parser.add_argument(
        "--non-interactive",
        "-n",
        action="store_true",
        help="Disable interactive prompt for reader/references if not provided",
    )
    args = parser.parse_args()

    category = args.category
    topic = args.topic
    reader = args.reader
    references = args.references
    intent = args.intent

    if args.csv and args.keyword:
        if not args.csv.exists():
            print(f"Error: CSV file not found: {args.csv}", file=sys.stderr)
            return 1
        
        import csv
        found = False
        with open(args.csv, mode="r", encoding="utf-8-sig") as f:
            reader_csv = csv.DictReader(f)
            for row in reader_csv:
                if row.get("keyword") == args.keyword:
                    found = True
                    category = category or row.get("seed")
                    if category not in CATEGORIES:
                        print(f"Warning: Category '{category}' from CSV seed is not in valid categories {CATEGORIES}. Defaulting to 'python'.", file=sys.stderr)
                        category = "python"
                    topic = topic or row.get("suggested_title") or row.get("keyword")
                    intent = intent or row.get("intent")
                    references = references or row.get("notes")
                    break
        if not found:
            print(f"Error: Keyword '{args.keyword}' not found in CSV.", file=sys.stderr)
            return 1

    if not category:
        print("Error: --category (or seed from CSV) is required.", file=sys.stderr)
        return 1
    if not topic:
        print("Error: --topic (or suggested_title from CSV) is required.", file=sys.stderr)
        return 1

    slug = args.slug or slugify(topic)

    if sys.stdin.isatty() and not args.non_interactive:
        if reader is None:
            print("\n=== 예상 독자 (Target Reader) 입력 ===")
            print("과거의 나와 비슷한 사람 중 누구를 타게팅하고 싶으신가요?")
            print("(입력을 마친 후 빈 줄에서 Enter를 누르시면 기본값으로 설정됩니다.)")
            reader_lines = []
            while True:
                try:
                    line = input("> ")
                    if not line:
                        break
                    reader_lines.append(line)
                except (EOFError, KeyboardInterrupt):
                    break
            reader = "\n".join(reader_lines).strip()
            if not reader:
                reader = DEFAULT_READER
                print(f"기본값 사용: {reader}")

        if references is None:
            print("\n=== 참고 및 반영 사항 (References) 입력 ===")
            print("글 작성 시 참고할 경험이나 주의할 내용을 입력해주세요.")
            print("(입력을 마친 후 빈 줄에서 Enter를 누르시면 기본값으로 설정됩니다.)")
            ref_lines = []
            while True:
                try:
                    line = input("> ")
                    if not line:
                        break
                    ref_lines.append(line)
                except (EOFError, KeyboardInterrupt):
                    break
            references = "\n".join(ref_lines).strip()
            if not references:
                references = DEFAULT_REFERENCES
                print(f"기본값 사용: {references}")

        if intent is None:
            print("\n=== 검색 의도 (Search Intent) 선택 ===")
            print("1. 정보형 (개념 설명, 원리 소개 등)")
            print("2. 비교형 (대안 비교, 장단점 분석 등)")
            print("3. 실행형 (실제 실습, 설정 가이드 등)")
            while True:
                val = input("검색 의도 선택 (1~3, 기본값: 1): ").strip()
                if not val or val == "1":
                    intent = "정보형"
                    break
                elif val == "2":
                    intent = "비교형"
                    break
                elif val == "3":
                    intent = "실행형"
                    break
                else:
                    print("유효한 번호를 입력하세요.")
    else:
        if reader is None:
            reader = DEFAULT_READER
        if references is None:
            references = DEFAULT_REFERENCES
        if intent is None:
            intent = DEFAULT_INTENT

    prompt_template = (PROMPTS_DIR / "article.md").read_text(encoding="utf-8")
    prompt = render_prompt(
        prompt_template,
        category,
        topic,
        slug,
        reader=reader,
        references=references,
        intent=intent,
    )

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
