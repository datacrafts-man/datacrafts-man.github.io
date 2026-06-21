#!/usr/bin/env python3
"""Batch agent-prompt generator from keywords.csv.

Pipeline:
  keywords.csv → priority 순 정렬 → 상위 N개 → agent-prompt.md 생성
  → 슬러그 중복 건너뜀 → 결과 리포트

Usage:
  python3 scripts/generate_batch.py             # 상위 3개 생성 (기본값)
  python3 scripts/generate_batch.py --count 5   # 상위 5개 생성
  python3 scripts/generate_batch.py --all       # 전체 키워드 처리
  python3 scripts/generate_batch.py --dry-run   # 실행 없이 처리 대상만 출력
"""

from __future__ import annotations

import argparse
import csv
import subprocess
import sys
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

from blog_config import CATEGORIES, CONTENT_DIR, DRAFTS_DIR, ROOT
from create_post import slugify

CSV_PATH = ROOT / "keywords.csv"
KST = ZoneInfo("Asia/Seoul")

INTENT_CHOICES = {"정보형", "비교형", "실행형", "이동형"}


def load_keywords(csv_path: Path) -> list[dict]:
    """Load and sort keywords by priority (ascending)."""
    if not csv_path.exists():
        print(f"오류: '{csv_path}' 파일이 존재하지 않습니다.", file=sys.stderr)
        sys.exit(1)

    rows = []
    with open(csv_path, encoding="utf-8-sig") as f:
        for row in csv.DictReader(f):
            try:
                row["_priority"] = int(row.get("priority", 99))
            except ValueError:
                row["_priority"] = 99
            rows.append(row)

    return sorted(rows, key=lambda r: r["_priority"])


def draft_exists(slug: str) -> bool:
    """Return True if a draft folder with index.md already exists."""
    return (DRAFTS_DIR / slug / "index.md").exists()


def generate_prompt(row: dict, dry_run: bool = False) -> tuple[str, bool]:
    """Generate agent-prompt.md for one keyword row. Returns (slug, skipped)."""
    keyword = row.get("keyword", "").strip()
    seed = row.get("seed", "python").strip()
    suggested_title = row.get("suggested_title", keyword).strip()
    notes = row.get("notes", "").strip()
    intent = row.get("intent", "정보형").strip()

    if seed not in CATEGORIES:
        seed = "python"
    if intent not in INTENT_CHOICES:
        intent = "정보형"

    slug = slugify(suggested_title or keyword)

    if draft_exists(slug):
        return slug, True  # skipped

    if dry_run:
        print(f"  [dry-run] 생성 예정: {slug} ({intent}) — {suggested_title}")
        return slug, False

    cmd = [
        "python3", "scripts/generate_article.py",
        "--category", seed,
        "--topic", suggested_title,
        "--references", notes or "블로그 운영자가 직접 고민하고 해결한 일화나 실제 경험담 형태로 서술",
        "--intent", intent,
        "--non-interactive",
        "--scaffold",
    ]

    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        print(f"  [오류] {keyword}: {result.stderr.strip()}", file=sys.stderr)
        return slug, False

    return slug, False


def report(generated: list[dict], skipped: list[str]) -> None:
    """Print a summary table of generated files."""
    print("\n" + "=" * 70)
    print("  [배치 생성 결과 리포트]")
    print("=" * 70)

    if not generated and not skipped:
        print("  처리된 항목이 없습니다.")
        print("=" * 70)
        return

    if generated:
        print(f"\n  ✅ 생성 완료 ({len(generated)}편)\n")
        print(f"  {'우선순위':<6} {'슬러그':<35} {'의도':<8} 제목")
        print("  " + "-" * 66)
        for item in generated:
            title_short = item["title"][:30] + "…" if len(item["title"]) > 30 else item["title"]
            print(f"  [{item['priority']:<4}] {item['slug']:<35} {item['intent']:<8} {title_short}")

    if skipped:
        print(f"\n  ⏭️  건너뜀 (이미 존재하는 슬러그, {len(skipped)}개)\n")
        for s in skipped:
            print(f"  - {s}")

    print("\n  ─── 검수 게이트 체크리스트 (각 초안에 대해 수행) ───")
    print("  □ 1. 사실 확인: 수치·날짜·API명이 정확한가?")
    print("  □ 2. 두괄식 확인: 첫 문단만 읽고 독자의 질문에 답이 됐는가?")
    print("  □ 3. 중복 확인: 다른 글과 통째로 겹치는 단락은 없는가?")
    print("  □ 4. 정직성 확인: 투자 권유 표현 또는 무책임한 단정은 없는가?")
    print("  □ 5. 사람 손길: AI 상투구를 다듬고 내 경험 한두 문장을 보탰는가?")
    print("\n  → 5가지 모두 통과 시 front matter의 draft: true → false 로 변경 후 발행")
    print("  → SEO 최종 검증: python3 scripts/seo_check.py content/drafts/<slug>")
    print("=" * 70 + "\n")


def main() -> int:
    parser = argparse.ArgumentParser(description="Batch generate agent-prompts from keywords.csv")
    parser.add_argument("--count", "-c", type=int, default=3, help="생성할 초안 수 (기본값: 3)")
    parser.add_argument("--all", "-a", action="store_true", help="전체 키워드 처리")
    parser.add_argument("--dry-run", action="store_true", help="실제 생성 없이 처리 대상만 출력")
    parser.add_argument("--csv", type=Path, default=CSV_PATH, help="키워드 CSV 파일 경로")
    args = parser.parse_args()

    rows = load_keywords(args.csv)
    limit = len(rows) if args.all else args.count

    print(f"\n{'[DRY-RUN] ' if args.dry_run else ''}배치 생성 시작: 우선순위 상위 {limit}개 처리")
    print(f"  소스: {args.csv}")
    print(f"  대상 디렉토리: {DRAFTS_DIR}\n")

    generated = []
    skipped_slugs = []
    processed = 0

    for row in rows:
        if processed >= limit:
            break

        keyword = row.get("keyword", "").strip()
        suggested_title = row.get("suggested_title", keyword).strip()
        intent = row.get("intent", "정보형").strip()
        priority = row.get("priority", "-")
        slug = slugify(suggested_title or keyword)

        print(f"[{priority}] '{keyword}' 처리 중...")

        slug_out, skipped = generate_prompt(row, dry_run=args.dry_run)

        if skipped:
            print(f"  → 건너뜀: '{slug_out}' 슬러그가 이미 존재합니다.")
            skipped_slugs.append(slug_out)
        elif not args.dry_run:
            # Count approximate characters in index.md if scaffold was created
            index_path = DRAFTS_DIR / slug_out / "index.md"
            char_count = len(index_path.read_text(encoding="utf-8")) if index_path.exists() else 0
            generated.append({
                "priority": priority,
                "slug": slug_out,
                "title": suggested_title,
                "intent": intent,
                "chars": char_count,
            })
            print(f"  → 완료: content/drafts/{slug_out}/")

        processed += 1

    report(generated, skipped_slugs)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
