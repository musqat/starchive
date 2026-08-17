"""재랭킹 프롬프트 -> 문자열만 만든다"""

from dataclasses import dataclass

DESCRIPTION_CHARS = 200  # 줄거리 전문을 넣으면 후보 30개에 토큰이 몰린다
LIKED_LIMIT = 15
REASON_CHARS = 60

SYSTEM = f"""당신은 영화와 책을 추천하는 사람이다.

사용자가 높게 평가한 작품과 후보 목록을 받는다. 후보 중 10개를 골라 순서대로 낸다.

기준
- 사용자가 좋아한 작품과 겹치는 지점이 있을 것
- 10개가 한쪽으로 쏠리지 않게 할 것
- 같은 작품의 다른 판본과 같은 시리즈는 한 편만 고를 것
- 사용자가 이미 본 작품과 같은 작품이면 제목이 달라도 고르지 말 것
- 후보 목록 밖의 작품은 절대 고르지 말 것

이유는 한 문장, {REASON_CHARS}자 이내. 줄거리 요약이 아니라 이 사용자에게 왜 맞는지를 쓴다.
사용자가 좋아한 작품을 근거로 들 때는 제목을 적는다.
'대비된다', '다르다' 처럼 차이를 드는 것은 추천 근거가 아니다. 통하는 지점을 쓴다.

{{"picks": [{{"n": 후보번호, "reason": "이유"}}]}} 형태의 JSON 으로만 답한다."""


@dataclass
class PromptItem:
    """프롬프트에 넣을 후보"""

    title: str
    genre: list[str] | None
    description: str | None


def build_user(liked: list[str], items: list[PromptItem]) -> str:
    """후보는 1 부터 번호를 매긴다. content_id 를 그대로 주면 모델이 흘린다"""
    lines = ["## 사용자가 높게 평가한 작품", ", ".join(liked[:LIKED_LIMIT]), "", "## 후보"]

    for number, item in enumerate(items, start=1):
        head = f"{number}. {item.title}"
        if item.genre:
            head += f" ({', '.join(item.genre)})"
        lines.append(head)
        if item.description:
            lines.append(f"   {item.description[:DESCRIPTION_CHARS]}")

    lines += ["", f"이 중 10개를 골라 순서대로 낸다. 번호는 1~{len(items)}."]
    return "\n".join(lines)
