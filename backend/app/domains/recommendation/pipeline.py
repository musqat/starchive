"""후보 → 재랭킹 → 저장

배치를 다 넣은 뒤 마지막에 users.current_rec_batch_id 를 갱신
"""

import uuid
from datetime import datetime

import httpx
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.domains.content.models import Content, ContentType
from app.domains.recommendation import candidates, profile, reranker
from app.domains.recommendation.models import Recommendation
from app.domains.recommendation.prompts import LIKED_LIMIT, PromptItem
from app.domains.user.models import User, UserContent

TYPES = (ContentType.MOVIE, ContentType.BOOK)

# 콜드 스타트 곡선. 2편은 인기순의 0.72배, 3편은 동점, 5편부터 앞선다
MIN_RATED = 5


def rated_count(db: Session, user_id: int, type_: ContentType | None = None) -> int:
    """높게 평가한 개수"""
    stmt = (
        select(func.count())
        .select_from(UserContent)
        .join(Content, Content.id == UserContent.content_id)
        .where(UserContent.user_id == user_id, UserContent.rating >= profile.LIKED_RATING)
    )
    if type_:
        stmt = stmt.where(Content.type == type_)
    return db.scalar(stmt) or 0


def generated_at(db: Session, user_id: int) -> datetime | None:
    """현재 배치를 만든 시각"""
    return db.scalar(
        select(Recommendation.generated_at)
        .join(User, User.current_rec_batch_id == Recommendation.batch_id)
        .where(User.id == user_id)
        .limit(1)
    )


def stale_users(db: Session, older_than: datetime, limit: int) -> list[int]:
    """갱신할 사용자. 오래된 것부터, 상한까지만

    배치가 없는 사람은 넣지 않는다 — 첫 생성은 사용자가 직접 누른다
    """
    stmt = (
        select(User.id, func.min(Recommendation.generated_at).label("made"))
        .join(Recommendation, Recommendation.batch_id == User.current_rec_batch_id)
        .where(User.is_seed.is_(False))
        .group_by(User.id)
        .having(func.min(Recommendation.generated_at) < older_than)
        .order_by("made")
        .limit(limit)
    )
    return [row.id for row in db.execute(stmt)]


def liked_titles(db: Session, user_id: int, limit: int = LIKED_LIMIT) -> list[str]:
    """높게 평가한 작품 제목. 프롬프트에 넣을 취향 요약"""
    stmt = (
        select(Content.title)
        .join(UserContent, UserContent.content_id == Content.id)
        .where(UserContent.user_id == user_id, UserContent.rating >= profile.LIKED_RATING)
        .order_by(UserContent.rating.desc(), UserContent.updated_at.desc())
        .limit(limit)
    )
    return list(db.scalars(stmt).all())


def prompt_items(db: Session, found: list[candidates.Candidate]) -> list[PromptItem]:
    """후보 순서 그대로"""
    rows = db.execute(
        select(Content.id, Content.genre, Content.description).where(
            Content.id.in_([c.content_id for c in found])
        )
    ).all()
    by_id = {row.id: row for row in rows}
    return [
        PromptItem(
            title=c.title,
            genre=by_id[c.content_id].genre if c.content_id in by_id else None,
            description=by_id[c.content_id].description if c.content_id in by_id else None,
        )
        for c in found
    ]


async def build_batch(
    db: Session,
    client: httpx.AsyncClient,
    user_id: int,
    batch_id: uuid.UUID,
) -> list[Recommendation]:
    """한 사용자의 추천 행들, 저장은 하지 않는다"""
    liked = liked_titles(db, user_id)
    rows: list[Recommendation] = []

    for type_ in TYPES:
        found = candidates.generate(db, user_id, type_)
        if not found:
            continue  # 기록이 없는 매체. 화면에서 안내로 처리한다
        ranked = await reranker.rerank(client, liked, found, prompt_items(db, found))
        rows += [
            Recommendation(
                batch_id=batch_id,
                content_id=r.candidate.content_id,
                user_id=user_id,
                type=type_,
                rank=r.rank,
                score=r.candidate.score,
                reason=r.reason,
                reason_source=r.source,
            )
            for r in ranked
        ]
    return rows


async def refresh(db: Session, client: httpx.AsyncClient, user_id: int) -> uuid.UUID | None:
    """새 배치를 만들고 포인터를 옮긴다. 추천이 없으면 None

    옛 배치는 지우지 않는다 — 포인터가 안 가리키므로 화면에 안 나오고,
    나중에 추천이 어떻게 달라졌는지 되짚을 수 있다. 정리는 별도 작업
    """
    batch_id = uuid.uuid4()
    rows = await build_batch(db, client, user_id, batch_id)
    if not rows:
        return None

    db.add_all(rows)
    db.execute(
        User.__table__.update().where(User.id == user_id).values(current_rec_batch_id=batch_id)
    )
    db.commit()
    return batch_id


def current(db: Session, user_id: int, type_: ContentType | None = None) -> list[Recommendation]:
    """지금 보여줄 추천. 포인터가 없으면 빈 목록"""
    batch_id = db.scalar(select(User.current_rec_batch_id).where(User.id == user_id))
    if not batch_id:
        return []

    stmt = select(Recommendation).where(Recommendation.batch_id == batch_id)
    if type_:
        stmt = stmt.where(Recommendation.type == type_)
    return list(db.scalars(stmt.order_by(Recommendation.type, Recommendation.rank)).all())
