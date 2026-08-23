"""하이브리드 검색 + RAG 코멘트

정확 매칭(제목·감독·배우) + 의미 검색(벡터) + 자연어일 때 LLM 코멘트.
임베딩·코멘트 호출을 가짜로 바꿔 OpenAI 없이 경로를 확인한다
"""

import pytest
from sqlalchemy import select

from app.domains.content import search_router
from app.domains.content.models import Content, ContentType
from app.ingestion.db import Session


def _first_movie():
    with Session() as db:
        return db.execute(
            select(Content.id, Content.title, Content.embedding).where(
                Content.type == ContentType.MOVIE, Content.embedding.isnot(None)
            )
        ).first()


@pytest.fixture
def no_comment(monkeypatch):
    """코멘트 LLM 을 끈다 — 검색 경로만 볼 때"""

    async def none(query, items):
        return None

    monkeypatch.setattr(search_router, "_comment", none)


@pytest.mark.db  # 벡터로 자기 자신을 검색하면 상위에 나온다
def test_search_semantic_ranks_self(client, monkeypatch, no_comment):
    row = _first_movie()

    async def fake_embed(query):
        return list(row.embedding)

    monkeypatch.setattr(search_router, "_embed_query", fake_embed)

    r = client.get("/search", params={"q": "zzz없는검색어xyz", "type": "MOVIE"})
    assert r.status_code == 200
    ids = [it["id"] for it in r.json()["items"]]
    assert ids and ids[0] == row.id


@pytest.mark.db  # 제목 정확 매칭은 임베딩 없이도 된다
def test_search_exact_title_without_embedding(client, monkeypatch, no_comment):
    async def no_vector(query):
        return None

    monkeypatch.setattr(search_router, "_embed_query", no_vector)

    row = _first_movie()
    r = client.get("/search", params={"q": row.title, "type": "MOVIE"})
    assert r.status_code == 200
    assert row.id in [it["id"] for it in r.json()["items"]]


@pytest.mark.db  # 정확 매칭도 벡터도 없으면 빈 결과
def test_search_no_match_returns_empty(client, monkeypatch, no_comment):
    async def no_vector(query):
        return None

    monkeypatch.setattr(search_router, "_embed_query", no_vector)

    r = client.get("/search", params={"q": "zzz매칭안되는검색어xyz"})
    assert r.status_code == 200
    body = r.json()
    assert body["items"] == []
    assert body["comment"] is None


@pytest.mark.db  # 제목 정확 매칭이면 코멘트를 안 만든다
def test_exact_match_skips_comment(client, monkeypatch):
    async def no_vector(query):
        return None

    called = False

    async def spy_comment(query, items):
        nonlocal called
        called = True
        return "골랐어요"

    monkeypatch.setattr(search_router, "_embed_query", no_vector)
    monkeypatch.setattr(search_router, "_comment", spy_comment)

    row = _first_movie()
    r = client.get("/search", params={"q": row.title, "type": "MOVIE"})
    assert r.json()["comment"] is None
    assert not called  # 정확 매칭이라 코멘트 호출 안 함


@pytest.mark.db
def test_search_blank_query_rejected(client):
    r = client.get("/search", params={"q": ""})
    assert r.status_code == 422  # min_length=1
