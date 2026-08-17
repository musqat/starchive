"""재랭킹 전/후 비교. OpenAI 를 사용자 수만큼 호출한다

evaluate.py 와 같은 방식으로 가리고, 후보 30 을 두 가지로 줄 세워 잰다
  전 - 점수순 상위 10
  후 - 재랭킹 상위 10

    uv run python -m scripts.evaluate_rerank
    uv run python -m scripts.evaluate_rerank --users 20
"""

import asyncio
import random
import sys

import httpx
from sqlalchemy import delete, select
from sqlalchemy.orm import Session as SessionType

from app.domains.content.models import Content, ContentType
from app.domains.recommendation import candidates, pipeline, profile, reranker
from app.domains.user.models import UserContent
from app.ingestion.db import Session
from scripts.evaluate import SEED, K, ndcg, pick_users, recall, split

USERS = 50


async def compare(
    db: SessionType, client: httpx.AsyncClient, user_id: int, rng: random.Random
) -> tuple[float, ...] | None:
    """전 recall/ndcg, 후 recall/ndcg, LLM 이 쓴 비율"""
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
    held = split(liked, rng)
    truth = set(held)

    try:
        db.execute(
            delete(UserContent).where(
                UserContent.user_id == user_id, UserContent.content_id.in_(held)
            ),
            execution_options={"synchronize_session": False},
        )
        db.flush()

        found = candidates.generate(db, user_id, ContentType.MOVIE)
        if not found:
            return None
        titles = pipeline.liked_titles(db, user_id)
        items = pipeline.prompt_items(db, found)
    finally:
        db.rollback()

    before = [c.content_id for c in found[:K]]
    ranked = await reranker.rerank(client, titles, found, items)
    after = [r.candidate.content_id for r in ranked]
    from_llm = sum(1 for r in ranked if r.source is reranker.ReasonSource.LLM) / max(len(ranked), 1)

    return (
        recall(before, truth),
        ndcg(before, truth),
        recall(after, truth),
        ndcg(after, truth),
        from_llm,
    )


async def main() -> None:
    limit = USERS
    if "--users" in sys.argv:
        limit = int(sys.argv[sys.argv.index("--users") + 1])

    rng = random.Random(SEED)

    with Session() as db:
        users = pick_users(db, limit)
        print(f"대상 {len(users)}명 / OpenAI {len(users)}회 호출\n")

        rows = []
        async with httpx.AsyncClient(timeout=60) as client:
            for user_id in users:
                result = await compare(db, client, user_id, rng)
                if result:
                    rows.append(result)

    if not rows:
        print("평가할 유저가 없음")
        return

    n = len(rows)
    avg = [sum(col) / n for col in zip(*rows, strict=True)]

    print(f"{'':8} {'Recall@10':>11} {'NDCG@10':>10}")
    print(f"{'재랭킹 전':7} {avg[0]:>11.3f} {avg[1]:>10.3f}")
    print(f"{'재랭킹 후':7} {avg[2]:>11.3f} {avg[3]:>10.3f}")

    # 같은 유저를 두 번 잰 자료 비교
    print(f"\n{'':8} {'좋아짐':>7} {'나빠짐':>7} {'같음':>7}")
    for name, before, after in (("Recall", 0, 2), ("NDCG", 1, 3)):
        win = sum(1 for r in rows if r[after] > r[before])
        lose = sum(1 for r in rows if r[after] < r[before])
        print(f"{name:8} {win:>7} {lose:>7} {n - win - lose:>7}")

    print(f"\n유저 {n}명 / LLM 이 고른 비율 {avg[4]:.0%} / seed={SEED}")


if __name__ == "__main__":  # import 시 실행 방지
    asyncio.run(main())
