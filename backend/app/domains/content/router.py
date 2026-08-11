import enum

from fastapi import APIRouter, Depends, HTTPException, Path, Query
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.core.db import get_db
from app.domains.content.models import Content, ContentType
from app.domains.content.schemas import ContentDetail, ContentPage

router = APIRouter(prefix="/contents", tags=["contents"])

# 표본이 적으면 평점을 신뢰할 수 없음
MIN_VOTES_FOR_RATING_SORT = 100


class SortKey(enum.StrEnum):
    POPULAR = "popular"
    RATING = "rating"
    RECENT = "recent"


class SortOrder(enum.StrEnum):
    DESC = "desc"
    ASC = "asc"


SORT_COLUMN = {
    SortKey.POPULAR: Content.external_popularity,
    SortKey.RATING: Content.external_rating,
    SortKey.RECENT: Content.release_date,
}


@router.get("/genres", summary="장르 목록", response_model=list[str])
def list_genres(
    type: ContentType | None = Query(None, description="지정하면 해당 타입의 장르만"),
    db: Session = Depends(get_db),
):
    """실제 데이터에 존재하는 장르만"""
    genre = func.unnest(Content.genre).label("genre")
    stmt = select(genre, func.count().label("n")).group_by(genre)
    if type:
        stmt = stmt.where(Content.type == type)
    return [row.genre for row in db.execute(stmt.order_by(func.count().desc()))]


@router.get("", response_model=ContentPage, summary="콘텐츠 목록")
def list_contents(
    q: str | None = Query(None, min_length=1, description="제목 부분 일치", examples=["반지의"]),
    type: ContentType | None = Query(None, description="지정하면 해당 타입만"),
    genre: str | None = Query(None, description="장르 정확히 일치", examples=["드라마"]),
    sort: SortKey = Query(SortKey.POPULAR, description="popular / rating / recent"),
    order: SortOrder = Query(SortOrder.DESC, description="desc / asc"),
    page: int = Query(1, ge=1, description="1 부터"),
    size: int = Query(20, ge=1, le=100, description="한 페이지 개수"),
    db: Session = Depends(get_db),
):
    """`total` 은 페이지가 아니라 필터 전체의 개수

    `sort=rating` 은 평가 수가 적은 항목을 제외
    """
    stmt = select(Content)
    if q:
        stmt = stmt.where(Content.title.ilike(f"%{q}%"))
    if type:
        stmt = stmt.where(Content.type == type)
    if genre:
        stmt = stmt.where(Content.genre.any(genre))
    if sort is SortKey.RATING:
        stmt = stmt.where(Content.external_popularity >= MIN_VOTES_FOR_RATING_SORT)

    total = db.scalar(select(func.count()).select_from(stmt.subquery()))

    column = SORT_COLUMN[sort]
    ordering = column.asc() if order is SortOrder.ASC else column.desc()
    stmt = stmt.order_by(ordering.nulls_last()).offset((page - 1) * size).limit(size)
    return {
        "items": db.scalars(stmt).all(),
        "total": total,
        "page": page,
        "size": size,
    }

@router.get(
    "/{content_id}",
    response_model=ContentDetail,
    summary="콘텐츠 상세",
    responses={404: {"description": "해당 id 없음"}},
)
def get_content(
    content_id: str = Path(..., description="목록 응답의 id", examples=["tmdb_278"]),
    db: Session = Depends(get_db),
):
    row = db.get(Content, content_id)
    if row is None:
        raise HTTPException(404, "content not found")
    return row