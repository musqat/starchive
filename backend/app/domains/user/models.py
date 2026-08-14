import enum
from datetime import datetime

from sqlalchemy import Boolean, ForeignKey, Index, String, func
from sqlalchemy import Enum as SAEnum
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.base import Base
from app.domains.content.models import Content


class ContentStatus(enum.StrEnum):
    """컨텐츠 상태"""

    WISH = "WISH"  # 보고싶어요 / 읽고싶어요
    DOING = "DOING"  # 보는 중 / 읽는 중
    DONE = "DONE"  # 봤어요 / 읽었어요


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True)
    email: Mapped[str] = mapped_column(String(255), unique=True)
    password_hash: Mapped[str] = mapped_column(String(100))  # bcrypt 는 60자
    nickname: Mapped[str] = mapped_column(String(30))
    created_at: Mapped[datetime] = mapped_column(server_default=func.now())


class UserContent(Base):
    """사용자의 콘텐츠 기록"""

    __tablename__ = "user_contents"

    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), primary_key=True
    )
    content_id: Mapped[str] = mapped_column(
        ForeignKey("contents.id", ondelete="CASCADE"), primary_key=True
    )

    status: Mapped[ContentStatus] = mapped_column(SAEnum(ContentStatus, name="content_status"))
    rating: Mapped[int | None]  # 내 평점 1~5
    recommended: Mapped[bool] = mapped_column(Boolean, default=False)  # 추천
    created_at: Mapped[datetime] = mapped_column(server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(server_default=func.now(), onupdate=func.now())

    content: Mapped[Content] = relationship(lazy="joined")

    __table_args__ = (
        Index("ix_user_contents_user_updated", "user_id", "updated_at"),  # 내 서재
        Index("ix_user_contents_rating", "user_id", "rating"),  # 개인화 추천 입력
        Index("ix_user_contents_recommended", "user_id", "recommended"),  # 커뮤니티 신호
    )
