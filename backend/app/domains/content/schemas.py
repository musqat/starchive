from datetime import date

from pydantic import BaseModel, ConfigDict

from app.domains.content.models import ContentType

_SUMMARY_EXAMPLE = {
    "id": "tmdb_278",
    "type": "MOVIE",
    "title": "쇼생크 탈출",
    "genre": ["드라마", "범죄"],
    "image_url": "https://image.tmdb.org/t/p/w500/qV9BQZdiM8foEzDz0Ag5hGWE5qM.jpg",
    "external_rating": 8.727,
}


class ContentSummary(BaseModel):
    """목록 응답"""

    model_config = ConfigDict(
        from_attributes=True,
        json_schema_extra={"example": _SUMMARY_EXAMPLE},
    )

    id: str
    type: ContentType
    title: str
    genre: list[str] | None
    image_url: str | None
    external_rating: float | None


class ContentDetail(ContentSummary):
    """상세 응답"""

    model_config = ConfigDict(
        from_attributes=True,
        json_schema_extra={
            "example": {
                **_SUMMARY_EXAMPLE,
                "description": "은행 간부 앤디는 살인 누명을 쓰고 쇼생크에 수감된다...",
                "release_date": "1994-09-23",
                "creator": None,
                "external_popularity": 30965,
                "content_metadata": {
                    "runtime": 142,
                    "original_title": "The Shawshank Redemption",
                },
            }
        },
    )

    description: str | None
    release_date: date | None
    creator: str | None
    external_popularity: int | None
    content_metadata: dict


class ContentPage(BaseModel):
    """목록 응답, 총 개수와 현재 위치 반환"""

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "items": [_SUMMARY_EXAMPLE],
                "total": 2988,
                "page": 1,
                "size": 20,
            }
        }
    )

    items: list[ContentSummary]
    total: int
    page: int
    size: int
