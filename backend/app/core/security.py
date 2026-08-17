"""비밀번호 해시와 JWT

bcrypt, jwt(pyjwt) 사용. 설정은 settings.JWT_SECRET / JWT_ALGORITHM /
ACCESS_TOKEN_EXPIRE_DAYS
"""

from datetime import UTC, datetime, timedelta

import bcrypt
import jwt

from app.core.config import settings

MAX_PASSWORD_BYTES = 72  # bcrypt 최대


def hash_password(raw: str) -> str:
    return bcrypt.hashpw(raw.encode(), bcrypt.gensalt()).decode()


def verify_password(raw: str, hashed: str) -> bool:
    try:
        return bcrypt.checkpw(raw.encode(), hashed.encode())
    except ValueError:  # 한계를 넘은 입력
        return False


def create_access_token(user_id: int, token_version: int = 0) -> str:
    """토큰 생성. 버전이 올라가면 이전 토큰은 못 쓴다"""
    exp = datetime.now(UTC) + timedelta(days=settings.ACCESS_TOKEN_EXPIRE_DAYS)
    payload = {"sub": str(user_id), "ver": token_version, "exp": exp}
    return jwt.encode(payload, settings.JWT_SECRET, algorithm=settings.JWT_ALGORITHM)


def decode_access_token(token: str) -> tuple[int, int] | None:
    """(사용자 id, 토큰 버전). 서명이나 만료가 어긋나면 None"""
    try:
        payload = jwt.decode(token, settings.JWT_SECRET, algorithms=[settings.JWT_ALGORITHM])
        return int(payload["sub"]), int(payload.get("ver", 0))
    except (jwt.InvalidTokenError, KeyError, TypeError, ValueError):
        return None
