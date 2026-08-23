"""같은 작품의 다른 판본 걸러내기

알라딘은 판본마다 ISBN 이 달라 `싯다르타`, `싯다르타 (양장)`, `초판본 싯다르타` 가
서로 다른 content_id 로 들어온다. content_id 로만 거르면 이미 읽은 책이 추천된다

영화 시리즈(`매트릭스` / `매트릭스 2: 리로디드`)는 다른 작품
"""

import re

# 판본·형태 표기. `싯다르타 (양장)`, `혼모노 (리커버, 양장)`
_BRACKETS = re.compile(r"[(\[{][^)\]}]*[)\]}]")
# 부제·수상 이력. `소년이 온다 - 2024 노벨문학상 수상작가`
_SUFFIX = re.compile(r"\s+[-–—:]\s+.*$")
# 판본 수식어. `초판본 싯다르타`, `개정판 데미안`
_EDITION = re.compile(r"^(초판본|개정판|완역본|합본|양장본|리커버)\s+")
_SPACES = re.compile(r"\s+")


def normalize(title: str) -> str:
    """판본 표기를 걷어낸 제목 -> 비교 전용"""
    text = _BRACKETS.sub(" ", title)
    text = _SUFFIX.sub("", text)
    text = _EDITION.sub("", text.strip())
    return _SPACES.sub(" ", text).strip().casefold()


def cap_series(items: list, limit: int) -> list:
    """한 시리즈에서 limit 편까지만. 점수순으로 들어온다고 가정한다

    스타워즈 6편이 상위 10을 나눠 갖는다. 시드가 시리즈 전편에 고르게 높은 점수를 준 탓
    """
    counts: dict[str, int] = {}
    kept = []
    for item in items:
        series = getattr(item, "series", None)
        if series:
            counts[series] = counts.get(series, 0) + 1
            if counts[series] > limit:
                continue
        kept.append(item)
    return kept


def drop_duplicates(items: list, seen: set[str], key=lambda x: x.title) -> list:
    """정규화 제목이 겹치면 앞의 것만 남긴다. seen 은 호출한 쪽에서 채워 보낸다"""
    kept = []
    for item in items:
        name = normalize(key(item))
        if not name or name in seen:
            continue
        seen.add(name)
        kept.append(item)
    return kept
