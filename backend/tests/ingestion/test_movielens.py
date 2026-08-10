from pathlib import Path

from app.ingestion.movielens import load_target_tmdb_ids

DATA_DIR = Path("data/ml-latest-small")


def test_load_ids():
    ids = load_target_tmdb_ids(DATA_DIR)

    assert len(ids) == 3000
    assert isinstance(ids[0], int)
    assert len(set(ids)) == len(ids), "tmdbId 중복"
