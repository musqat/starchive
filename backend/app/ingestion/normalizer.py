"""외부 API 응답 → Content 생성용 dict."""

from datetime import date

from app.domains.content.ids import make_content_id
from app.domains.content.models import ContentType

POSTER_BASE = "https://image.tmdb.org/t/p/w500"


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
        "description": overview or None,  # "" 는 줄거리 없음으로 취급 → 임베딩 제외
        "source": "TMDB",
        "external_id": str(data["id"]),
        "release_date": date.fromisoformat(released) if released else None,
        "creator": None,  # 감독은 append_to_response=credits 가 필요.
        "image_url": f"{POSTER_BASE}{poster}" if poster else None,
        "external_rating": data.get("vote_average"),
        "external_rating_count": data.get("vote_count"),
        "content_metadata": {
            "runtime": data.get("runtime"),
            "original_title": data.get("original_title"),
            "tagline": data.get("tagline"),
            "backdrop_path": data.get("backdrop_path"),
        },
    }
