import httpx
import pytest

from app.core.clients.tmdb import fetch_movie
from app.ingestion.movielens import load_target_tmdb_ids
from app.ingestion.normalizer import normalize_movie
from pathlib import Path


def test_load_ids():
    ids = load_target_tmdb_ids(Path("data/ml-latest-small"))
    assert len(ids) == 3000
    assert isinstance(ids[0], int)


@pytest.mark.external
async def test_fetch_and_normalize():
    ids = load_target_tmdb_ids(Path("data/ml-latest-small"))[:5]

    async with httpx.AsyncClient(timeout=10) as client:
        for tmdb_id in ids:
            raw = await fetch_movie(client, tmdb_id)
            row = normalize_movie(raw)

            assert row["id"] == f"tmdb_{tmdb_id}"
            assert row["title"]
            assert row["source"] == "TMDB"
            assert row["type"].value == "MOVIE"
            assert isinstance(row["genre"], list)

@pytest.mark.db
def test_contents_saved():
    from sqlalchemy import create_engine, text
    from app.core.config import settings

    with create_engine(settings.DIRECT_URL).connect() as conn:
        count = conn.execute(text("select count(*) from contents")).scalar()

    assert count > 2900
