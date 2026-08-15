import enum
from datetime import datetime

from sqlalchemy import Boolean, ForeignKey, Index, String, func
from sqlalchemy import Enum as SAEnum
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.base import Base
from app.domains.content.models import Content

MEMO_MAX_LENGTH = 500


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
    # MovieLens 평점을 담는 가짜 계정
    is_seed: Mapped[bool] = mapped_column(Boolean, default=False)
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
    # 0.5 단위
    rating: Mapped[float | None]
    liked: Mapped[bool] = mapped_column(Boolean, default=False)  # 내 기호
    recommended: Mapped[bool] = mapped_column(Boolean, default=False)  # 남에게 권할 만함
    memo: Mapped[str | None] = mapped_column(String(MEMO_MAX_LENGTH))
    memo_public: Mapped[bool] = mapped_column(Boolean, default=False)  # 켜면 닉네임과 함께 공개
    created_at: Mapped[datetime] = mapped_column(server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(server_default=func.now(), onupdate=func.now())

    content: Mapped[Content] = relationship(lazy="joined")
    user: Mapped[User] = relationship(lazy="joined")

    __table_args__ = (
        Index("ix_user_contents_user_updated", "user_id", "updated_at"),  # 내 서재
        Index("ix_user_contents_rating", "user_id", "rating"),  # 개인화 추천 입력
        Index("ix_user_contents_liked", "user_id", "liked"),  # 개인화 추천 입력
        Index("ix_user_contents_recommended", "user_id", "recommended"),  # 커뮤니티 신호
        Index("ix_user_contents_public_memo", "content_id", "memo_public"),  # 상세의 공개 메모
    )
