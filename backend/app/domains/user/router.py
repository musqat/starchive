from fastapi import APIRouter, Depends, HTTPException, Response
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.db import get_db
from app.core.deps import COOKIE_NAME, get_current_user
from app.core.security import create_access_token, hash_password, verify_password
from app.domains.user.models import User
from app.domains.user.schemas import LoginIn, SignUpIn, UserOut

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/signup", response_model=UserOut, status_code=201)
def sign_up(payload: SignUpIn, db: Session = Depends(get_db)):
    """이메일 중복이면 409"""
    existing_user = db.scalar(select(User).where(User.email == payload.email))
    
    if existing_user:
        raise HTTPException(status_code=409, detail="Email already registered")
    user = User(
        email=payload.email,
        password_hash=hash_password(payload.password),
        nickname=payload.nickname,
    )

    db.add(user)
    db.commit()
    db.refresh(user)
    return user


@router.post("/login", response_model=UserOut)
def log_in(payload: LoginIn, response: Response, db: Session = Depends(get_db)):
    """성공 시 httpOnly 쿠키에 토큰. 실패는 이메일·비밀번호 구분 없이 401"""
    user = db.scalar(select(User).where(User.email == payload.email))
    if not user or not verify_password(payload.password, user.password_hash):
        raise HTTPException(status_code=401, detail="invalid credentials")
    
    response.set_cookie(
        COOKIE_NAME,
        create_access_token(user.id),
        httponly=True,
        secure=settings.COOKIE_SECURE,
        samesite="none" if settings.COOKIE_SECURE else "lax",
        max_age=settings.ACCESS_TOKEN_EXPIRE_DAYS * 86400,
    )

    return user

@router.post("/logout", status_code=204)
def log_out(response: Response):
    response.delete_cookie(COOKIE_NAME)

@router.get("/me", response_model=UserOut)
def read_me(user: User = Depends(get_current_user)):
    return user
