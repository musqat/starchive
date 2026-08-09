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

    id: Mapped[str] = mapped_column(String(80), primary_key=True)  # tmdb_12345 형식 슬러그
    type: Mapped[ContentType] = mapped_column(SAEnum(ContentType, name="content_type"))
    title: Mapped[str] = mapped_column(String(500))
    genre: Mapped[list[str] | None] = mapped_column(ARRAY(String))  # text[]. GIN 인덱스
    description: Mapped[str | None] = mapped_column(Text)  # 줄거리 / 책소개. 임베딩 재료
    source: Mapped[str] = mapped_column(String(20))  # TMDB / ALADIN
    external_id: Mapped[str] = mapped_column(String(50))  # 소스 쪽 원본 ID
    release_date: Mapped[date | None]  # 개봉일 / 출간일
    creator: Mapped[str | None] = mapped_column(String(300))  # 감독 / 저자
    image_url: Mapped[str | None] = mapped_column(String(500))  # 포스터 / 표지
    external_rating: Mapped[float | None]  # TMDB·알라딘 평점
    external_rating_count: Mapped[int | None]  # 평가 수. 인기순 폴백 정렬 기준
    content_metadata: Mapped[dict] = mapped_column(JSONB, default=dict)  # 표시 전용 타입별 필드
    embedding_text: Mapped[str | None] = mapped_column(Text)  # 임베딩에 넣은 정규화 텍스트
    embedding: Mapped[list[float] | None] = mapped_column(Vector(1536))  # description 없으면 NULL
    embedded_at: Mapped[datetime | None]  # 모델 교체 시 재생성 대상 판별
    created_at: Mapped[datetime] = mapped_column(server_default=func.now())

    __table_args__ = (
        UniqueConstraint("source", "external_id", name="uq_contents_source_external"),
        Index("ix_contents_type_title", "type", "title"),
        Index("ix_contents_genre_gin", "genre", postgresql_using="gin"),
        # HNSW 는 무료 티어 RAM 에서 빌드 실패. 느려지면 IVFFlat 부터 (design.md §4)
    )
