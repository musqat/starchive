"""추천 성능 측정 — 가린 평점을 얼마나 되찾나

좋아한 기록 일부를 트랜잭션 안에서 지우고, 추천이 그걸 되찾는지 본다.
같은 홀드아웃으로 인기순도 재 비교 기준으로 쓴다

    uv run python -m scripts.evaluate
    uv run python -m scripts.evaluate --users 50
"""

import random
import sys
from math import log2

from sqlalchemy import delete, func, select
from sqlalchemy.orm import Session as SessionType

from app.domains.content.models import Content, ContentType
from app.domains.recommendation import candidates, profile
from app.domains.user.models import User, UserContent
from app.ingestion.db import Session

MIN_RATED = 20  # 20% 를 가려 정답 4건 -> 지표 분산을 위해서
HOLDOUT = 0.2
K = 10  # 화면에 띄울 개수와 맞춤
SEED = 42  # 튜닝 전후 비교용 고정값
USERS = 200


def pick_users(db: SessionType, limit: int) -> list[int]:
    """평가할 시드 유저. 기록이 적은 계정은 제외"""
    rows = db.execute(
        select(UserContent.user_id)
        .join(User, User.id == UserContent.user_id)
        .where(User.is_seed.is_(True), UserContent.rating >= profile.LIKED_RATING)
        .group_by(UserContent.user_id)
        .having(func.count() >= MIN_RATED)
        .order_by(UserContent.user_id)  # 매번 같은 표본
        .limit(limit)
    ).all()
    return [row.user_id for row in rows]


def split(liked: list[str], rng: random.Random) -> list[str]:
    """가릴 목록. 원본은 건드리지 않음"""
    shuffled = sorted(liked)  # DB 반환 순서와 무관하게 재현
    rng.shuffle(shuffled)
    return shuffled[: max(1, round(len(shuffled) * HOLDOUT))]


def by_popularity(db: SessionType, user_id: int, limit: int = K) -> list[str]:
    """인기순 — 좋아한 사람이 많은 순. 비교 기준"""
    rows = db.execute(
        select(UserContent.content_id, func.count().label("likes"))
        .join(Content, Content.id == UserContent.content_id)
        .where(
            UserContent.rating >= profile.LIKED_RATING,
            Content.type == ContentType.MOVIE,
            UserContent.content_id.not_in(
                select(UserContent.content_id).where(UserContent.user_id == user_id)
            ),
        )
        .group_by(UserContent.content_id)
        .order_by(func.count().desc())
        .limit(limit)
    ).all()
    return [row.content_id for row in rows]


def recall(ranked: list[str], truth: set[str]) -> float:
    """가린 것 중 상위 K 에서 되찾은 비율

    정답이 K 보다 많으면 최댓값이 1.0 미만. 인기순도 같은 분모
    """
    return sum(1 for content_id in ranked[:K] if content_id in truth) / len(truth)


def ndcg(ranked: list[str], truth: set[str]) -> float:
    """맞춘 것이 위쪽일수록 높음. 순위까지 보는 지표"""
    gain = sum(1 / log2(i + 2) for i, cid in enumerate(ranked[:K]) if cid in truth)
    ideal = sum(1 / log2(i + 2) for i in range(min(K, len(truth))))
    return gain / ideal if ideal else 0.0


def evaluate_one(db: SessionType, user_id: int, rng: random.Random) -> tuple[float, ...] | None:
    """한 유저의 recall / ndcg / 인기순 recall / 인기순 ndcg

    커밋하지 않아 지운 상태가 이 트랜잭션 밖으로 안 나간다
    """
    liked = list(
        db.scalars(
            select(UserContent.content_id)
            .join(Content, Content.id == UserContent.content_id)
            .where(
                UserContent.user_id == user_id,
                UserContent.rating >= profile.LIKED_RATING,
                Content.type == ContentType.MOVIE,
            )
        ).all()
    )
    if len(liked) < MIN_RATED:
        return None

    held = split(liked, rng)
    truth = set(held)

    try:
        db.execute(
            delete(UserContent).where(
                UserContent.user_id == user_id, UserContent.content_id.in_(held)
            ),
            execution_options={"synchronize_session": False},
        )
        db.flush()  # 이어지는 조회에 반영

        got = candidates.generate(db, user_id, ContentType.MOVIE, limit=K)
        ranked = [c.content_id for c in got]
        popular = by_popularity(db, user_id)
    finally:
        db.rollback()  # 가린 기록을 되돌림

    return recall(ranked, truth), ndcg(ranked, truth), recall(popular, truth), ndcg(popular, truth)


def main() -> None:
    limit = USERS
    if "--users" in sys.argv:
        limit = int(sys.argv[sys.argv.index("--users") + 1])

    rng = random.Random(SEED)

    with Session() as db:
        users = pick_users(db, limit)
        print(f"평가 대상 {len(users)}명 (좋아한 영화 {MIN_RATED}건 이상)\n")

        scored = [r for uid in users if (r := evaluate_one(db, uid, rng))]

    if not scored:
        print("평가할 유저가 없음")
        return

    n = len(scored)
    avg = [sum(col) / n for col in zip(*scored, strict=True)]

    print(f"{'':10} {'Recall@' + str(K):>10} {'NDCG@' + str(K):>10}")
    print(f"{'추천':10} {avg[0]:>10.3f} {avg[1]:>10.3f}")
    print(f"{'인기순':9} {avg[2]:>10.3f} {avg[3]:>10.3f}")
    print(f"\n유저 {n}명 평균 / seed={SEED}")


if __name__ == "__main__":  # import 시 실행 방지
    main()
