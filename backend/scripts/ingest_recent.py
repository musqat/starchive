"""신작 수집 — MovieLens 가 끝나는 2018년 이후

목록은 TMDB discover 로 만들고 상세는 기존 fetch_movie 로 받는다.
id 충돌 시 갱신하므로 여러 번 돌려도 된다

    uv run python -m scripts.ingest_recent            # 대상 수만
    uv run python -m scripts.ingest_recent --apply    # 새로 나온 것만
    uv run python -m scripts.ingest_recent --apply --pages 5
    uv run python -m scripts.ingest_recent --apply --refresh  # 있는 것도 다시 받는다
"""

import asyncio
import sys

import httpx
from sqlalchemy import select

from app.core.clients.tmdb import DISCOVER_SINCE, MIN_VOTE_COUNT, discover_movie_ids, fetch_movie
from app.core.config import settings
from app.domains.content.ids import make_content_id
from app.domains.content.models import Content
from app.ingestion.db import Session, upsert
from app.ingestion.normalizer import normalize_movie


async def collect_ids(client: httpx.AsyncClient, max_pages: int | None) -> list[int]:
    """discover 를 훑어 tmdb id 를 모은다"""
    first, pages = await discover_movie_ids(client, 1)
    if max_pages:
        pages = min(pages, max_pages)

    sem = asyncio.Semaphore(settings.MAX_CONCURRENCY)

    async def one(page: int) -> list[int]:
        async with sem:
            ids, _ = await discover_movie_ids(client, page)
            return ids

    rest = await asyncio.gather(*[one(p) for p in range(2, pages + 1)], return_exceptions=True)
    ids = list(first)
    for chunk in rest:
        if isinstance(chunk, list):
            ids += chunk
    return list(dict.fromkeys(ids))  # 순서 유지 중복 제거


def unseen(ids: list[int]) -> list[int]:
    """DB 에 있는 영화는 새로 수집하지 않는다

    discover 목록은 매번 갱신된다. 전부 다시 받으면 실행 시간만 길어진다
    """
    wanted = {make_content_id("TMDB", str(i)): i for i in ids}
    with Session() as session:
        known = set(session.scalars(select(Content.id).where(Content.id.in_(wanted))))
    return [tmdb_id for cid, tmdb_id in wanted.items() if cid not in known]


async def main() -> None:
    apply = "--apply" in sys.argv
    max_pages = None
    if "--pages" in sys.argv:
        max_pages = int(sys.argv[sys.argv.index("--pages") + 1])

    async with httpx.AsyncClient(timeout=15) as client:
        ids = await collect_ids(client, max_pages)
        # 저장 항목을 추가하면 DB 에 있는 영화도 다시 수집해야 한다
        fresh = ids if "--refresh" in sys.argv else unseen(ids)
        print(f"{DISCOVER_SINCE} 이후 {MIN_VOTE_COUNT}표 이상 {len(ids):,}편")
        print(f"이미 있음 {len(ids) - len(fresh):,}편 / 받을 것 {len(fresh):,}편")

        if not apply:
            print("--apply 를 붙이면 실행한다")
            return

        sem = asyncio.Semaphore(settings.MAX_CONCURRENCY)

        async def one(tmdb_id: int) -> dict | None:
            async with sem:
                return await fetch_movie(client, tmdb_id)

        raws = await asyncio.gather(*[one(i) for i in fresh], return_exceptions=True)

    saved = skipped = 0
    with Session() as session:
        for raw in raws:
            if not isinstance(raw, dict):  # 404 와 예외
                skipped += 1
                continue
            upsert(session, normalize_movie(raw))
            saved += 1
        session.commit()

    print(f"저장 {saved:,}편 / 건너뜀 {skipped:,}편")


if __name__ == "__main__":  # import 시 실행 방지
    asyncio.run(main())
