"""하이브리드 검색 + RAG 코멘트

정확 매칭(제목·감독·배우) + 의미 검색(벡터) + 자연어일 때 LLM 코멘트.
임베딩·코멘트 호출을 가짜로 바꿔 OpenAI 없이 경로를 확인한다
"""

import pytest
from sqlalchemy import select

from app.core.config import settings
from app.core.ratelimit import limiter
from app.domains.content import search, search_router
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


@pytest.mark.db  # 공개 엔드포인트인데 호출마다 OpenAI 를 부른다. IP 당 분당 제한
def test_search_rate_limited(client, monkeypatch, no_comment):
    async def no_vector(query):
        return None

    monkeypatch.setattr(search_router, "_embed_query", no_vector)
    monkeypatch.setattr(settings, "SEARCH_RATE_LIMIT", "3/minute")
    limiter.reset()

    codes = [
        client.get("/search", params={"q": "zzz없는검색어xyz"}).status_code for _ in range(4)
    ]

    assert codes == [200, 200, 200, 429]


@pytest.mark.db  # 로그인하면 계정으로 센다. 같은 IP 의 익명이 막혀도 로그인 사용자는 자기 버킷
def test_search_limit_keyed_by_user_when_logged_in(client, credentials, monkeypatch, no_comment):
    async def no_vector(query):
        return None

    monkeypatch.setattr(search_router, "_embed_query", no_vector)
    monkeypatch.setattr(settings, "SEARCH_RATE_LIMIT", "2/minute")
    limiter.reset()

    params = {"q": "zzz없는검색어xyz"}
    anon = [client.get("/search", params=params).status_code for _ in range(3)]
    assert anon == [200, 200, 429]

    client.post("/auth/signup", json=credentials)
    client.post(
        "/auth/login",
        json={"email": credentials["email"], "password": credentials["password"]},
    )

    assert client.get("/search", params=params).status_code == 200


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


@pytest.mark.db  # 정확 매칭이 있으면 검색어 대신 그 작품의 임베딩으로 이웃을 찾는다. OpenAI 없이
def test_exact_match_uses_content_embedding_for_neighbors(client, monkeypatch, no_comment):
    async def must_not_embed(query):
        raise AssertionError("정확 매칭이 있는데 검색어를 임베딩했다")

    monkeypatch.setattr(search_router, "_embed_query", must_not_embed)

    row = _first_movie()
    with Session() as db:
        exact = search.by_exact(db, row.title, type_=ContentType.MOVIE)

    r = client.get("/search", params={"q": row.title, "type": "MOVIE"})
    assert r.status_code == 200
    ids = [it["id"] for it in r.json()["items"]]
    assert ids[: len(exact)] == exact  # 정확 매칭이 앞
    assert len(ids) > len(exact)  # 뒤에 작품 임베딩으로 찾은 이웃


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
