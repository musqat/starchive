"""외부 API 응답 → Content 생성용 dict"""

import html
from datetime import date

from app.domains.content.ids import make_content_id
from app.domains.content.models import ContentType

POSTER_BASE = "https://image.tmdb.org/t/p/w500"


def _text(raw: str | None) -> str | None:
    """HTML 이스케이프 해제. '&lt;채식주의자&gt;' → '<채식주의자>'"""
    return html.unescape(raw).strip() or None if raw else None


def _director(data: dict) -> str | None:
    """credits.crew 에서 감독만. 공동 연출은 쉼표로 연결"""
    crew = data.get("credits", {}).get("crew", [])
    return ", ".join(c["name"] for c in crew if c.get("job") == "Director") or None


def _author(raw: str | None) -> str | None:
    """알라딘 author 는 '세네카 (지은이), 하와이 대저택 (편역)' 형태. 지은이만 추출

    역할 표기가 없으면 전체를 그대로 사용
    """
    if not raw:
        return None
    names = [
        part.split("(")[0].strip()
        for part in raw.split(",")
        if "(지은이)" in part or "(글)" in part
    ]
    return ", ".join(names) or raw.strip()


CATEGORY_DEPTH = 2


def _categories(raw: str | None) -> list[str]:
    """'국내도서>소설/시/희곡>영미소설>영미소설 일반' → ['소설/시/희곡', '영미소설'].
    """
    if not raw:
        return []
    parts = [c.strip() for c in raw.split(">")[1:] if c.strip()]
    return parts[:CATEGORY_DEPTH]


def normalize_movie(data: dict) -> dict:
    """TMDB /movie/{id} 응답을 Content 컬럼명 dict 로 변환"""
    poster = data.get("poster_path")
    released = data.get("release_date")

    return {
        "id": make_content_id("TMDB", data["id"]),
        "type": ContentType.MOVIE,
        "title": _text(data["title"]),
        "genre": [g["name"] for g in data.get("genres", [])],
        "description": _text(data.get("overview")),  # "" 는 줄거리 없음으로 취급
        "source": "TMDB",
        "external_id": str(data["id"]),
        "release_date": date.fromisoformat(released) if released else None,
        "creator": _director(data),
        "image_url": f"{POSTER_BASE}{poster}" if poster else None,
        "external_rating": data.get("vote_average"),
        "external_popularity": data.get("vote_count"),
        "content_metadata": {
            "runtime": data.get("runtime"),
            "original_title": data.get("original_title"),
            "tagline": data.get("tagline"),
            "backdrop_path": data.get("backdrop_path"),
        },
    }

def normalize_book(data: dict) -> dict:
    """알라딘 ItemList/ItemLookUp 응답의 item 하나를 Content 컬럼명 dict 로 변환"""
    isbn13 = data["isbn13"]
    cover = data.get("cover")
    pub_date = data.get("pubDate")

    return {
        "id": make_content_id("ALADIN", isbn13),
        "type": ContentType.BOOK,
        "title": _text(data["title"]),
        "genre": _categories(data.get("categoryName")),
        "description": _text(data.get("description")),
        "source": "ALADIN",
        "external_id": isbn13,
        "release_date": date.fromisoformat(pub_date) if pub_date else None,
        "creator": _author(data.get("author")),
        # coversum 은 썸네일, cover500 은 같은 경로의 큰 이미지
        "image_url": cover.replace("/coversum/", "/cover500/") if cover else None,
        "external_rating": data.get("customerReviewRank"),
        "external_popularity": data.get("salesPoint"),
        "content_metadata": {
            "publisher": data.get("publisher"),
            "isbn13": isbn13,
            "itemId": data.get("itemId"),
            "priceStandard": data.get("priceStandard"),
            "categoryName": data.get("categoryName"),  # 원본, genre 재가공용
            "author": data.get("author"),  # 원본, 역자·엮은이 포함
            "bestRank": data.get("bestRank"),
        },
    }
