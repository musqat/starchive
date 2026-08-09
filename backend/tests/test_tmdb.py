import httpx
import pytest

from app.core.clients.tmdb import fetch_movie
from app.ingestion.normalizer import normalize_movie


### TMDB 개별 ID 호출 테스트
@pytest.mark.external
@pytest.mark.asyncio
async def test_fetch_movie():
    async with httpx.AsyncClient(timeout=10) as client:
        data = await fetch_movie(client, 123)

    assert data is not None
    assert data["title"]
    assert data["overview"]

### TMDB 여러 ID 호출 테스트
@pytest.mark.external
async def test_overview_missing():
    async with httpx.AsyncClient(timeout=10) as client:
        for tid in [278, 680, 155, 13, 4995]:
            data = await fetch_movie(client, tid)
            print(tid, data["title"], "overview:", len(data["overview"]))

### TMDB 다수 ID 호출 테스트 (한국 개봉인지 아닌지 확인)
@pytest.mark.external
async def test_overview_coverage():
    from pathlib import Path

    from app.ingestion.movielens import load_target_tmdb_ids

    ids = load_target_tmdb_ids(Path("data/ml-latest-small"))
    sample = ids[::100]          # 100개 간격으로 30개

    missing = 0
    async with httpx.AsyncClient(timeout=10) as client:
        for tid in sample:
            data = await fetch_movie(client, tid)
            if data is None:
                print(tid, "404")
                continue
            if not data["overview"]:
                missing += 1
                print(tid, data["title"], "← 줄거리 없음")

    print(f"\n{missing}/{len(sample)} 비어 있음")

@pytest.mark.external
async def test_normalize():
    async with httpx.AsyncClient(timeout=10) as client:
        raw = await fetch_movie(client, 278)
    row = normalize_movie(raw)
    print(row)
    assert row["id"] == "tmdb_278"
    assert row["genre"]
    assert row["image_url"].startswith("https://")