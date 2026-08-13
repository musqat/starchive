from datetime import datetime

from pydantic import BaseModel, ConfigDict, EmailStr, Field

from app.domains.content.schemas import ContentSummary
from app.domains.user.models import ContentStatus


class SignUpIn(BaseModel):
    email: EmailStr
    password: str = Field(min_length=8, max_length=72)
    nickname: str = Field(min_length=1, max_length=30)


class LoginIn(BaseModel):
    email: EmailStr
    password: str


class UserOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    email: EmailStr
    nickname: str
    created_at: datetime


class RecordIn(BaseModel):
    """status 또는 recommended 중 보낸 것만 바꿈"""

    status: ContentStatus | None = None
    recommended: bool | None = None


class RecordOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    content_id: str
    status: ContentStatus
    recommended: bool
    updated_at: datetime


class LibraryItem(RecordOut):
    """내 서재 — 콘텐츠 정보를 추가"""

    content: ContentSummary
