import asyncio

import httpx

from app.core.clients.aladin import fetch_bestsellers
from app.core.config import settings
from app.ingestion.db import Session, upsert
from app.ingestion.normalizer import normalize_book

PAGE_SIZE = 50
TOTAL = 20


async def fetch_page(client, sem, start: int) -> list[dict]:
    async with sem:
        return await fetch_bestsellers(client, start, PAGE_SIZE)


async def main():
    sem = asyncio.Semaphore(settings.MAX_CONCURRENCY)

    async with httpx.AsyncClient(timeout=10) as client:
        pages = await asyncio.gather(
            *[fetch_page(client, sem, p) for p in range(1, TOTAL + 1)],
            return_exceptions=True,
        )

    with Session() as session:
        for page in pages:
            if not isinstance(page, list):  # 예외는 건너뛴다
                continue
            for item in page:
                upsert(session, normalize_book(item))
        session.commit()


asyncio.run(main())