import enum

from fastapi import APIRouter, Depends, HTTPException, Path, Query
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.core.db import get_db
from app.core.deps import get_current_user_optional
from app.domains.content.models import Content, ContentType
from app.domains.content.schemas import ContentDetail, ContentPage, PublicMemo
from app.domains.user.models import User, UserContent

router = APIRouter(prefix="/contents", tags=["contents"])

# 표본이 적으면 평점을 신뢰할 수 없음
MIN_VOTES_FOR_RATING_SORT = 100


def attach_records(db: Session, user: User | None, items: list[Content]) -> list[Content]:
    """응답 스키마의 my_* 필드를 채운다. 비로그인이면 기본값"""
    if not user or not items:
        return items

    stmt = select(UserContent).where(
        UserContent.user_id == user.id,
        UserContent.content_id.in_([c.id for c in items]),
    )
    records = {r.content_id: r for r in db.scalars(stmt).unique()}

    for content in items:
        record = records.get(content.id)
        content.my_status = record.status if record else None
        content.my_rating = record.rating if record else None
        content.my_liked = record.liked if record else False
        content.my_recommended = record.recommended if record else False
        content.my_memo = record.memo if record else None
        content.my_memo_public = record.memo_public if record else False
    return items


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
    unseen: bool = Query(False, description="내가 기록한 것 제외. 비로그인이면 무시"),
    page: int = Query(1, ge=1, description="1 부터"),
    size: int = Query(20, ge=1, le=100, description="한 페이지 개수"),
    user: User | None = Depends(get_current_user_optional),
    db: Session = Depends(get_db),
):
    """
    total 은 페이지가 아니라 필터 전체의 개수
    sort=rating 은 평가 수가 적은 항목을 제외
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
    if unseen and user:
        seen = select(UserContent.content_id).where(UserContent.user_id == user.id)
        stmt = stmt.where(Content.id.not_in(seen))

    total = db.scalar(select(func.count()).select_from(stmt.subquery()))

    column = SORT_COLUMN[sort]
    ordering = column.asc() if order is SortOrder.ASC else column.desc()
    stmt = stmt.order_by(ordering.nulls_last()).offset((page - 1) * size).limit(size)
    return {
        "items": attach_records(db, user, list(db.scalars(stmt).all())),
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
    user: User | None = Depends(get_current_user_optional),
    db: Session = Depends(get_db),
):
    row = db.get(Content, content_id)
    if row is None:
        raise HTTPException(404, "content not found")
    return attach_records(db, user, [row])[0]


@router.get(
    "/{content_id}/memos",
    response_model=list[PublicMemo],
    summary="공개 메모",
)
def list_public_memos(
    content_id: str = Path(..., description="목록 응답의 id"),
    limit: int = Query(20, ge=1, le=50),
    user: User | None = Depends(get_current_user_optional),
    db: Session = Depends(get_db),
):
    """공개로 켠 것만. 내 메모는 상세 응답에 있으므로 뺀다"""
    stmt = (
        select(UserContent)
        .where(
            UserContent.content_id == content_id,
            UserContent.memo_public.is_(True),
            UserContent.memo.isnot(None),
        )
        .order_by(UserContent.updated_at.desc())
        .limit(limit)
    )
    if user:
        stmt = stmt.where(UserContent.user_id != user.id)

    return [
        PublicMemo(
            nickname=record.user.nickname,
            memo=record.memo,
            rating=record.rating,
            updated_at=record.updated_at,
        )
        for record in db.scalars(stmt).unique()
    ]