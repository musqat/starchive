import logging
from datetime import UTC, datetime, timedelta

import httpx
from fastapi import APIRouter, Depends, Header, HTTPException, Query
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.db import get_db
from app.core.deps import get_current_user
from app.domains.content.models import ContentType
from app.domains.recommendation import pipeline, profile
from app.domains.recommendation.schemas import RecommendationList, RefreshResult
from app.domains.user.models import User

log = logging.getLogger(__name__)

router = APIRouter(tags=["recommendations"])


def _payload(db: Session, user: User, type_: ContentType) -> RecommendationList:
    rows = pipeline.current(db, user.id, type_)
    return RecommendationList(
        items=rows,
        generated_at=rows[0].generated_at if rows else None,
        rated_count=pipeline.rated_count(db, user.id, type_),
        required_count=pipeline.MIN_RATED,
        required_rating=profile.LIKED_RATING,
    )


@router.get(
    "/recommendations",
    response_model=RecommendationList,
    summary="추천 목록",
)
def list_recommendations(
    type: ContentType = Query(..., description="영화와 책을 따로 낸다"),
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return _payload(db, user, type)


@router.post(
    "/me/recommendations/refresh",
    response_model=RefreshResult,
    summary="추천 다시 만들기",
    responses={
        409: {"description": "평가한 작품이 부족함"},
        429: {"description": "쿨다운 중"},
    },
)
async def refresh_recommendations(
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """LLM 을 부르므로 쿨다운을 둔다. 매체 둘이 함께 바뀐다"""
    # 기록이 적으면 인기순보다 못한 결과가 나온다
    rated = pipeline.rated_count(db, user.id)
    if rated < pipeline.MIN_RATED:
        raise HTTPException(409, f"{pipeline.MIN_RATED - rated}편 더 평가해주세요")

    last = pipeline.generated_at(db, user.id)
    if last:
        cooldown = timedelta(minutes=settings.REC_COOLDOWN_MINUTES)
        # server_default=now() 로 들어온 값이라 시간대가 없다
        elapsed = datetime.now(UTC) - last.replace(tzinfo=UTC)
        if elapsed < cooldown:
            wait = int((cooldown - elapsed).total_seconds())
            # 주입받은 Response 에 넣으면 예외 응답에 안 실린다
            raise HTTPException(
                429,
                f"{wait // 60 + 1}분 뒤에 다시 시도해주세요",
                headers={"Retry-After": str(wait)},
            )

    async with httpx.AsyncClient(timeout=settings.LLM_TIMEOUT_SECONDS) as client:
        await pipeline.refresh(db, client, user.id)

    return RefreshResult(
        movie=_payload(db, user, ContentType.MOVIE),
        book=_payload(db, user, ContentType.BOOK),
    )


@router.get(
    "/recommendations/cron",
    summary="배치 갱신 (Cron 전용)",
    include_in_schema=False,
    responses={401: {"description": "CRON_SECRET 불일치"}},
)
async def run_cron(
    authorization: str = Header(""),
    db: Session = Depends(get_db),
):
    """오래된 배치를 상한까지 다시 만든다

    Hobby 는 함수 60초, Cron 하루 1회다. 사용자당 LLM 2회라 한 번에 CRON_USER_LIMIT 명뿐이다.
    사용자가 늘면 로컬 스크립트나 별도 워커로 옮긴다
    """
    if not settings.CRON_SECRET or authorization != f"Bearer {settings.CRON_SECRET}":
        raise HTTPException(401, "not authorized")

    older_than = datetime.now(UTC) - timedelta(hours=settings.CRON_STALE_HOURS)
    users = pipeline.stale_users(db, older_than, settings.CRON_USER_LIMIT)

    done: list[int] = []
    failed: list[int] = []
    async with httpx.AsyncClient(timeout=settings.LLM_TIMEOUT_SECONDS) as client:
        for user_id in users:
            try:
                await pipeline.refresh(db, client, user_id)
                done.append(user_id)
            except Exception:  # 한 명이 막혀도 나머지는 돌린다
                log.exception("배치 갱신 실패: user %s", user_id)
                db.rollback()
                failed.append(user_id)

    return {"targets": len(users), "done": len(done), "failed": failed}
