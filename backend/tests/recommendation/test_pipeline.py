"""배치 저장과 포인터 교체. LLM 은 부르지 않는다"""

import uuid

import pytest
from sqlalchemy import func, select

from app.core.security import hash_password
from app.domains.content.models import Content, ContentType
from app.domains.recommendation import candidates, pipeline, reranker
from app.domains.recommendation.models import ReasonSource, Recommendation
from app.domains.user.models import ContentStatus, User, UserContent


@pytest.fixture
def user(db_session, credentials):
    """빈 계정 하나. credentials 가 나중에 정리"""
    row = User(
        email=credentials["email"],
        password_hash=hash_password(credentials["password"]),
        nickname="테스터",
    )
    db_session.add(row)
    db_session.commit()
    return row


@pytest.fixture
def movies(db_session):
    """후보로 쓸 영화 몇 편"""
    stmt = select(Content).where(Content.type == ContentType.MOVIE).limit(12)
    return list(db_session.scalars(stmt).all())


@pytest.fixture
def stub(monkeypatch, movies):
    """candidates.generate 와 rerank 를 고정 결과로 바꾼다"""
    found = [
        candidates.Candidate(
            content_id=m.id,
            title=m.title,
            type=ContentType.MOVIE,
            score=1.0 - i / 100,
            content_score=0.5,
            taste_score=0.5,
        )
        for i, m in enumerate(movies)
    ]

    def fake_generate(db, user_id, type_=None, limit=None):
        return found if type_ is ContentType.MOVIE else []  # 책은 후보 없음

    async def fake_rerank(client, liked, cands, items):
        return reranker.fallback(cands)

    monkeypatch.setattr(candidates, "generate", fake_generate)
    monkeypatch.setattr(reranker, "rerank", fake_rerank)
    return found


@pytest.mark.db  # 배치를 만들면 포인터가 그 배치를 가리킨다
async def test_refresh_sets_pointer(db_session, user, stub):
    batch_id = await pipeline.refresh(db_session, None, user.id)

    assert batch_id is not None
    db_session.refresh(user)
    assert user.current_rec_batch_id == batch_id

    rows = pipeline.current(db_session, user.id)
    assert len(rows) == reranker.TOP_K
    assert [r.rank for r in rows] == list(range(1, 11))
    assert all(r.type is ContentType.MOVIE for r in rows)


@pytest.mark.db  # 후보가 없는 매체는 건너뛴다
async def test_skips_type_without_candidates(db_session, user, stub):
    await pipeline.refresh(db_session, None, user.id)

    assert pipeline.current(db_session, user.id, ContentType.BOOK) == []
    assert len(pipeline.current(db_session, user.id, ContentType.MOVIE)) == reranker.TOP_K


@pytest.mark.db  # 두 번 돌리면 옛 배치는 남고 포인터만 새것을 가리킨다
async def test_refresh_keeps_previous_but_moves_pointer(db_session, user, stub):
    first = await pipeline.refresh(db_session, None, user.id)
    second = await pipeline.refresh(db_session, None, user.id)

    assert first != second
    stored = db_session.scalar(
        select(func.count()).select_from(Recommendation).where(Recommendation.user_id == user.id)
    )
    assert stored == reranker.TOP_K * 2  # 두 배치가 다 남아 있다

    rows = pipeline.current(db_session, user.id)
    assert {r.batch_id for r in rows} == {second}  # 화면에는 새 배치만


@pytest.mark.db  # 포인터가 없으면 빈 목록
async def test_current_without_pointer(db_session, user):
    assert pipeline.current(db_session, user.id) == []


@pytest.mark.db  # 후보가 아예 없으면 배치를 만들지 않는다
async def test_refresh_returns_none_without_candidates(db_session, user, monkeypatch):
    monkeypatch.setattr(candidates, "generate", lambda *a, **k: [])

    assert await pipeline.refresh(db_session, None, user.id) is None
    db_session.refresh(user)
    assert user.current_rec_batch_id is None


@pytest.mark.db  # 폴백 배치도 저장된다. 이유는 템플릿
async def test_template_reason_saved(db_session, user, stub):
    await pipeline.refresh(db_session, None, user.id)

    rows = pipeline.current(db_session, user.id)
    assert all(r.reason_source is ReasonSource.TEMPLATE for r in rows)
    assert all(r.reason == reranker.TEMPLATE_REASON for r in rows)


@pytest.mark.db  # 취향 요약은 높게 평가한 것부터
def test_liked_titles_order(db_session, user, movies):
    db_session.add_all(
        [
            UserContent(
                user_id=user.id,
                content_id=movies[0].id,
                status=ContentStatus.DONE,
                rating=4.0,
            ),
            UserContent(
                user_id=user.id,
                content_id=movies[1].id,
                status=ContentStatus.DONE,
                rating=5.0,
            ),
        ]
    )
    db_session.commit()

    assert pipeline.liked_titles(db_session, user.id) == [movies[1].title, movies[0].title]


@pytest.mark.db  # 배치 안에 같은 작품이 두 번 들어갈 수 없다
async def test_duplicate_content_in_batch_rejected(db_session, user, movies):
    from sqlalchemy.exc import IntegrityError

    batch_id = uuid.uuid4()
    row = dict(
        batch_id=batch_id,
        user_id=user.id,
        content_id=movies[0].id,
        type=ContentType.MOVIE,
        score=0.5,
        reason_source=ReasonSource.TEMPLATE,
    )
    db_session.add_all([Recommendation(rank=1, **row), Recommendation(rank=2, **row)])

    with pytest.raises(IntegrityError):
        db_session.commit()
    db_session.rollback()
