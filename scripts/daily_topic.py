#!/usr/bin/env python3
"""Pick and manage daily blog topic recommendations."""

from __future__ import annotations

import argparse
import json
import sys
from datetime import date, datetime, timedelta
from pathlib import Path
from zoneinfo import ZoneInfo

from blog_config import CATEGORIES, ROOT

TOPICS_DIR = ROOT / "topics"
POOL_FILE = TOPICS_DIR / "pool.json"
STATE_FILE = TOPICS_DIR / "state.json"
DAILY_FILE = TOPICS_DIR / "daily.json"
KST = ZoneInfo("Asia/Seoul")


def load_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def save_json(path: Path, data: dict) -> None:
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def slugify_topic(topic: str) -> str:
    ascii_words = "".join(ch if ch.isascii() and (ch.isalnum() or ch.isspace()) else " " for ch in topic)
    slug = "-".join(ascii_words.lower().split())
    return slug or f"topic-{date.today().isoformat()}"


def recently_used_topics(state: dict, days: int = 21) -> set[str]:
    cutoff = datetime.now(KST).date() - timedelta(days=days)
    used: set[str] = set()
    for item in state.get("used", []):
        used_on = date.fromisoformat(item["date"])
        if used_on >= cutoff:
            used.add(item["topic"])
    return used


def pick_topic(target_day: date | None = None) -> dict:
    target_day = target_day or datetime.now(KST).date()
    pool = load_json(POOL_FILE)
    state = load_json(STATE_FILE)
    used_recent = recently_used_topics(state)

    category = CATEGORIES[target_day.toordinal() % len(CATEGORIES)]
    candidates = [topic for topic in pool[category] if topic not in used_recent]
    if not candidates:
        candidates = pool[category]

    topic = candidates[target_day.toordinal() % len(candidates)]
    slug = slugify_topic(topic)

    return {
        "date": target_day.isoformat(),
        "category": category,
        "topic": topic,
        "slug": slug,
        "command": (
            "python3 scripts/generate_article.py "
            f"--category {category} --topic \"{topic}\" --slug {slug} --scaffold"
        ),
        "generated_at": datetime.now(KST).isoformat(),
    }


def pick_week(start_day: date | None = None) -> list[dict]:
    start_day = start_day or datetime.now(KST).date()
    return [pick_topic(start_day + timedelta(days=i)) for i in range(7)]


def mark_used(topic: str, used_on: date | None = None) -> None:
    state = load_json(STATE_FILE)
    used_on = used_on or datetime.now(KST).date()
    state.setdefault("used", []).append({"topic": topic, "date": used_on.isoformat()})
    save_json(STATE_FILE, state)


def update_daily(target_day: date | None = None) -> dict:
    recommendation = pick_topic(target_day)
    save_json(DAILY_FILE, recommendation)
    return recommendation


def main() -> int:
    parser = argparse.ArgumentParser(description="Daily blog topic recommendation")
    sub = parser.add_subparsers(dest="command", required=True)

    sub.add_parser("today", help="Print today's topic")
    sub.add_parser("update", help="Write today's topic to topics/daily.json")
    sub.add_parser("week", help="Print 7-day topic plan")

    mark_cmd = sub.add_parser("mark-used", help="Mark a topic as used")
    mark_cmd.add_argument("topic", help="Topic text to mark as used")

    args = parser.parse_args()

    if args.command == "today":
        print(json.dumps(pick_topic(), ensure_ascii=False, indent=2))
        return 0

    if args.command == "update":
        recommendation = update_daily()
        print(f"Updated: {DAILY_FILE}")
        print(json.dumps(recommendation, ensure_ascii=False, indent=2))
        return 0

    if args.command == "week":
        print(json.dumps(pick_week(), ensure_ascii=False, indent=2))
        return 0

    if args.command == "mark-used":
        mark_used(args.topic)
        print(f"Marked as used: {args.topic}")
        return 0

    return 1


if __name__ == "__main__":
    raise SystemExit(main())
