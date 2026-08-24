from pathlib import Path

import pytest

from app.ingestion.movielens import load_target_tmdb_ids

DATA_DIR = Path("data/ml-latest-small")

# 내려받는 데이터라 저장소에 없다. 있을 때만 돈다
pytestmark = pytest.mark.skipif(
    not (DATA_DIR / "ratings.csv").exists(),
    reason="MovieLens 데이터 없음 — scripts.ingest_seed 참고",
)


def test_load_ids():
    ids = load_target_tmdb_ids(DATA_DIR)

    assert len(ids) == 3000
    assert isinstance(ids[0], int)
    assert len(set(ids)) == len(ids), "tmdbId 중복"
