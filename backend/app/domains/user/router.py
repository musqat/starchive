from datetime import UTC, datetime, timedelta

from fastapi import APIRouter, Depends, HTTPException, Response
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.db import get_db
from app.core.deps import COOKIE_NAME, get_current_user
from app.core.security import create_access_token, hash_password, verify_password
from app.domains.user.models import User
from app.domains.user.schemas import (
    LoginIn,
    PasswordChangeIn,
    SignUpIn,
    UserOut,
    WithdrawIn,
)

router = APIRouter(prefix="/auth", tags=["auth"])


def set_auth_cookie(response: Response, user: User) -> None:
    """프론트가 /api 로 프록시해 같은 출처가 되므로 lax"""
    response.set_cookie(
        COOKIE_NAME,
        create_access_token(user.id, user.token_version),
        httponly=True,
        secure=settings.COOKIE_SECURE,
        samesite="lax",
        max_age=settings.ACCESS_TOKEN_EXPIRE_DAYS * 86400,
    )


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


@router.post(
    "/login",
    response_model=UserOut,
    responses={429: {"description": "실패가 쌓여 잠김"}},
)
def log_in(payload: LoginIn, response: Response, db: Session = Depends(get_db)):
    """성공 시 httpOnly 쿠키에 토큰. 실패는 이메일·비밀번호 구분 없이 401"""
    # 시드 유저는 조회 단계에서 막는다
    user = db.scalar(select(User).where(User.email == payload.email, User.is_seed.is_(False)))
    if not user:
        raise HTTPException(status_code=401, detail="invalid credentials")

    now = datetime.now(UTC)
    if user.locked_until and user.locked_until.replace(tzinfo=UTC) > now:
        wait = int((user.locked_until.replace(tzinfo=UTC) - now).total_seconds())
        raise HTTPException(
            429,
            f"{wait // 60 + 1}분 뒤에 다시 시도해주세요",
            headers={"Retry-After": str(wait)},
        )

    if not verify_password(payload.password, user.password_hash):
        user.failed_logins += 1
        if user.failed_logins >= settings.MAX_FAILED_LOGINS:
            user.locked_until = now + timedelta(minutes=settings.LOGIN_LOCK_MINUTES)
            user.failed_logins = 0
        db.commit()
        raise HTTPException(status_code=401, detail="invalid credentials")

    user.failed_logins = 0
    user.locked_until = None
    db.commit()

    set_auth_cookie(response, user)
    return user


@router.post("/logout", status_code=204)
def log_out(response: Response):
    response.delete_cookie(COOKIE_NAME)


@router.get("/me", response_model=UserOut)
def read_me(user: User = Depends(get_current_user)):
    return user


@router.patch("/password", status_code=204)
def change_password(
    payload: PasswordChangeIn,
    response: Response,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """현재 비밀번호가 틀리면 403. 다른 기기의 로그인은 모두 끊긴다"""
    if not verify_password(payload.current_password, user.password_hash):
        raise HTTPException(status_code=403, detail="wrong password")

    user.password_hash = hash_password(payload.new_password)
    # 유출된 토큰을 끊는 게 비밀번호를 바꾸는 이유다
    user.token_version += 1
    db.commit()

    set_auth_cookie(response, user)


# DELETE 는 본문을 떼는 프록시가 있어 POST 로 받는다
@router.post("/withdraw", status_code=204)
def withdraw(
    payload: WithdrawIn,
    response: Response,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """기록도 함께 지워진다 (user_contents 는 ON DELETE CASCADE)"""
    if not verify_password(payload.password, user.password_hash):
        raise HTTPException(status_code=403, detail="wrong password")

    db.delete(user)
    db.commit()
    response.delete_cookie(COOKIE_NAME)
