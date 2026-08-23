from datetime import datetime
from typing import Annotated

from pydantic import AfterValidator, BaseModel, ConfigDict, EmailStr, Field

from app.core.sanitize import strip_tags
from app.core.security import MAX_PASSWORD_BYTES
from app.domains.content.schemas import ContentSummary
from app.domains.user.models import MEMO_MAX_LENGTH, ContentStatus


def _fits_bcrypt(value: str) -> str:
    """글자 수가 아니라 바이트로 체크"""
    if len(value.encode()) > MAX_PASSWORD_BYTES:
        raise ValueError(f"비밀번호가 {MAX_PASSWORD_BYTES}바이트를 넘음")
    return value


Password = Annotated[str, Field(min_length=8), AfterValidator(_fits_bcrypt)]

# 공개 메모로 남에게 나가는 필드는 태그를 걷어낸다
Public = Annotated[str, AfterValidator(strip_tags)]


def _clean_nickname(value: str) -> str:
    """태그를 걷어낸다. 태그만 있으면 빈값이 되므로 막는다"""
    cleaned = strip_tags(value).strip()
    if not cleaned:
        raise ValueError("닉네임에 표시할 수 있는 문자가 없음")
    return cleaned


Nickname = Annotated[str, Field(min_length=1, max_length=30), AfterValidator(_clean_nickname)]


class SignUpIn(BaseModel):
    email: EmailStr
    password: Password
    nickname: Nickname


class LoginIn(BaseModel):
    email: EmailStr
    password: str


class PasswordChangeIn(BaseModel):
    current_password: str
    new_password: Password


class WithdrawIn(BaseModel):
    """탈퇴는 되돌릴 수 없어 비밀번호로 한 번 더 확인"""

    password: str


class UserOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    email: EmailStr
    nickname: str
    created_at: datetime


class RecordIn(BaseModel):
    """보낸 필드만 바꿈"""

    status: ContentStatus | None = None
    rating: float | None = Field(None, ge=0.5, le=5, multiple_of=0.5)
    liked: bool | None = None
    recommended: bool | None = None
    memo: Public | None = Field(None, max_length=MEMO_MAX_LENGTH)
    memo_public: bool | None = None


class RecordOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    content_id: str
    status: ContentStatus
    rating: float | None
    liked: bool
    recommended: bool
    memo: str | None
    memo_public: bool
    updated_at: datetime


class LibraryItem(RecordOut):
    """내 서재 — 콘텐츠 정보를 추가"""

    content: ContentSummary
