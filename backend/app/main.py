from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import settings
from app.domains.content.router import router as content_router
from app.domains.content.search_router import router as search_router
from app.domains.recommendation.router import router as recommendation_router
from app.domains.user.records_router import router as records_router
from app.domains.user.router import router as auth_router

app = FastAPI(title="starchive")

app.add_middleware(
    CORSMiddleware,
    allow_origins=[settings.FRONTEND_ORIGIN],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# JSON API 라 대부분의 표면이 없지만, 표준 방어 헤더는 붙여 둔다.
# CSP 는 frame-ancestors 만 — default-src 를 걸면 /docs(Swagger) 가 깨진다
SECURITY_HEADERS = {
    "X-Content-Type-Options": "nosniff",
    "X-Frame-Options": "DENY",
    "Content-Security-Policy": "frame-ancestors 'none'",
    "Referrer-Policy": "no-referrer",
}


@app.middleware("http")
async def security_headers(request: Request, call_next):
    response = await call_next(request)
    for key, value in SECURITY_HEADERS.items():
        response.headers.setdefault(key, value)
    return response

app.include_router(content_router)
app.include_router(search_router)
app.include_router(auth_router)
app.include_router(records_router)
app.include_router(recommendation_router)


@app.get("/health")
def health():
    return {"status": "ok"}
