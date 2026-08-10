from fastapi import APIRouter, Depends, HTTPException, Path, Query
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.core.db import get_db
from app.domains.content.models import Content, ContentType
from app.domains.content.schemas import ContentDetail, ContentPage

router = APIRouter(prefix="/contents", tags=["contents"])


@router.get("", response_model=ContentPage, summary="콘텐츠 목록")
def list_contents(
    q: str | None = Query(None, min_length=1, description="제목 부분 일치", examples=["반지의"]),
    type: ContentType | None = Query(None, description="지정하면 해당 타입만"),
    page: int = Query(1, ge=1, description="1 부터"),
    size: int = Query(20, ge=1, le=100, description="한 페이지 개수"),
    db: Session = Depends(get_db),
):
    """평가 수 내림차순. `total` 은 페이지가 아니라 필터 전체의 개수."""
    stmt = select(Content)
    if q:
        stmt = stmt.where(Content.title.ilike(f"%{q}%"))
    if type:
        stmt = stmt.where(Content.type == type)

    total = db.scalar(select(func.count()).select_from(stmt.subquery()))

    stmt = (
        stmt.order_by(Content.external_popularity.desc())
        .offset((page - 1) * size)
        .limit(size)
    )
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