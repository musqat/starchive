"""추천 API. 조회는 캐시만 읽고 LLM 을 부르지 않는다"""

import uuid
from datetime import UTC, datetime, timedelta

import pytest
from sqlalchemy import select

from app.core.config import settings
from app.domains.content.models import Content, ContentType
from app.domains.recommendation import pipeline
from app.domains.recommendation.models import ReasonSource, Recommendation
from app.domains.user.models import ContentStatus, User, UserContent


@pytest.fixture
def movies(db_session):
    """MIN_RATED 를 넘길 수 있게 넉넉히"""
    stmt = select(Content).where(Content.type == ContentType.MOVIE).limit(pipeline.MIN_RATED)
    return list(db_session.scalars(stmt).all())


def rate_all(db, user_id: int, movies) -> None:
    """MIN_RATED 검사를 통과시킨다"""
    db.add_all(
        [
            UserContent(
                user_id=user_id,
                content_id=movie.id,
                status=ContentStatus.DONE,
                rating=4.5,
            )
            for movie in movies
        ]
    )
    db.commit()


def stored_batch(db, user_id: int, movies, *, minutes_ago: int = 0) -> uuid.UUID:
    """추천 몇 줄과 포인터를 직접 넣는다. 배치 생성 경로는 test_pipeline 에서 본다"""
    batch_id = uuid.uuid4()
    made = datetime.now(UTC) - timedelta(minutes=minutes_ago)
    db.add_all(
        [
            Recommendation(
                batch_id=batch_id,
                content_id=movie.id,
                user_id=user_id,
                type=ContentType.MOVIE,
                rank=i,
                score=1.0 - i / 100,
                reason=f"이유{i}",
                reason_source=ReasonSource.LLM,
                generated_at=made,
            )
            for i, movie in enumerate(movies, start=1)
        ]
    )
    db.execute(
        User.__table__.update().where(User.id == user_id).values(current_rec_batch_id=batch_id)
    )
    db.commit()
    return batch_id


@pytest.mark.db  # 비로그인 → 401
def test_requires_login(client):
    assert client.get("/recommendations", params={"type": "MOVIE"}).status_code == 401


@pytest.mark.db  # type 없이 부르면 422. 매체를 섞지 않는다
def test_type_required(auth_client):
    assert auth_client.get("/recommendations").status_code == 422


@pytest.mark.db  # 추천이 없으면 빈 목록과 안내용 개수
def test_empty_without_batch(auth_client):
    body = auth_client.get("/recommendations", params={"type": "MOVIE"}).json()

    assert body["items"] == []
    assert body["generated_at"] is None
    assert body["rated_count"] == 0
    assert body["required_count"] == pipeline.MIN_RATED


@pytest.mark.db  # 저장된 배치를 순위대로 낸다
def test_returns_stored_batch(auth_client, db_session, credentials, movies):
    user = db_session.scalar(select(User).where(User.email == credentials["email"]))
    stored_batch(db_session, user.id, movies)

    body = auth_client.get("/recommendations", params={"type": "MOVIE"}).json()

    assert [i["rank"] for i in body["items"]] == list(range(1, len(movies) + 1))
    assert body["items"][0]["content"]["title"] == movies[0].title
    assert body["items"][0]["reason"] == "이유1"
    assert body["items"][0]["reason_source"] == "LLM"
    assert body["generated_at"] is not None


@pytest.mark.db  # 영화 배치만 있으면 책은 비어 있다
def test_book_empty_when_only_movies(auth_client, db_session, credentials, movies):
    user = db_session.scalar(select(User).where(User.email == credentials["email"]))
    stored_batch(db_session, user.id, movies)

    body = auth_client.get("/recommendations", params={"type": "BOOK"}).json()

    assert body["items"] == []


@pytest.mark.db  # 평가한 개수가 응답에 담긴다
def test_rated_count(auth_client, db_session, credentials, movies):
    user = db_session.scalar(select(User).where(User.email == credentials["email"]))
    rate_all(db_session, user.id, movies)
    db_session.commit()

    body = auth_client.get("/recommendations", params={"type": "MOVIE"}).json()

    assert body["rated_count"] == len(movies)


@pytest.mark.db  # 쿨다운 중에는 429 와 Retry-After
def test_refresh_cooldown(auth_client, db_session, credentials, movies):
    user = db_session.scalar(select(User).where(User.email == credentials["email"]))
    rate_all(db_session, user.id, movies)
    stored_batch(db_session, user.id, movies, minutes_ago=1)

    r = auth_client.post("/me/recommendations/refresh")

    assert r.status_code == 429
    assert 0 < int(r.headers["Retry-After"]) <= settings.REC_COOLDOWN_MINUTES * 60


@pytest.mark.db  # 평가가 부족하면 409. 화면 버튼만이 아니라 API 도 막는다
def test_refresh_requires_enough_ratings(auth_client):
    r = auth_client.post("/me/recommendations/refresh")

    assert r.status_code == 409
    assert str(pipeline.MIN_RATED) in r.json()["detail"]


@pytest.mark.db  # 비밀값이 없거나 틀리면 401
@pytest.mark.parametrize("header", [{}, {"Authorization": "Bearer wrong"}])  # 헤더는 latin-1
def test_cron_rejects_wrong_secret(client, header):
    assert client.get("/recommendations/cron", headers=header).status_code == 401


@pytest.mark.db  # 갱신 대상은 오래된 배치만. 방금 만든 것은 건너뛴다
def test_cron_skips_fresh_batch(client, db_session, credentials, movies, monkeypatch):
    monkeypatch.setattr(settings, "CRON_SECRET", "cron-test-secret")
    client.post("/auth/signup", json=credentials)
    user = db_session.scalar(select(User).where(User.email == credentials["email"]))
    stored_batch(db_session, user.id, movies, minutes_ago=1)

    r = client.get(
        "/recommendations/cron",
        headers={"Authorization": "Bearer cron-test-secret"},
    )

    assert r.status_code == 200
    assert user.id not in pipeline.stale_users(
        db_session,
        datetime.now(UTC) - timedelta(hours=settings.CRON_STALE_HOURS),
        settings.CRON_USER_LIMIT,
    )


@pytest.mark.db  # 배치가 없는 사람은 Cron 대상이 아니다. 첫 생성은 사용자가 누른다
def test_cron_ignores_users_without_batch(db_session, credentials, client):
    client.post("/auth/signup", json=credentials)
    user = db_session.scalar(select(User).where(User.email == credentials["email"]))

    targets = pipeline.stale_users(db_session, datetime.now(UTC), settings.CRON_USER_LIMIT)

    assert user.id not in targets
