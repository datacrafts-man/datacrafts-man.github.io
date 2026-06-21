---
title: "Pydantic 사용법: API 데이터 검증과 직렬화 한 방에 해결하기"
date: 2026-06-16T22:05:00+09:00
draft: true
tags: ["python", "pydantic", "데이터검증", "FastAPI"]
categories: ["python"]
description: "파이썬의 대표적인 데이터 검증 라이브러리인 Pydantic v2의 핵심 사용법(BaseModel, 타입 선언, validator)을 실무적인 코드 예제와 함께 단계별로 마스터합니다."
ShowToc: true
TocOpen: false
---

외부 API나 환경 변수, 사용자 입력 등 가공되지 않은 외부 데이터를 다룰 때 가장 중요한 것은 데이터의 정합성 검증입니다. 기존 파이썬에서는 수많은 `if` 문이나 `isinstance` 체크 코드를 도배하여 데이터를 검사하곤 했습니다. 결론부터 말씀드리면, **Pydantic은 파이썬의 타입 힌트를 활용해 클래스 정의 한 번으로 입력 데이터의 유효성 검증(Validation)과 타입 변환 및 직렬화(Serialization)를 모두 자동화해 주는 표준 도구**입니다.

과거의 저는 데이터 파이프라인을 구축하면서 잘못 들어온 누락된 필드나 문자열로 형변환된 숫자형 데이터 때문에 서버가 죽는 에러를 수없이 겪었습니다. 당시 딕셔너리로 데이터를 관리하다가 한계를 느끼고 `Pydantic`을 도입한 후, 무의미한 검증 코드 수백 줄이 단 몇 줄의 클래스 선언으로 줄어드는 마법을 경험했습니다. 이 글에서는 Pydantic의 중심인 `BaseModel` 정의부터 필드 유효성 검사기(`validator`) 구현까지 실무에 바로 적용할 수 있는 단계별 튜토리얼을 공유해 드립니다.

---

## 1. Pydantic의 핵심 동작 모델 (BaseModel)

Pydantic의 모든 데이터 모델은 `BaseModel`을 상속받아 구현합니다. 각 필드에 파이썬 표준 타입 힌트를 지정하면, Pydantic은 인스턴스 생성 시점에 들어온 값이 해당 타입과 호환되는지 검증하고 필요에 따라 자동 강제 형변환(Coercion)을 처리합니다.

```python
from pydantic import BaseModel, Field

class User(BaseModel):
    id: int               # 필수 필드, 정수형 자동 변환 가능
    name: str             # 필수 필드, 문자열
    email: str | None = None  # 선택적 필드, 기본값 None
    age: int = Field(default=18, ge=0, le=120)  # 필드 세부 제약 (0세 이상 120세 이하)
```

---

## 2. Pydantic을 이용한 데이터 검증 실습 (단계별 가이드)

Pydantic을 프로젝트에 적용하고 데이터를 검증하는 3단계 프로세스를 구현해 보겠습니다.

### 1단계: 올바른 데이터 입력 및 형변환
Pydantic은 데이터 형변환을 영리하게 수행합니다. 예를 들어 문자열 `"123"`은 `int` 필드에 맞게 정수 `123`으로 변환됩니다.

```python
# 문자열 형태의 id와 age를 가진 데이터 입력
raw_data = {
    "id": "42",
    "name": "Minsu",
    "email": "minsu@example.com",
    "age": "28"
}

user = User(**raw_data)
print(user.id)   # 출력: 42 (정수형으로 자동 변환됨!)
print(user.age)  # 출력: 28 (정수형으로 자동 변환됨!)
```

### 2단계: 유효하지 않은 데이터 입력 시 에러 처리
입력 제약 조건을 벗어나거나 필수 필드가 누락되면 Pydantic은 즉시 `ValidationError`를 발생시킵니다.

```python
from pydantic import ValidationError

bad_data = {
    "id": "not_an_int",  # 정수 변환 불가능한 값
    "name": "Minsu",
    "age": -5            # ge=0 조건 위반
}

try:
    User(**bad_data)
except ValidationError as e:
    print(e.json())  # 에러 세부 사항을 JSON 포맷으로 확인 가능
```

### 3단계: 커스텀 검증기 (Validator) 추가하기
Pydantic v2에서는 `@field_validator` 데코레이터를 사용하여 특정 필드에 대한 복잡한 비즈니스 로직 검증을 유연하게 추가할 수 있습니다.

```python
from pydantic import BaseModel, field_validator

class SignUpRequest(BaseModel):
    username: str
    password: str
    confirm_password: str

    @field_validator("confirm_password")
    @classmethod
    def passwords_match(cls, v: str, info) -> str:
        # info.data에서 다른 필드 값에 접근 가능
        if "password" in info.data and v != info.data["password"]:
            raise ValueError("비밀번호가 서로 일치하지 않습니다.")
        return v
```

---

## 3. Pydantic v1과 v2 주요 차이점 비교

현재 업계 표준인 Pydantic v2는 내부 코어를 Rust로 재작성하여 v1 대비 엄청난 속도 개선을 이루어냈습니다. 실무에서 헷갈리기 쉬운 두 버전의 주요 차이점은 다음과 같습니다.

| 비교 항목 | Pydantic v1 | Pydantic v2 (현재 표준) |
| :--- | :--- | :--- |
| **코어 구현 언어** | Python | Rust (성능 최대 50배 향상) |
| **커스텀 검증기 데코레이터** | `@validator`, `@root_validator` | `@field_validator`, `@model_validator` |
| **딕셔너리 변환 메서드** | `model.dict()` | `model.model_dump()` |
| **JSON 직렬화 메서드** | `model.json()` | `model.model_dump_json()` |

---

## 4. 실무 도입 시 자주 범하는 에러와 주의사항

*   **Pydantic 모델을 변경 불가능하게 만들기**: 데이터가 중간에 임의로 변경되는 것을 막고 싶다면 configuration을 수정하여 모델을 읽기 전용(Frozen)으로 설정하세요. (v2 기준 `model_config = ConfigDict(frozen=True)` 사용)
*   **Mutable 기본값 할당 금지**: 필드의 기본값으로 빈 리스트 `[]`나 딕셔너리 `{}`를 직접 할당하는 것은 파이썬의 고질적인 공유 객체 에러를 낳을 수 있으므로 지양하고, `Field(default_factory=list)`를 사용해 안전하게 할당하는 것이 좋습니다.
*   **타입 어노테이션 오용**: Pydantic은 런타임에 유효성을 검증하지만, 편집기 레벨의 린터(Mypy, Pyright 등)가 정상 작동하도록 타입 명시 규칙을 철저히 따라야 협업 시 에러를 예방할 수 있습니다.

---

## 5. 자주 묻는 질문 (FAQ)

### Q. Pydantic과 Python 내장 dataclass는 무엇이 다른가요?
Python 내장 `dataclasses`는 단순히 데이터를 묶는 경량 객체를 생성하며, 기본적으로 런타임 타입 검증을 수행하지 않습니다. 반면 `Pydantic`은 런타임에 엄격하게 타입을 파싱하고 유효성 에러를 일으키는 검증 프레임워크입니다. API 통신이나 외부 데이터 검증이 동반되는 환경에서는 Pydantic이 압도적으로 유리합니다.

### Q. Pydantic 모델 인스턴스에서 원시 딕셔너리나 JSON으로 어떻게 변환하나요?
Pydantic v2부터는 `user.model_dump()` 메서드를 호출하여 딕셔너리로 변환할 수 있고, JSON 문자열로 뽑으려면 `user.model_dump_json()`을 실행하면 됩니다. (이전 v1의 `dict()`와 `json()`은 deprecated 되었습니다.)

### Q. 환경 변수(.env) 파일을 파이썬 객체로 쉽게 매핑할 수도 있나요?
네, `pydantic-settings` 라이브러리를 설치한 뒤 `BaseSettings` 클래스를 상속받아 모델을 만들면, `.env`나 시스템 환경 변수의 값들을 자동으로 검증하여 파이썬 설정 객체로 깔끔하게 파싱해 줍니다.

> 본 글은 Pydantic 라이브러리의 버전 사양 및 정보 제공을 위해 작성되었습니다. 신규 v2 버전과 구 v1 버전을 혼용할 경우 빌드 타임에 패키지 임포트 에러가 발생할 수 있으므로, 사용 중인 패키지의 버전 요구사항을 확인하시길 바랍니다.
