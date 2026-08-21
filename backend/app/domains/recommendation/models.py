import enum
import uuid
from datetime import datetime

from sqlalchemy import Enum as SAEnum
from sqlalchemy import ForeignKey, Index, SmallInteger, String, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.base import Base
from app.domains.content.models import Content, ContentType

REASON_MAX_LENGTH = 300


class ReasonSource(enum.StrEnum):
    """LLM이 작성하고 실패시 TEMPLATE"""

    LLM = "LLM"
    TEMPLATE = "TEMPLATE"  # LLM 실패
    RECENT = "RECENT"  # 신작 자리. 실패가 아니라 정상 경로다


class Recommendation(Base):
    """만들어둔 추천 내용, 조회는 캐시만 읽는다"""

    __tablename__ = "recommendations"

    # 한 배치에 같은 작품이 두 번 들어갈 수 없다
    batch_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True)
    content_id: Mapped[str] = mapped_column(
        ForeignKey("contents.id", ondelete="CASCADE"), primary_key=True
    )

    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"))
    type: Mapped[ContentType] = mapped_column(SAEnum(ContentType, name="content_type"))
    rank: Mapped[int] = mapped_column(SmallInteger)  # 매체마다 1 부터

    score: Mapped[float]  # 재랭킹 전 후보 점수. 순서가 얼마나 바뀌었는지 되짚는 값
    reason: Mapped[str | None] = mapped_column(String(REASON_MAX_LENGTH))
    reason_source: Mapped[ReasonSource] = mapped_column(SAEnum(ReasonSource, name="reason_source"))
    generated_at: Mapped[datetime] = mapped_column(server_default=func.now())

    content: Mapped[Content] = relationship(lazy="joined")

    # 화면이 읽는 경로 — 배치와 매체를 지정해 순위대로
    __table_args__ = (Index("ix_recommendations_batch_type_rank", "batch_id", "type", "rank"),)
