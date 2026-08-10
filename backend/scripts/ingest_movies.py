import asyncio
from pathlib import Path

import httpx

from app.core.clients.tmdb import fetch_movie
from app.core.config import settings
from app.ingestion.db import Session, upsert
from app.ingestion.movielens import load_target_tmdb_ids
from app.ingestion.normalizer import normalize_movie


async def fetch_one(client, sem, tmdb_id):
    async with sem:
        return await fetch_movie(client, tmdb_id)

async def main():
    ids = load_target_tmdb_ids(Path("data/ml-latest-small"))

    sem = asyncio.Semaphore(settings.MAX_CONCURRENCY)

    async with httpx.AsyncClient(timeout=10) as client:
        raws = await asyncio.gather(
            *[fetch_one(client, sem, i) for i in ids],
            return_exceptions=True,
        )

    with Session() as session:
        for raw in raws:
            if raw is None:          # 404
                continue
            upsert(session, normalize_movie(raw))
        session.commit()


asyncio.run(main())