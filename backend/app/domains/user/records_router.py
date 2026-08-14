from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.db import get_db
from app.core.deps import get_current_user
from app.domains.content.models import Content, ContentType
from app.domains.user.models import ContentStatus, User, UserContent
from app.domains.user.schemas import LibraryItem, RecordIn, RecordOut

router = APIRouter(prefix="/me", tags=["records"])


@router.get("/library", response_model=list[LibraryItem])
def list_library(
    status: ContentStatus | None = Query(None),
    type: ContentType | None = Query(None),
    page: int = Query(1, ge=1),
    size: int = Query(20, ge=1, le=100),
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    stmt = select(UserContent).where(UserContent.user_id == user.id)
    if status:
        stmt = stmt.where(UserContent.status == status)
    if type:
        stmt = stmt.join(Content).where(Content.type == type)
    stmt = stmt.order_by(UserContent.updated_at.desc()).offset((page - 1) * size).limit(size)

    records = db.scalars(stmt).unique().all()
    # 카드가 체크 상태를 그리려면 content 안에도 같은 값이 있어야 한다
    for record in records:
        record.content.my_status = record.status
        record.content.my_rating = record.rating
        record.content.my_recommended = record.recommended
    return records

@router.put("/records/{content_id}", response_model=RecordOut)
def upsert_record(
    content_id: str,
    payload: RecordIn,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """rating 이나 recommended 가 있으면 status 도 DONE 으로 변경"""

    if not db.get(Content, content_id):
        raise HTTPException(status_code=404, detail="Content not found")
    
    record = db.get(UserContent, (user.id, content_id))

    if not record:
        record = UserContent(user_id=user.id, content_id=content_id, status=ContentStatus.WISH)
        db.add(record)
    if payload.status is not None:
        record.status = payload.status
    if payload.recommended is not None:
        record.recommended = payload.recommended
    # rating 은 null 을 보내 지울 수 있어야 하므로 전송 여부로 판단한다
    if "rating" in payload.model_fields_set:
        record.rating = payload.rating
    if record.rating or record.recommended:
        record.status = ContentStatus.DONE
    db.commit()
    db.refresh(record)
    return record


@router.delete("/records/{content_id}", status_code=204)
def delete_record(
    content_id: str,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    record = db.get(UserContent, (user.id, content_id))
    if record:
        db.delete(record)
        db.commit()
