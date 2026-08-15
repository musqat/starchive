from pathlib import Path

import httpx
import pytest

from app.core.clients.tmdb import fetch_movie
from app.ingestion.movielens import load_target_tmdb_ids
from app.ingestion.normalizer import _providers, normalize_movie


@pytest.mark.external
async def test_fetch_movie():
    async with httpx.AsyncClient(timeout=10) as client:
        data = await fetch_movie(client, 123)

    assert data is not None
    assert data["title"]
    assert data["overview"]


@pytest.mark.external
async def test_normalize():
    async with httpx.AsyncClient(timeout=10) as client:
        raw = await fetch_movie(client, 278)

    row = normalize_movie(raw)

    assert row["id"] == "tmdb_278"
    assert row["type"].value == "MOVIE"
    assert row["source"] == "TMDB"
    assert row["external_id"] == "278"
    assert row["genre"]
    assert row["image_url"].startswith("https://")
    assert row["creator"], "append_to_response=credits 누락"


@pytest.mark.external
async def test_overview_coverage():
    """한국어 줄거리가 없는 비율. 임베딩 대상이 얼마나 줄어드는지"""
    ids = load_target_tmdb_ids(Path("data/ml-latest-small"))[::100]  # 30개 표본

    missing = 0
    async with httpx.AsyncClient(timeout=10) as client:
        for tid in ids:
            data = await fetch_movie(client, tid)
            if data is None:
                continue
            if not data["overview"]:
                missing += 1

    assert missing / len(ids) < 0.15, f"줄거리 없는 비율 15% 초과: {missing}/{len(ids)}"


def test_providers_prefers_flatrate():
    """구독이 대여·구매보다 앞에 오고, 같은 서비스는 한 번만"""
    raw = {
        "watch/providers": {
            "results": {
                "KR": {
                    "link": "https://example.com/watch",
                    "rent": [
                        {"provider_id": 3, "provider_name": "Google Play", "logo_path": "/g.jpg"}
                    ],
                    "flatrate": [
                        {"provider_id": 1, "provider_name": "wavve", "logo_path": "/w.jpg"}
                    ],
                    "buy": [
                        {"provider_id": 3, "provider_name": "Google Play", "logo_path": "/g.jpg"}
                    ],
                }
            }
        }
    }

    result = _providers(raw)

    assert [p["name"] for p in result["items"]] == ["wavve", "Google Play"]
    assert result["items"][1]["kind"] == "rent"  # 먼저 만난 종류를 쓴다
    assert result["link"] == "https://example.com/watch"


def test_providers_absent_region():
    """한국에서 볼 수 없으면 None"""
    assert _providers({"watch/providers": {"results": {"US": {"link": "x"}}}}) is None
    assert _providers({}) is None
