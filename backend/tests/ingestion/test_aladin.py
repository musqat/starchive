import httpx
import pytest

from app.core.clients.aladin import fetch_bestsellers
from app.ingestion.normalizer import normalize_book


@pytest.mark.external
async def test_fetch_and_normalize_book():
    async with httpx.AsyncClient(timeout=30) as client:
        items = await fetch_bestsellers(client, start=1, max_results=3)

    assert len(items) == 3

    for item in items:
        row = normalize_book(item)

        assert row["id"].startswith("aladin_")
        assert row["type"].value == "BOOK"
        assert row["source"] == "ALADIN"
        assert row["title"]
        assert row["genre"], "categoryName 파싱 실패"
        assert "국내도서" not in row["genre"]  # 첫 칸(SearchTarget)은 버린다
        assert "(" not in (row["creator"] or "")  # (지은이) 같은 역할 표기 제거


@pytest.mark.external
async def test_bestseller_start_is_page_number():
    """start 는 페이지 번호, 1,2 겹치지않는지 테스트 """
    async with httpx.AsyncClient(timeout=30) as client:
        page1 = await fetch_bestsellers(client, start=1, max_results=50)
        page2 = await fetch_bestsellers(client, start=2, max_results=50)

    assert not {i["isbn13"] for i in page1} & {i["isbn13"] for i in page2}
