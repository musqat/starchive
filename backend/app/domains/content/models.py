import enum
from datetime import date, datetime

from pgvector.sqlalchemy import Vector
from sqlalchemy import Enum as SAEnum
from sqlalchemy import Index, String, Text, UniqueConstraint, func
from sqlalchemy.dialects.postgresql import ARRAY, JSONB
from sqlalchemy.orm import Mapped, mapped_column

from app.core.base import Base


class ContentType(enum.StrEnum):
    MOVIE = "MOVIE"
    BOOK = "BOOK"
    WEBTOON = "WEBTOON"


class Content(Base):
    __tablename__ = "contents"

    # 식별
    id: Mapped[str] = mapped_column(String(80), primary_key=True)  # PK. tmdb_12345 형식
    type: Mapped[ContentType] = mapped_column(SAEnum(ContentType, name="content_type"))  # 타입
    source: Mapped[str] = mapped_column(String(20))  # 출처. TMDB / ALADIN
    external_id: Mapped[str] = mapped_column(String(50))  # 소스 쪽 원본 ID

    # 표시
    title: Mapped[str] = mapped_column(String(500))  # 제목
    genre: Mapped[list[str] | None] = mapped_column(ARRAY(String))  # 장르
    description: Mapped[str | None] = mapped_column(Text)  # 줄거리 / 책소개
    release_date: Mapped[date | None]  # 개봉일 / 출간일
    creator: Mapped[str | None] = mapped_column(String(300))  # 감독 / 저자. 공동이면 쉼표 연결
    image_url: Mapped[str | None] = mapped_column(String(500))  # 포스터 / 표지
    content_metadata: Mapped[dict] = mapped_column(JSONB, default=dict)  # 타입별 표시 전용 필드

    # 평점
    external_rating: Mapped[float | None]  # 평점. 소스마다 척도가 달라 소스 간 비교 금지
    external_popularity: Mapped[int | None]  # 인기 지표. TMDB=평가 수, 알라딘=판매 지수

    # 임베딩
    embedding_text: Mapped[str | None] = mapped_column(Text)  # 임베딩에 넣은 정규화 텍스트
    embedding: Mapped[list[float] | None] = mapped_column(Vector(1536))  # description 없으면 NULL
    embedded_at: Mapped[datetime | None]  # 임베딩 시각. 

    created_at: Mapped[datetime] = mapped_column(server_default=func.now())  # 적재 시각

    __table_args__ = (
        UniqueConstraint("source", "external_id", name="uq_contents_source_external"),
        Index("ix_contents_type_title", "type", "title"),
        Index("ix_contents_genre_gin", "genre", postgresql_using="gin"),
    )
