#!/usr/bin/env python3
"""CLI tool for keyword research and automated blog draft preparation."""

from __future__ import annotations

import argparse
import csv
import json
import subprocess
import sys
import urllib.parse
import urllib.request
import webbrowser
from pathlib import Path

from blog_config import CATEGORIES, CATEGORY_LABELS, ROOT

CSV_PATH = ROOT / "keywords.csv"
HEADERS = {"User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36"}


def get_google_suggestions(query: str) -> list[str]:
    """Fetch autocomplete suggestions from Google."""
    url = f"http://suggestqueries.google.com/complete/search?output=chrome&hl=ko&q={urllib.parse.quote(query)}"
    try:
        req = urllib.request.Request(url, headers=HEADERS)
        with urllib.request.urlopen(req) as response:
            data = json.loads(response.read().decode("utf-8"))
            return data[1]
    except Exception as e:
        print(f"[경고] 구글 연관 검색어 조회 실패: {e}", file=sys.stderr)
        return []


def get_naver_suggestions(query: str) -> list[str]:
    """Fetch autocomplete suggestions from Naver."""
    url = (
        f"https://ac.search.naver.com/nx/ac?q={urllib.parse.quote(query)}"
        "&con=1&frm=nv&ans=2&r_format=json&r_enc=UTF-8&r_unicode=0&t_kcond=1&mode=2"
    )
    try:
        req = urllib.request.Request(url, headers=HEADERS)
        with urllib.request.urlopen(req) as response:
            data = json.loads(response.read().decode("utf-8"))
            items = data.get("items", [])
            if items:
                return [item[0] for item in items[0]]
            return []
    except Exception as e:
        print(f"[경고] 네이버 연관 검색어 조회 실패: {e}", file=sys.stderr)
        return []


def print_manual_guide(keyword: str) -> None:
    """Print step-by-step keyword research guide for the user."""
    encoded_kw = urllib.parse.quote(keyword)
    
    urls = {
        "키워드마스터 (웨어이즈포스트)": f"https://whereispost.com/keyword/?keyword={encoded_kw}",
        "블랙키위 (BlackKiwi)": f"https://blackkiwi.net/service/keyword-analysis?keyword={encoded_kw}",
        "구글 트렌드 (Google Trends)": f"https://trends.google.co.kr/trends/explore?q={encoded_kw}",
        "네이버 통합 검색": f"https://search.naver.com/search.naver?query={encoded_kw}",
        "네이버 광고 시스템 (직접 로그인 필요)": "https://searchad.naver.com/",
    }

    print("\n" + "=" * 60)
    print(f"  [키워드 분석 가이드] '{keyword}'")
    print("=" * 60)
    print("AI가 직접 조회할 수 없는 상세 수치는 아래 무료 도구들을 통해 확인해 주세요.\n")
    
    for idx, (name, url) in enumerate(urls.items(), 1):
        print(f"  {idx}. {name}")
        print(f"     링크: {url}")
    
    print("\n--- 분석 시 체크리스트 ---")
    print("1. 검색량 확인: 월간 PC/모바일 검색량이 충분한가 (글을 쓸 가치가 있는가)?")
    print("2. 포화도/경쟁도 확인: 검색량 대비 블로그 문서 수가 적어 상위 노출이 쉬운가?")
    print("3. 검색 의도 분석: 네이버/구글 검색 시 상위 글들이 개인 블로그나 정보글인가?")
    print("   * 주의: 키워드플래너의 '경쟁' 지수는 광고 경쟁도이므로, 반드시 실제 검색결과 1페이지를 확인하세요!")
    print("=" * 60)

    if sys.stdin.isatty():
        choice = input("\n위 무료 도구 링크들을 브라우저에서 모두 여시겠습니까? (y/N): ").strip().lower()
        if choice == "y":
            print("브라우저에서 링크를 여는 중...")
            for name, url in urls.items():
                webbrowser.open(url)


def print_llm_prompt() -> None:
    """Print LLM prompt for generating new long-tail keywords."""
    categories_str = ", ".join(CATEGORIES)
    print("\n" + "=" * 60)
    print("  [LLM 프롬프트 복사용 텍스트]")
    print("=" * 60)
    print("아래 텍스트를 복사하여 Claude나 ChatGPT 등의 AI에게 전달하면")
    print("블로그 카테고리에 맞는 고단가 저경쟁 롱테일 키워드를 발굴할 수 있습니다.\n")
    
    prompt = f"""너는 한국의 IT/기술/커리어 블로그 'datacrafts-man'의 전문 SEO 담당자다.
아래 씨앗 카테고리 각각에 대해, 한국의 검색 사용자들이 구글이나 네이버 검색창에 실제로 입력할 법한 '롱테일 키워드(롱테일 키워드)' 후보군을 발굴해 다오.

씨앗 카테고리: {categories_str}

[조건]
- 각 씨앗 카테고리당 6~8개의 구체적인 롱테일 키워드를 추출할 것.
- 단어 한 개짜리 머리(Head) 키워드는 금지하며, 반드시 두 단어 이상의 구체적 질문형, 비교형, 실행형 키워드로 구성할 것.
- '추천', '계산', '방법', '설정', '비교', '한도', '초보', '에러'와 같은 수식어 및 사용자의 구체적 목적을 적극 결합할 것.
- 각 키워드에 대해 다음 항목을 추정해라:
  1. 검색 의도 (정보형 / 비교형 / 실행형 중 하나)
  2. 왜 신생 블로그가 노려볼 만한지 (검색 엔진 1페이지에 대형 매체 대신 개인 블로그가 비집고 들어갈 틈이 있는 이유)
- 결과는 아래 마크다운 표 형식으로 한 번에 출력할 것.

[출력 형식 (마크다운 표)]
| 키워드 | 씨앗 | 검색의도 | suggested_title (클릭 유도형 제목) | notes (본문에서 다뤄야 할 핵심 사항) | 노려볼 근거 |
"""
    print(prompt.strip())
    print("=" * 60 + "\n")


def list_keywords() -> None:
    """List all keywords from keywords.csv."""
    if not CSV_PATH.exists():
        print(f"오류: '{CSV_PATH}' 파일이 존재하지 않습니다.", file=sys.stderr)
        return

    print("\n" + "=" * 60)
    print(f"  [키워드 데이터베이스 목록] ({CSV_PATH.name})")
    print("=" * 60)
    
    try:
        with open(CSV_PATH, mode="r", encoding="utf-8-sig") as f:
            reader = csv.DictReader(f)
            rows = sorted(reader, key=lambda x: int(x.get("priority", 999)))
            for row in rows:
                prio = row.get("priority", "-")
                kw = row.get("keyword", "-")
                seed = row.get("seed", "-")
                intent = row.get("intent", "-")
                title = row.get("suggested_title", "-")
                print(f"[{prio}] [{seed}] {kw} ({intent})")
                print(f"   └ 제목: {title}")
    except Exception as e:
        print(f"오류 발생: {e}", file=sys.stderr)
    print("=" * 60 + "\n")


def save_keyword_to_csv(keyword: str) -> None:
    """Save a new keyword to keywords.csv."""
    print("\n" + "=" * 60)
    print("  [키워드 데이터베이스 추가]")
    print("=" * 60)
    
    # 1. Seed
    print("* 카테고리(Seed) 목록:")
    for idx, cat in enumerate(CATEGORIES, 1):
        print(f"  {idx}. {cat} ({CATEGORY_LABELS.get(cat, cat)})")
    
    cat_idx = 1
    while True:
        try:
            val = input(f"카테고리 번호 선택 (1~{len(CATEGORIES)}, 기본값: 1): ").strip()
            if not val:
                break
            idx = int(val)
            if 1 <= idx <= len(CATEGORIES):
                cat_idx = idx
                break
            print("유효한 번호를 입력하세요.")
        except ValueError:
            print("숫자를 입력하세요.")
    seed = CATEGORIES[cat_idx - 1]

    # 2. Intent
    intent = "정보형"
    print("\n* 검색 의도 선택:")
    print("  1. 정보형 (개념 설명, 원리 소개 등)")
    print("  2. 비교형 (대안 비교, 장단점 분석 등)")
    print("  3. 실행형 (실제 실습, 설정 가이드 등)")
    while True:
        val = input("의도 번호 선택 (1~3, 기본값: 1): ").strip()
        if not val or val == "1":
            intent = "정보형"
            break
        elif val == "2":
            intent = "비교형"
            break
        elif val == "3":
            intent = "실행형"
            break
        print("유효한 번호를 입력하세요.")

    # 3. Suggested Title
    suggested_title = input(f"\n클릭 유도형 제목 (기본값: '{keyword}'): ").strip() or keyword

    # 4. Notes
    notes = input("\n본문에서 반드시 다뤄야 할 핵심 한두 가지 (참고사항): ").strip()
    if not notes:
        notes = "블로그 운영자가 직접 경험한 사례나 일화 형태의 서술"

    # 5. Priority
    priority = "30"
    while True:
        val = input("\n우선순위 지정 (1~30, 기본값: 30): ").strip()
        if not val:
            break
        try:
            p = int(val)
            if 1 <= p <= 100:
                priority = str(p)
                break
            print("1~100 사이의 숫자를 입력하세요.")
        except ValueError:
            print("숫자를 입력하세요.")

    # Write to CSV
    file_exists = CSV_PATH.exists()
    try:
        with open(CSV_PATH, mode="a", encoding="utf-8", newline="") as f:
            writer = csv.writer(f)
            if not file_exists:
                writer.writerow(["keyword", "seed", "intent", "suggested_title", "notes", "priority"])
            writer.writerow([keyword, seed, intent, suggested_title, notes, priority])
        print(f"\n[성공] '{keyword}' 키워드가 {CSV_PATH.name}에 추가되었습니다!")
    except Exception as e:
        print(f"\n[오류] CSV 추가 중 에러 발생: {e}", file=sys.stderr)


def run_article_generator_for_keyword(keyword: str) -> None:
    """Run generate_article using CSV database or interactive prompt."""
    cmd = ["python3", "scripts/generate_article.py", "--scaffold"]
    
    # Check if keyword exists in CSV
    in_csv = False
    if CSV_PATH.exists():
        with open(CSV_PATH, mode="r", encoding="utf-8-sig") as f:
            reader = csv.DictReader(f)
            for row in reader:
                if row.get("keyword") == keyword:
                    in_csv = True
                    break

    if in_csv:
        cmd += ["--csv", str(CSV_PATH), "--keyword", keyword]
        print(f"\nCSV 데이터베이스에서 '{keyword}' 정보를 로드하여 실행합니다.")
    else:
        # Prompt user to select category to bridge manually
        print("\n* 카테고리 선택:")
        for idx, cat in enumerate(CATEGORIES, 1):
            print(f"  {idx}. {cat} ({CATEGORY_LABELS.get(cat, cat)})")
        cat_idx = 1
        while True:
            try:
                val = input(f"카테고리 번호 선택 (1~{len(CATEGORIES)}, 기본값: 1): ").strip()
                if not val:
                    break
                idx = int(val)
                if 1 <= idx <= len(CATEGORIES):
                    cat_idx = idx
                    break
                print("유효한 번호를 입력하세요.")
            except ValueError:
                print("숫자를 입력하세요.")
        cmd += ["--category", CATEGORIES[cat_idx - 1], "--topic", keyword]
        
    print("실행할 명령어:", " ".join(cmd))
    try:
        subprocess.run(cmd, check=True)
        print("\n[성공] AI 글 생성 프롬프트와 초안 파일이 작성되었습니다!")
    except subprocess.CalledProcessError as e:
        print(f"\n[오류] 글 생성 스크립트 실행 중 에러가 발생했습니다: {e}", file=sys.stderr)


def main() -> int:
    parser = argparse.ArgumentParser(description="Keyword research helper with free tools guide.")
    parser.add_argument("keyword", nargs="?", help="Keyword to search")
    parser.add_argument("--list", "-l", action="store_true", help="List all keywords in keywords.csv")
    parser.add_argument("--prompt", "-p", action="store_true", help="Print LLM prompt for generating new long-tail keywords")
    args = parser.parse_args()

    if args.list:
        list_keywords()
        return 0

    if args.prompt:
        print_llm_prompt()
        return 0

    keyword = args.keyword
    if not keyword and sys.stdin.isatty():
        keyword = input("분석할 키워드를 입력하세요: ").strip()

    if not keyword:
        print("에러: 분석할 키워드를 입력하거나 옵션을 지정해 주세요.", file=sys.stderr)
        parser.print_help()
        return 1

    print(f"'{keyword}' 키워드를 분석 중입니다...\n")

    # 1. Fetch autocompletes
    print("[1] 구글 연관 검색어 (Google Autocomplete Suggestions):")
    g_sug = get_google_suggestions(keyword)
    if g_sug:
        for idx, sug in enumerate(g_sug[:10], 1):
            print(f"  - {sug}")
    else:
        print("  (결과 없음)")

    print("\n[2] 네이버 연관 검색어 (Naver Autocomplete Suggestions):")
    n_sug = get_naver_suggestions(keyword)
    if n_sug:
        for idx, sug in enumerate(n_sug[:10], 1):
            print(f"  - {sug}")
    else:
        print("  (결과 없음)")

    # 2. Print manual guides and tool URLs
    print_manual_guide(keyword)

    # 3. Add to CSV or generate article
    if sys.stdin.isatty():
        # Check if already in CSV
        in_csv = False
        if CSV_PATH.exists():
            with open(CSV_PATH, mode="r", encoding="utf-8-sig") as f:
                reader = csv.DictReader(f)
                for row in reader:
                    if row.get("keyword") == keyword:
                        in_csv = True
                        break
        
        if not in_csv:
            save_choice = input(f"\n이 키워드('{keyword}')를 keywords.csv 데이터베이스에 추가하시겠습니까? (y/N): ").strip().lower()
            if save_choice == "y":
                save_keyword_to_csv(keyword)

        gen_choice = input("\n이 키워드로 블로그 글 생성 프롬프트를 작성하시겠습니까? (Y/n): ").strip().lower()
        if gen_choice != "n":
            run_article_generator_for_keyword(keyword)

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
