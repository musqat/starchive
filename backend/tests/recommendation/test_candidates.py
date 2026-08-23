import pytest
from sqlalchemy import select

from app.domains.content.models import ContentType
from app.domains.recommendation import candidates, profile
from app.domains.user.models import User

MOVIE = "tmdb_157336"  # 인터스텔라
BOOK = "aladin_9788937460586"  # 싯다르타


def seed_user(db):
    """기록이 많은 시드유저 하나"""
    return db.scalars(select(User).where(User.is_seed.is_(True)).limit(1)).first()


@pytest.mark.db  # 기록이 없으면 프로필 벡터도 없다
def test_profile_none_without_records(db_session, credentials):
    from app.core.security import hash_password

    user = User(
        email=credentials["email"],
        password_hash=hash_password(credentials["password"]),
        nickname="빈유저",
    )
    db_session.add(user)
    db_session.flush()

    assert profile.build(db_session, user.id) is None


@pytest.mark.db  # 시드는 평점이 많아 프로필 벡터가 만들어진다
def test_profile_from_seed(db_session):
    user = seed_user(db_session)

    vector = profile.build(db_session, user.id)

    assert vector is not None
    assert len(vector) == 1536


@pytest.mark.db  # 후보는 내가 이미 기록한 것을 빼고 나온다
def test_candidates_exclude_recorded(db_session):
    user = seed_user(db_session)

    rows = candidates.generate(db_session, user.id, limit=30)

    assert rows
    assert len(rows) <= 30

    recorded = set(
        db_session.scalars(
            select(candidates.UserContent.content_id).where(
                candidates.UserContent.user_id == user.id
            )
        )
    )
    assert not {c.content_id for c in rows} & recorded


@pytest.mark.db  # 점수는 두 신호의 가중합
def test_candidate_score_is_weighted_sum(db_session):
    user = seed_user(db_session)

    rows = candidates.generate(db_session, user.id, limit=5)

    for c in rows:
        expected = (
            candidates.CONTENT_WEIGHT * c.content_score + candidates.TASTE_WEIGHT * c.taste_score
        )
        assert c.score == pytest.approx(expected)


@pytest.mark.db  # type 을 주면 그 타입만 나온다
def test_candidates_filter_type(db_session):
    user = seed_user(db_session)

    rows = candidates.generate(db_session, user.id, type_=ContentType.MOVIE, limit=10)

    assert rows
    assert all(c.type is ContentType.MOVIE for c in rows)


@pytest.mark.db  # only_ids 를 주면 그 안에서만 고른다. 카탈로그가 늘어도 평가가 안 흔들린다
def test_candidates_restricted_to_only_ids(db_session):
    user = seed_user(db_session)
    full = candidates.generate(db_session, user.id, ContentType.MOVIE)
    assert len(full) > 3

    allowed = {c.content_id for c in full[:3]}
    limited = candidates.generate(db_session, user.id, ContentType.MOVIE, only_ids=allowed)

    assert {c.content_id for c in limited} <= allowed


@pytest.mark.db  # 상위 하나만 뽑으면 모두가 같은 신작을 받는다. 상위 N 에서 무작위로 뽑는다
def test_recent_picks_vary_between_users(db_session):
    import random

    from app.domains.recommendation.candidates import recent_picks

    users = list(
        db_session.scalars(select(User.id).where(User.is_seed.is_(True)).order_by(User.id).limit(8))
    )
    rng = random.Random(42)
    picked = [
        c.content_id
        for uid in users
        for c in recent_picks(db_session, uid, ContentType.MOVIE, rng=rng)
    ]

    assert len(picked) >= len(users)  # 유저마다 최소 한 편
    assert len(set(picked)) > len(picked) // 2  # 절반 넘게 서로 다르다
