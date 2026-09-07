"""호출 제한. 공개 엔드포인트가 유료 API 를 부를 때 건다

로그인한 사용자는 계정으로, 익명은 IP 로 센다. 계정으로만 세면 익명 트래픽에 키가 없고
가입이 열려 있어 계정 수만큼 늘어난다. IP 로만 세면 같은 NAT 뒤 사람들이 한 버킷을 나눈다
"""

from fastapi import Request
from slowapi import Limiter

from app.core.deps import COOKIE_NAME
from app.core.security import decode_access_token


def client_ip(request: Request) -> str:
    """Vercel 뒤에서는 client.host 가 프록시다. X-Forwarded-For 첫 값이 실제 IP"""
    forwarded = request.headers.get("x-forwarded-for")
    if forwarded:
        return forwarded.split(",")[0].strip()
    return request.client.host if request.client else "unknown"


def user_or_ip(request: Request) -> str:
    """유효한 토큰이 있으면 user:<id>, 없으면 ip:<addr>. DB 는 안 본다"""
    token = request.cookies.get(COOKIE_NAME)
    if token:
        decoded = decode_access_token(token)
        if decoded:
            return f"user:{decoded[0]}"
    return f"ip:{client_ip(request)}"


# 메모리 저장소 — 서버리스는 인스턴스마다 따로 센다.
limiter = Limiter(key_func=user_or_ip)
