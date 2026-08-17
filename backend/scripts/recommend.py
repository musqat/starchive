"""추천 배치 — 사용자마다 후보를 뽑아 재랭킹하고 저장한다

시드 계정은 제외

    uv run python -m scripts.recommend            대상 수만
    uv run python -m scripts.recommend --apply    실행
    uv run python -m scripts.recommend --apply --users 5
"""

import asyncio
import sys

import httpx
from sqlalchemy import func, select

from app.domains.recommendation import pipeline
from app.domains.recommendation.models import ReasonSource, Recommendation
from app.domains.user.models import User
from app.ingestion.db import Session


def targets(db, limit: int | None) -> list[int]:
    stmt = select(User.id).where(User.is_seed.is_(False)).order_by(User.id)
    if limit:
        stmt = stmt.limit(limit)
    return list(db.scalars(stmt).all())


async def main() -> None:
    apply = "--apply" in sys.argv
    limit = None
    if "--users" in sys.argv:
        limit = int(sys.argv[sys.argv.index("--users") + 1])

    with Session() as db:
        users = targets(db, limit)
        print(f"대상 {len(users)}명")
        if not apply:
            print("--apply 를 붙이면 실행한다")
            return

        done = skipped = 0
        fallback = 0
        async with httpx.AsyncClient(timeout=60) as client:
            for user_id in users:
                batch_id = await pipeline.refresh(db, client, user_id)
                if batch_id is None:
                    skipped += 1  # 기록이 없어 후보가 안 나온 계정
                    continue
                done += 1
                templates = db.scalar(
                    select(func.count())
                    .select_from(Recommendation)
                    .where(
                        Recommendation.batch_id == batch_id,
                        Recommendation.reason_source == ReasonSource.TEMPLATE,
                    )
                )
                if templates:
                    fallback += 1

    print(f"생성 {done}명 / 건너뜀 {skipped}명 / 폴백 섞인 배치 {fallback}건")


if __name__ == "__main__":  # import 시 실행 방지
    asyncio.run(main())
