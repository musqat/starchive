"""취향 중심 — 내가 좋아한 작품들의 한가운데"""

from pgvector.sqlalchemy import Vector
from sqlalchemy import Select, func, select
from sqlalchemy.orm import Session

from app.domains.content.models import Content, ContentType
from app.domains.user.models import UserContent

LIKED_RATING = 4.0  # 이 위면 좋아한 것으로 봄
MIN_LIKED = 3  # 1~2건 평균은 한쪽으로 쏠림
FALLBACK_LIMIT = 10
DIMENSIONS = 1536


def _rated(user_id: int, type_: ContentType | None) -> Select:
    """임베딩이 있는 내 기록"""
    stmt = (
        select(Content.embedding.label("embedding"))
        .join(UserContent, UserContent.content_id == Content.id)
        .where(
            UserContent.user_id == user_id,
            UserContent.rating.isnot(None),
            Content.embedding.isnot(None),
        )
    )
    if type_:
        stmt = stmt.where(Content.type == type_)
    return stmt


def build(db: Session, user_id: int, type_: ContentType | None = None) -> list[float] | None:
    """좋아한 작품 임베딩의 평균. 기록이 없으면 None

    폴백 3단계
     1. 4.0 이상 3건 이상  →  그것들의 평균
     2. 4.0 이상 3건 미만  →  평점 상위 N건의 평균 (점수 무관)
     3. 평점 0건          →  None. 호출한 쪽에서 인기순으로 폴백

    평균은 Postgres 가 낸다. 파이썬으로 끌어오면 vector(1536) × 기록 수만큼 오간다
    """
    liked = _rated(user_id, type_).where(UserContent.rating >= LIKED_RATING).subquery()
    center, count = db.execute(
        select(func.avg(liked.c.embedding, type_=Vector(DIMENSIONS)), func.count())
    ).one()

    if count < MIN_LIKED:
        top = (
            _rated(user_id, type_)
            .order_by(UserContent.rating.desc(), UserContent.updated_at.desc())
            .limit(FALLBACK_LIMIT)
            .subquery()
        )
        center = db.scalar(select(func.avg(top.c.embedding, type_=Vector(DIMENSIONS))))

    return list(center) if center is not None else None
