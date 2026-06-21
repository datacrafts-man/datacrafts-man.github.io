---
title: "macOS 반복 작업 자동화: Python으로 스크립트 작성하기"
date: 2026-06-16T22:10:00+09:00
draft: true
tags: ["macOS", "automation", "python", "scripting"]
categories: ["automation"]
description: "macOS 환경에서 반복적인 파일 정리, 파일 실행, 다운로드 정리 등의 일상 작업을 파이썬 내장 os 및 subprocess 모듈을 활용해 완벽하게 자동화하는 실무 스크립트를 구현합니다."
ShowToc: true
TocOpen: false
---

매일 출근하자마자 하는 일이 무엇인가요? 다운로드 폴더에서 불필요한 스크린샷 파일을 지우고, 특정 폴더의 파일들을 백업용 외장 드라이브로 옮기며, 터미널을 열어 늘 쓰던 명령어 서너 개를 차례로 입력하진 않나요? 결론부터 말씀드리면, **파이썬의 표준 내장 라이브러리인 os와 subprocess 모듈을 조합해 단 몇십 줄의 스크립트만 작성해 두면, macOS 내에서 일어나는 파일 관리와 터미널 유틸리티 실행 작업을 클릭 한 번으로 자동화**할 수 있습니다.

과거의 저 역시 매번 바탕화면이 다운로드 파일과 캡처 이미지로 지저분해질 때마다 손으로 파일을 분류하여 폴더에 집어넣는 노가다를 반복하곤 했습니다. 어느 날 이 반복적인 귀찮음을 해소하고자 파이썬 파일 정리 스크립트를 짜서 macOS 스케줄러(launchd)에 올려두었고, 그 이후로는 파일 정리 스트레스에서 완전히 해방되었습니다. 이 글에서는 비전공자나 초보자도 바로 적용할 수 있도록 macOS의 파일 시스템을 다루는 `os` 활용법부터 다른 실행 프로그램들을 제어하는 `subprocess` 구현까지 실전 자동화 스크립트 튜토리얼을 상세히 전달합니다.

---

## 1. 파일 자동화의 핵심 도구 (os vs pathlib)

과거 파이썬 스크립트에서는 파일 경로와 시스템 폴더를 제어할 때 `os` 모듈을 주로 사용했습니다. 하지만 현대 파이썬(3.4+)에서는 객체 지향형 경로 처리가 가능한 `pathlib` 모듈이 함께 선호됩니다. 자동화 스크립트를 짜기 전, 두 라이브러리의 용도와 차이를 이해해야 합니다.

| 기능 비교 | 기존 os 모듈 | 현대적 pathlib 모듈 |
| :--- | :--- | :--- |
| **경로 표현** | 문자열 기반 (`"folder/file.txt"`) | Path 객체 기반 (`Path("folder") / "file.txt"`) |
| **경로 결합** | `os.path.join(path, filename)` | `path / filename` (슬래시 연산자 직관적 매핑) |
| **디렉토리 생성**| `os.makedirs(path, exist_ok=True)`| `Path.mkdir(parents=True, exist_ok=True)` |
| **파일 존재 확인**| `os.path.exists(path)` | `Path.exists()` |

*실무에서는 기본적인 시스템 환경 변수나 셸 실행 명령 환경 제어에는 `os`를 사용하고, 파일 경로 및 폴더 관리는 가독성이 좋은 `pathlib`을 함께 조화롭게 섞어 사용합니다.*

---

## 2. macOS 다운로드 폴더 자동 정리 스크립트 (단계별 실습)

다운로드 폴더에 쌓여 있는 파일들을 확장자별(이미지, 문서, 실행파일)로 자동 분류하여 각 하위 폴더로 이동시키는 스크립트를 구현합니다.

### 1단계: 대상 디렉토리 설정 및 폴더 생성
먼저 다운로드 폴더(`~/Downloads`) 경로를 획득하고, 분류용 타겟 폴더들을 동적으로 생성합니다.

```python
import os
from pathlib import Path

# 사용자의 홈 디렉토리를 찾아 다운로드 폴더 지정
DOWNLOADS_DIR = Path.home() / "Downloads"

# 확장자별 이동 대상 폴더 정의
DEST_FOLDERS = {
    ".png": DOWNLOADS_DIR / "Images",
    ".jpg": DOWNLOADS_DIR / "Images",
    ".jpeg": DOWNLOADS_DIR / "Images",
    ".pdf": DOWNLOADS_DIR / "Documents",
    ".xlsx": DOWNLOADS_DIR / "Documents",
    ".zip": DOWNLOADS_DIR / "Archives",
}

# 대상 폴더가 없으면 자동 생성
for folder in set(DEST_FOLDERS.values()):
    folder.mkdir(parents=True, exist_ok=True)
```

### 2단계: 파일 분류 및 안전한 이동 구현
이후 다운로드 폴더 내의 파일들을 순회하며 대상 폴더로 파일을 안전하게 이동시킵니다. 중복 파일이 있을 경우 덮어쓰지 않고 뒤에 숫자를 붙이는 안전장치를 더합니다.

```python
def move_file_safely(src_path: Path, dest_dir: Path):
    dest_path = dest_dir / src_path.name
    
    # 만약 대상 경로에 이미 같은 이름의 파일이 존재한다면 이름을 변경
    counter = 1
    while dest_path.exists():
        new_name = f"{src_path.stem}_{counter}{src_path.suffix}"
        dest_path = dest_dir / new_name
        counter += 1
        
    os.rename(src_path, dest_path)
    print(f"이동 완료: {src_path.name} -> {dest_path.name}")

# 다운로드 디렉토리 파일 순회하며 이동 실행
for file_path in DOWNLOADS_DIR.iterdir():
    # 폴더가 아닌 파일만 이동 처리
    if file_path.is_file() and file_path.suffix.lower() in DEST_FOLDERS:
        target_dir = DEST_FOLDERS[file_path.suffix.lower()]
        move_file_safely(file_path, target_dir)
```

---

## 3. Subprocess를 이용한 macOS 앱 및 셸 스크립트 실행 제어

자동화 중에 다른 macOS 앱을 실행하거나, 터미널 명령을 직접 파이썬에서 수행하고 그 결과를 가져오고 싶을 때 `subprocess` 모듈을 사용합니다.

### 터미널 명령 실행 및 결과 텍스트 획득
`subprocess.run` 함수를 사용하면 터미널 명령의 반환값과 표준 출력을 획득할 수 있습니다.

```python
import subprocess

# macOS의 현재 디스크 여유 공간(df -h)을 조회하는 터미널 명령 실행
try:
    result = subprocess.run(
        ["df", "-h", "/"],
        capture_output=True,
        text=True,
        check=True
    )
    # 터미널 명령어의 출력 내용을 파이썬 변수로 획득
    output = result.stdout
    print("디스크 사용량 조회 성공:")
    print(output)
except subprocess.CalledProcessError as e:
    print(f"터미널 명령 실패: {e}")
```

---

## 4. macOS 자동화 스크립트 작성 시 에러 예방 및 주의사항

*   **하드코딩된 경로 사용 지양**: 절대 경로(`"/Users/minsu_lee/Downloads"`)를 그대로 코드에 써 두면 사용자 계정명이 바뀌거나 다른 Mac으로 소스 코드를 옮겼을 때 에러가 납니다. 반드시 `Path.home()`이나 `os.path.expanduser("~")`를 사용해 동적으로 경로를 읽으세요.
*   **권한 설정(TCC) 이슈**: macOS는 보안 정책(TCC)이 매우 엄격합니다. 파이썬 스크립트가 데스크탑, 다운로드, 문서 등 시스템 기본 폴더의 파일에 접근하거나 파일을 제어하려 할 때 "Python이 파일에 접근하려고 합니다"라는 시스템 팝업 권한 동의를 거쳐야 정상 작동합니다. 터미널이나 에디터에 '전체 디스크 접근 권한'을 설정해 두면 수월합니다.
*   **셸 인젝션(Shell Injection) 방지**: `subprocess.run(..., shell=True)` 옵션을 사용해 사용자 입력을 그대로 실행하면 위험한 명령이 주입되어 시스템이 손상될 수 있습니다. 가급적 `shell=True` 옵션을 끄고 인자 리스트(`["df", "-h"]`) 전달 방식을 사용하세요.

---

## 5. 자주 묻는 질문 (FAQ)

### Q. 작성한 파이썬 스크립트를 매일 특정 시간에 자동으로 실행되게 만들 수 있나요?
네, macOS에는 리눅스의 cron`과 유사한 시스템 수준의 스케줄러인 `launchd`가 내장되어 있습니다. 실행 주기와 파일 위치를 설정한 `.plist` 파일을 `~/Library/LaunchAgents/` 폴더에 등록해 두면 시스템이 켜져 있는 동안 파이썬 스크립트를 매일 지정한 시간마다 백그라운드에서 실행시킬 수 있습니다.

### Q. 파이썬 스크립트를 다른 프로그램 설치 없이 바로 실행하는 앱(.app)으로 포장할 수 있나요?
`PyInstaller`나 `py2app` 같은 서드파티 라이브러리를 사용하면 작성한 `.py` 스크립트를 독립적으로 실행할 수 있는 macOS 실행 바이너리나 단독 어플리케이션 파일(`.app`) 형태로 패키징할 수 있습니다. 이렇게 하면 파이썬 개발 환경이 깔끔하게 없는 다른 사람에게도 자동화 앱을 배포하여 공유할 수 있습니다.

### Q. 파일 정리 중에 휴지통으로 버리지 않고 바로 영구 삭제되나요?
`os.remove()` 또는 `Path.unlink()` 함수는 휴지통을 거치지 않고 디스크에서 파일을 영구 삭제하므로 복구가 어렵습니다. 실무 개발 시 실수를 예방하기 위해 휴지통으로 이동시키는 기능이 안전한데, 이 경우 내장 라이브러리 대신 `send2trash`라는 오픈소스 파이썬 패키지를 설치해 사용하는 것을 권장합니다.

> 본 글은 macOS 환경에서의 파이썬 자동화 스크립트 구축에 관한 정보 제공용 가이드입니다. 파일 삭제 및 오버라이트 작업은 비가역적인 데이터 손실을 유발할 수 있으므로, 실제 다운로드 폴더나 중요 폴더에 스크립트를 적용하기 전에 반드시 백업 테스트 폴더를 생성하여 정상 작동 여부를 사전에 검증하십시오.
