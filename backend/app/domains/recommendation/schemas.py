from datetime import datetime

from pydantic import BaseModel, ConfigDict

from app.domains.content.schemas import ContentSummary
from app.domains.recommendation.models import ReasonSource


class RecommendationItem(BaseModel):
    """추천 한 줄"""

    model_config = ConfigDict(from_attributes=True)

    rank: int
    reason: str | None
    reason_source: ReasonSource
    content: ContentSummary


class RecommendationList(BaseModel):
    """매체별 추천. 비어 있으면 기록이 부족한 것"""

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "items": [
                    {
                        "rank": 1,
                        "reason": "'인터스텔라'의 우주 탐사와 생존의 긴장감을 공유합니다",
                        "reason_source": "LLM",
                        "content": {"id": "tmdb_49047", "title": "그래비티"},
                    }
                ],
                "generated_at": "2026-08-18T01:20:00",
                "rated_count": 9,
                "required_count": 5,
                "required_rating": 4.0,
            }
        }
    )

    items: list[RecommendationItem]
    generated_at: datetime | None
    # 화면이 "★4 이상 몇 편 더" 를 그리는 데 쓴다
    rated_count: int
    required_count: int
    required_rating: float


class RefreshResult(BaseModel):
    """다시 만들면 두 매체가 함께 바뀌므로 같이 돌려준다"""

    movie: RecommendationList
    book: RecommendationList
