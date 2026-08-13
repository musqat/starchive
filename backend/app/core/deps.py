"""라우터 공용 의존성"""

from fastapi import Depends, HTTPException, Request
from sqlalchemy.orm import Session

from app.core.db import get_db
from app.core.security import decode_access_token
from app.domains.user.models import User

COOKIE_NAME = "access_token"


def unauthorized() -> HTTPException:
    return HTTPException(401, "not authorized")


def get_current_user(request: Request, db: Session = Depends(get_db)) -> User:
    """쿠키의 JWT 로 사용자 조회. 없거나 만료면 401"""
    token = request.cookies.get(COOKIE_NAME)
    if not token:
        raise unauthorized()
    user_id = decode_access_token(token)
    if not user_id:
        raise unauthorized()
    user = db.get(User, user_id)
    if not user:
        raise unauthorized()
    return user


def get_current_user_optional(request: Request, db: Session = Depends(get_db)) -> User | None:
    token = request.cookies.get(COOKIE_NAME)
    if not token:
        return None
    user_id = decode_access_token(token)
    if not user_id:
        return None
    return db.get(User, user_id)
