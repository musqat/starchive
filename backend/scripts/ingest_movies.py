import asyncio
from pathlib import Path

import httpx
from sqlalchemy import create_engine
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.orm import sessionmaker

from app.core.clients.tmdb import fetch_movie
from app.core.config import settings
from app.domains.content.models import Content
from app.ingestion.movielens import load_target_tmdb_ids
from app.ingestion.normalizer import normalize_movie

engine = create_engine(settings.DIRECT_URL)
Session = sessionmaker(bind=engine)

def upsert(session, row: dict) -> None:
    stmt = insert(Content).values(**row)
    stmt = stmt.on_conflict_do_update(
        index_elements=["id"],
        set_={k: stmt.excluded[k] for k in row if k != "id"},
    )
    session.execute(stmt)

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