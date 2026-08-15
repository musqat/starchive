import httpx
import pytest

from app.core.clients.aladin import fetch_bestsellers
from app.ingestion.normalizer import is_excluded_book, normalize_book


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
        assert "국내도서" not in row["genre"]  # 첫 칸(SearchTarget)은 제외
        assert "(" not in (row["creator"] or "")  # (지은이) 같은 역할 표기 제거


@pytest.mark.external
async def test_bestseller_start_is_page_number():
    """start 는 오프셋이 아니라 페이지 번호. 1 과 2 는 겹치지 않아야 함"""
    async with httpx.AsyncClient(timeout=30) as client:
        page1 = await fetch_bestsellers(client, start=1, max_results=50)
        page2 = await fetch_bestsellers(client, start=2, max_results=50)

    assert not {i["isbn13"] for i in page1} & {i["isbn13"] for i in page2}


def test_excluded_categories():
    """제외 목록에 있는 책들을 필터링"""
    assert is_excluded_book("국내도서>외국어>토익>Reading")
    assert is_excluded_book("국내도서>수험서/자격증>공무원 수험서>국어")
    assert is_excluded_book("국내도서>컴퓨터/모바일>활용능력>컴퓨터활용능력")

    assert not is_excluded_book("국내도서>소설/시/희곡>영미소설")
    assert not is_excluded_book("국내도서>어린이>동화/명작/고전")
    assert not is_excluded_book(None)  # 분류가 없으면 판단하지 않는다
