"""공식 근거 자료(official reference materials).

이 목록에 있는 자료만 모델에 제공한다. 모델이 새로운 URL을 만들어내지 못하게
하고, 공식 근거가 없는 주제는 official_references를 빈 배열로 저장한다.
OpenAI Web Search tool은 사용하지 않는다.
"""

from __future__ import annotations

from typing import Any

INTERVIEW_REFERENCE_MATERIALS: list[dict[str, str]] = [
    {
        "topic": "java_oop",
        "title": "Oracle Java Tutorials - Object-Oriented Programming Concepts",
        "url": "https://docs.oracle.com/javase/tutorial/java/concepts/index.html",
        "summary": (
            "Java 공식 튜토리얼의 객체지향 프로그래밍 개념 설명. "
            "객체, 클래스, 상속, 인터페이스, 패키지 등의 기본 개념을 다룸."
        ),
    },
    {
        "topic": "java_object",
        "title": "Oracle Java Tutorials - What Is an Object?",
        "url": "https://docs.oracle.com/javase/tutorial/java/concepts/object.html",
        "summary": "객체는 관련된 상태와 행위를 묶은 소프트웨어 단위라는 설명을 제공함.",
    },
    {
        "topic": "java_class",
        "title": "Oracle Java Tutorials - What Is a Class?",
        "url": "https://docs.oracle.com/javase/tutorial/java/concepts/class.html",
        "summary": "클래스는 개별 객체를 생성하기 위한 설계도라는 설명을 제공함.",
    },
    {
        "topic": "java_inheritance",
        "title": "Oracle Java Tutorials - What Is Inheritance?",
        "url": "https://docs.oracle.com/javase/tutorial/java/concepts/inheritance.html",
        "summary": "상속을 통해 클래스가 다른 클래스의 상태와 행위를 물려받을 수 있다는 설명을 제공함.",
    },
]

# 제공된 공식 근거 자료의 허용 URL 집합.
# 채점 결과에서 이 집합에 없는 URL은 모델이 지어낸 것으로 간주하고 제거한다.
ALLOWED_REFERENCE_URLS: frozenset[str] = frozenset(
    item["url"] for item in INTERVIEW_REFERENCE_MATERIALS
)

ALLOWED_REFERENCES_BY_URL: dict[str, dict[str, str]] = {
    item["url"]: item for item in INTERVIEW_REFERENCE_MATERIALS
}


def all_reference_materials() -> list[dict[str, Any]]:
    """질문 생성 시 모델에 제공할 전체 공식 근거 목록을 반환한다."""
    return [dict(item) for item in INTERVIEW_REFERENCE_MATERIALS]
