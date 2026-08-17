"""라우터 공용 의존성"""

from fastapi import Depends, HTTPException, Request
from sqlalchemy.orm import Session

from app.core.db import get_db
from app.core.security import decode_access_token
from app.domains.user.models import User

COOKIE_NAME = "access_token"


def unauthorized() -> HTTPException:
    return HTTPException(401, "not authorized")


def _user_from_cookie(request: Request, db: Session) -> User | None:
    """쿠키의 JWT 로 사용자 조회"""
    token = request.cookies.get(COOKIE_NAME)
    if not token:
        return None
    claims = decode_access_token(token)
    if not claims:
        return None

    user_id, version = claims
    user = db.get(User, user_id)
    # 비밀번호를 바꾸면 버전이 올라간다. 그 전에 발급된 토큰은 여기서 걸린다
    if not user or user.token_version != version:
        return None
    return user


def get_current_user(request: Request, db: Session = Depends(get_db)) -> User:
    """없거나 만료거나 무효화된 토큰이면 401"""
    user = _user_from_cookie(request, db)
    if not user:
        raise unauthorized()
    return user


def get_current_user_optional(request: Request, db: Session = Depends(get_db)) -> User | None:
    return _user_from_cookie(request, db)
