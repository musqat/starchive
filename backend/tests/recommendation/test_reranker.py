"""LLM 응답 파싱과 폴백. API 를 부르지 않는다"""

import json

import httpx
import pytest

from app.domains.content.models import ContentType
from app.domains.recommendation import reranker
from app.domains.recommendation.candidates import Candidate
from app.domains.recommendation.models import ReasonSource


def make(n: int) -> list[Candidate]:
    return [
        Candidate(
            content_id=f"tmdb_{i}",
            title=f"작품{i}",
            type=ContentType.MOVIE,
            score=1.0 - i / 100,
            content_score=0.5,
            taste_score=0.5,
        )
        for i in range(n)
    ]


def answer(numbers: list[int]) -> str:
    return json.dumps({"picks": [{"n": n, "reason": f"이유{n}"} for n in numbers]})


@pytest.fixture
def patched(monkeypatch):
    """complete_json 을 정해둔 문자열로 바꾼다"""

    def use(raw: str | Exception):
        async def fake(client, system, user):
            if isinstance(raw, Exception):
                raise raw
            return raw

        monkeypatch.setattr(reranker, "complete_json", fake)

    return use


async def test_picks_in_order(patched):
    """LLM 이 준 번호 순서가 rank 가 된다"""
    patched(answer([3, 1, 2]))

    ranked = await reranker.rerank(None, [], make(30), [])

    assert [r.candidate.content_id for r in ranked[:3]] == ["tmdb_2", "tmdb_0", "tmdb_1"]
    assert [r.rank for r in ranked[:3]] == [1, 2, 3]
    assert ranked[0].source is ReasonSource.LLM


async def test_drops_out_of_range_and_duplicates(patched):
    """범위 밖과 중복 번호는 버린다"""
    patched(answer([1, 1, 999, 0, -5, 2]))

    ranked = await reranker.rerank(None, [], make(30), [])
    llm = [r for r in ranked if r.source is ReasonSource.LLM]

    assert [r.candidate.content_id for r in llm] == ["tmdb_0", "tmdb_1"]


async def test_fills_to_ten_when_short(patched):
    """10개를 못 채우면 점수순으로 메운다"""
    patched(answer([5, 6]))

    ranked = await reranker.rerank(None, [], make(30), [])

    assert len(ranked) == reranker.TOP_K
    assert [r.rank for r in ranked] == list(range(1, 11))
    assert ranked[2].source is ReasonSource.TEMPLATE


async def test_falls_back_on_broken_json(patched):
    """JSON 이 아니면 점수순 전체"""
    patched("이건 JSON 이 아님")

    ranked = await reranker.rerank(None, [], make(30), [])

    assert len(ranked) == reranker.TOP_K
    assert all(r.source is ReasonSource.TEMPLATE for r in ranked)
    assert [r.candidate.content_id for r in ranked] == [f"tmdb_{i}" for i in range(10)]


async def test_falls_back_on_http_error(patched):
    """호출이 실패해도 추천은 나온다"""
    patched(httpx.ConnectError("끊김"))

    ranked = await reranker.rerank(None, [], make(30), [])

    assert all(r.source is ReasonSource.TEMPLATE for r in ranked)


async def test_empty_candidates(patched):
    """후보가 없으면 빈 목록. LLM 을 부르지 않는다"""
    patched(httpx.ConnectError("불리면 안 됨"))

    assert await reranker.rerank(None, [], [], []) == []
