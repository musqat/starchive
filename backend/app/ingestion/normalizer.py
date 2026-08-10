"""외부 API 응답 → Content 생성용 dict."""

from datetime import date

from app.domains.content.ids import make_content_id
from app.domains.content.models import ContentType

POSTER_BASE = "https://image.tmdb.org/t/p/w500"


def _director(data: dict) -> str | None:
    """credits.crew 에서 감독만 추출, 공동 연출이면 쉼표로 구분"""
    crew = data.get("credits", {}).get("crew", [])
    return ", ".join(c["name"] for c in crew if c.get("job") == "Director") or None


def _author(raw: str | None) -> str | None:
    """알라딘 author 는 '세네카 (지은이), 하와이 대저택 (편역)' 형태. 지은이만 남긴다.

    역할 표기가 아예 없으면 (단독 저자) 전체를 그대로 쓴다.
    """
    if not raw:
        return None
    names = [
        part.split("(")[0].strip()
        for part in raw.split(",")
        if "(지은이)" in part or "(글)" in part
    ]
    return ", ".join(names) or raw.strip()


def _categories(raw: str | None) -> list[str]:
    """
    국내도서>인문학>서양철학' → ['인문학', '서양철학']
    """
    if not raw:
        return []
    return [c.strip() for c in raw.split(">")[1:] if c.strip()]


def normalize_movie(data: dict) -> dict:
    """TMDB /movie/{id} 응답을 Content 컬럼명 dict 로 변환."""
    poster = data.get("poster_path")
    released = data.get("release_date")
    overview = data.get("overview")

    return {
        "id": make_content_id("TMDB", data["id"]),
        "type": ContentType.MOVIE,
        "title": data["title"],
        "genre": [g["name"] for g in data.get("genres", [])],
        "description": overview or None,  # "" 는 줄거리 없음으로 취급
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
    """알라딘 ItemList/ItemLookUp 응답의 item 하나를 Content 컬럼명 dict 로 변환."""
    isbn13 = data["isbn13"]
    cover = data.get("cover")
    pub_date = data.get("pubDate")
    description = data.get("description")

    return {
        "id": make_content_id("ALADIN", isbn13),
        "type": ContentType.BOOK,
        "title": data["title"],
        "genre": _categories(data.get("categoryName")),
        "description": description or None,
        "source": "ALADIN",
        "external_id": isbn13,
        "release_date": date.fromisoformat(pub_date) if pub_date else None,
        "creator": _author(data.get("author")),
        # coversum 은 썸네일. cover500 은 경로의 큰 이미지다
        "image_url": cover.replace("/coversum/", "/cover500/") if cover else None,
        "external_rating": data.get("customerReviewRank"),
        "external_popularity": data.get("salesPoint"),
        "content_metadata": {
            "publisher": data.get("publisher"),
            "isbn13": isbn13,
            "itemId": data.get("itemId"),
            "priceStandard": data.get("priceStandard"),
            "categoryName": data.get("categoryName"),  # 원본. genre 재가공용
            "author": data.get("author"),  # 원본. 역자·엮은이까지 포함
            "bestRank": data.get("bestRank"),
        },
    }
