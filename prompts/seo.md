# SEO Guidelines

## Title

- 길이: 20~40자 권장 (한국어 기준)
- 핵심 키워드를 앞쪽에 배치
- 클릭베이트 금지, 검색 의도와 일치해야 함

## Description

- 길이: 120~160자
- 글의 핵심 가치 + 대상 독자를 한 문장으로 요약
- 제목과 동일 문장 반복 금지

## Tags & Categories

- `categories`: Hugo 섹션 1개 (python, automation, ai, data-analysis, quant, projects, career)
- `tags`: 2~5개, 구체적 키워드 (예: `pandas`, `backtest`)

## 본문

- H1은 front matter `title`만 사용 (본문에 H1 금지)
- H2부터 시작
- 첫 100자 안에 주제 키워드 포함
- 내부 링크 1개 이상 권장

## URL (slug)

- 영문 소문자 + 하이픈 (예: `asyncio-basics`)
- 날짜 기반 slug는 시리즈 글에만 사용

## Open Graph (자동)

PaperMod가 `title`, `description`, `date`를 기반으로 OG 태그를 생성합니다.
front matter를 정확히 채우는 것이 가장 중요합니다.
