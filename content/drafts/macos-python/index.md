---
title: "macOS 파이썬 개발환경 구성 가이드: pyenv와 venv로 깔끔하게 시작하기"
date: 2026-06-21T19:45:00+09:00
draft: true
tags: ["macOS", "python", "pyenv", "venv"]
categories: ["python"]
description: "macOS 환경에서 시스템 파이썬을 오염시키지 않고, pyenv와 venv를 활용해 깔끔하고 독립적인 파이썬 개발 환경을 구축하는 방법을 단계별로 알기 쉽게 정리합니다."
ShowToc: true
TocOpen: false
---

새로운 Mac을 받거나 포맷한 뒤 개발 환경을 세팅할 때, 가장 먼저 설치하게 되는 도구 중 하나가 바로 **파이썬(Python)**입니다. 결론부터 말씀드리면, **macOS에 기본적으로 설치되어 있는 시스템 파이썬은 절대 그대로 사용하면 안 되며, pyenv와 venv를 조합하여 버전과 프로젝트 환경을 철저히 격리해 사용**해야 합니다.

과거의 저는 이러한 격리의 중요성을 잘 알지 못한 채, 터미널에 `pip install`을 남발하며 전역(Global) 공간에 온갖 패키지들을 설치하곤 했습니다. 그러다 특정 라이브러리의 버전 충돌로 인해 macOS 시스템 도구가 오동작하거나, 이전에 잘 돌아가던 다른 프로젝트의 코드가 먹통이 되어 꼬여버린 환경을 복구하느라 밤을 새운 쓰라린 기억이 있습니다. 

이 글에서는 저와 같은 실수를 반복하지 않도록, macOS 환경에서 가장 깔끔하고 정석적인 파이썬 개발 환경을 구축하는 방법을 아주 기초적인 단계부터 핵심적인 설정까지 상세히 공유합니다.

---

## 1. 왜 파이썬 환경 격리가 필수적일까요?

macOS에는 운영체제 자체나 Xcode 개발 도구 등이 내부적으로 사용하는 시스템 파이썬이 이미 내장되어 있습니다. 이를 그대로 사용해 패키지를 설치하거나 수정을 가하게 되면 다음과 같은 치명적인 문제가 발생합니다.

1. **시스템 안정성 저하**: macOS 내부 시스템 스크립트가 의존하는 파이썬 패키지 버전을 변경해 버리면 OS 기능 자체가 오작동할 수 있습니다.
2. **권한 오류**: 시스템 영역에 설치를 시도하다 보니 상시 `sudo` 권한을 요구하게 되고, 이는 보안상 매우 취약한 환경을 만듭니다.
3. **프로젝트 간 버전 충돌**: 프로젝트 A는 Pandas 1.x 버전을 쓰고 프로젝트 B는 Pandas 2.x 버전을 써야 할 때, 글로벌 환경 하나만 사용하면 한쪽 프로젝트는 무조건 실행에 실패하게 됩니다.

따라서 우리는 **Homebrew**로 패키지 매니저를 설치한 뒤, **pyenv**로 독립적인 파이썬 버전을 내려받고, **venv**를 이용해 프로젝트마다 고유한 가상환경을 만들어 사용할 것입니다.

---

## 2. 1단계: 패키지 매니저 Homebrew 설치

Mac 개발자들에게 절대 빠질 수 없는 도구가 바로 패키지 매니저인 **Homebrew**입니다. pyenv를 컴파일하고 설치하는 데 필요한 다양한 라이브러리를 터미널 명령어 하나로 손쉽게 관리할 수 있게 해줍니다.

터미널을 열고 아래 명령어를 입력하여 Homebrew를 설치합니다.

```bash
/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
```

설치가 완료되면 화면의 안내 메시지(Next steps)를 따라 아래와 같이 셸 환경 변수에 Homebrew 경로를 추가해 줍니다. (M1/M2/M3 Apple Silicon Mac 기준)

```bash
echo 'eval "$(/opt/homebrew/bin/brew shellenv)"' >> ~/.zprofile
eval "$(/opt/homebrew/bin/brew shellenv)"
```

---

## 3. 2단계: pyenv로 파이썬 버전 자유롭게 변경하기

**pyenv**는 Mac 시스템에 여러 버전의 파이썬을 설치하고, 프로젝트별로 원하는 버전을 자유롭게 스위칭할 수 있도록 돕는 버전 관리 도구입니다.

### 1) pyenv 설치 및 의존성 라이브러리 설치
파이썬을 소스 코드로부터 올바르게 빌드하기 위해, 먼저 빌드 의존 도구들을 설치한 후 pyenv를 설치합니다.

```bash
# 파이썬 컴파일에 필요한 의존성 도구 설치
brew install openssl readline sqlite3 xz zlib tcl-tk

# pyenv 설치
brew install pyenv
```

### 2) 셸 환경 설정 (.zshrc 파일 수정)
macOS의 기본 셸인 zsh에서 pyenv 명령어가 항상 우선적으로 호출되도록 환경 변수 경로 설정을 추가해야 합니다. 

```bash
echo 'export PYENV_ROOT="$HOME/.pyenv"' >> ~/.zshrc
echo '[[ -d $PYENV_ROOT/bin ]] && export PATH="$PYENV_ROOT/bin:$PATH"' >> ~/.zshrc
echo 'eval "$(pyenv init -)"' >> ~/.zshrc
```

설정을 마친 후, 현재 열려 있는 터미널 창에 변경 사항을 적용합니다.

```bash
source ~/.zshrc
```

### 3) 원하는 파이썬 버전 설치 및 적용
이제 준비가 되었습니다. 원하는 버전을 조회하고 설치해 봅시다.

```bash
# 설치 가능한 파이썬 최신 버전 목록 조회
pyenv install --list | grep -E '^  3\.[0-9]+'

# 특정 파이썬 버전 설치 (예: 3.12.0)
pyenv install 3.12.0

# Mac 시스템 전체에서 기본적으로 사용할 글로벌 파이썬 버전을 지정
pyenv global 3.12.0
```

적용이 완료되었는지 확인하려면 다음 명령어를 실행합니다. 경로가 `/Users/계정명/.pyenv/shims/python`으로 잡혀 있다면 성공적으로 세팅된 것입니다.

```bash
which python
# 출력 예시: /Users/username/.pyenv/shims/python

python --version
# 출력 예시: Python 3.12.0
```

---

## 4. 3단계: venv로 프로젝트별 가상환경 구성하기

버전을 통일했더라도 프로젝트마다 설치할 패키지(예: Django, FastAPI, PyTorch 등)들을 격리해야 합니다. 파이썬에 내장된 **venv** 모듈을 사용해 가상환경을 구성해 보겠습니다.

### 1) 프로젝트 디렉토리 생성 및 이동
```bash
mkdir -p ~/projects/my-first-app
cd ~/projects/my-first-app
```

### 2) 가상환경 생성
디렉토리 내부에 `.venv`라는 이름의 독립된 가상환경 폴더를 만듭니다.

```bash
python -m venv .venv
```

### 3) 가상환경 활성화 (Activate)
생성된 가상환경을 활성화하면, 이후 설치하는 모든 라이브러리는 전역 공간이 아닌 이 프로젝트 폴더 내부(`.venv`)에만 설치됩니다.

```bash
source .venv/bin/activate
```
활성화가 완료되면 터미널 프롬프트 앞에 `(.venv)`라는 표시가 나타납니다.

```bash
# 가상환경 내 패키지 설치 예시
pip install --upgrade pip
pip install requests
```

### 4) 가상환경 비활성화 (Deactivate)
작업을 마친 후 가상환경에서 빠져나오려면 단지 다음 명령어를 수행하면 됩니다.

```bash
deactivate
```

---

## 5. 4단계: VS Code 에디터 연동 설정

코드를 작성할 때 린터(Linter) 오류가 나지 않고 자동 완성이 제대로 작동하려면, 사용하는 에디터(VS Code)가 우리가 방금 만든 가상환경의 파이썬 인터프리터를 인식하도록 설정해야 합니다.

1. VS Code로 프로젝트 폴더(`my-first-app`)를 엽니다.
2. 단축키 `Cmd + Shift + P`를 눌러 명령 팔레트를 엽니다.
3. **`Python: Select Interpreter`**를 입력하고 선택합니다.
4. 목록에서 **`Use VS Code's recommended interpreter`** 또는 우리가 생성한 `(.venv) ./venv/bin/python` 경로의 인터프리터를 선택합니다.

이렇게 설정하면 코드를 작성할 때 외부 라이브러리 참조 경로가 제대로 잡혀 붉은 밑줄 에러 표시 없이 쾌적한 개발이 가능해집니다.

---

## 6. 자주 발생하는 에러와 문제 해결 (FAQ)

### Q. pyenv install 실행 시 빌드 에러가 납니다.
M 시리즈 Mac의 경우 빌드 환경 경로가 제대로 잡히지 않아 실패할 수 있습니다. 터미널에 아래 명령어를 실행하여 Xcode 개발자 도구를 재설치/업데이트한 후 다시 시도해 보세요.
```bash
xcode-select --install
```

### Q. pyenv 버전을 global로 설정했는데도 계속 시스템 파이썬 버전이 출력됩니다.
경로가 꼬인 경우로, 높은 확률로 `.zshrc` 파일에 추가한 `eval "$(pyenv init -)"` 코드가 적용되지 않았거나 파일 하단에 다른 환경 변수 설정으로 덮어써졌을 가능성이 높습니다. `.zshrc` 파일을 열어 해당 라인이 맨 마지막 부분에 잘 배치되어 있는지 점검하고 `source ~/.zshrc`를 다시 한 번 입력해 주세요.

### Q. 가상환경 폴더 `.venv`도 Git에 커밋해야 하나요?
**절대 안 됩니다.** 가상환경 폴더 내부에는 수백 메가바이트에 달하는 패키지 바이너리 파일들이 포함되어 있으므로 깃허브에 올릴 필요가 없습니다. 프로젝트 루트에 `.gitignore` 파일을 만들고 아래 코드를 한 줄 추가해 줍니다.
```text
.venv/
```
대신 설치한 라이브러리 목록을 `pip freeze > requirements.txt`로 내보내어, 이 텍스트 파일만 Git에 커밋해 동료들과 공유하세요. 상대방은 공유받은 텍스트 파일로 `pip install -r requirements.txt`를 실행해 똑같은 가상환경을 구축할 수 있습니다.

---

## 7. 요약 및 핵심 체크리스트
1. **Homebrew**로 모든 설치의 기초 마련하기
2. **pyenv**로 버전 관리하고 셸 변수(`.zshrc`) 등록하기
3. 프로젝트 폴더마다 **`python -m venv .venv`**로 가상환경 구축하고 격리하기
4. `.venv/` 경로는 절대 Git에 올리지 말고 **`.gitignore`**에 꼭 등록하기

> 본 가이드는 macOS Sequoia 및 M 시리즈 프로세서 환경을 기준으로 검증되었습니다. 파이썬 설치 도중 문제가 생기거나 동작하지 않는 단계가 있다면 언제든 댓글로 상세 로그를 남겨주세요!
