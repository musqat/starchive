"""판본 표기 정규화. DB 를 쓰지 않는다"""

from dataclasses import dataclass

import pytest

from app.domains.recommendation import dedupe


@pytest.mark.parametrize(
    "title",
    [
        "싯다르타",
        "싯다르타 (양장)",
        "초판본 싯다르타 - 1922년 오리지널 초판본",
        "싯다르타 [무선]",
        "개정판 싯다르타",
    ],
)
def test_editions_collapse(title):
    assert dedupe.normalize(title) == "싯다르타"


@pytest.mark.parametrize(
    ("left", "right"),
    [
        ("소년이 온다 - 2024 노벨문학상 수상작가", "소년이 온다"),
        ("혼모노 (리커버, 양장)", "혼모노"),
        ("데미안  ", " 데미안"),
        ("Sherlock", "sherlock"),
    ],
)
def test_same_work(left, right):
    assert dedupe.normalize(left) == dedupe.normalize(right)


@pytest.mark.parametrize(
    ("left", "right"),
    [
        ("매트릭스", "매트릭스 2: 리로디드"),  # 시리즈는 다른 작품
        ("대부", "대부 2"),
        ("싯다르타", "데미안"),
    ],
)
def test_different_work(left, right):
    assert dedupe.normalize(left) != dedupe.normalize(right)


@dataclass
class Item:
    title: str


def test_drop_duplicates_keeps_first():
    """점수순으로 들어오므로 앞의 것이 남는다"""
    items = [Item("싯다르타"), Item("싯다르타 (양장)"), Item("데미안")]

    kept = dedupe.drop_duplicates(items, set())

    assert [i.title for i in kept] == ["싯다르타", "데미안"]


def test_drop_duplicates_excludes_seen():
    """이미 기록한 작품은 판본이 달라도 빠진다"""
    items = [Item("초판본 싯다르타 - 1922년 오리지널 초판본"), Item("데미안")]

    kept = dedupe.drop_duplicates(items, {dedupe.normalize("싯다르타")})

    assert [i.title for i in kept] == ["데미안"]
