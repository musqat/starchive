from fastapi import FastAPI
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

app.include_router(content_router)
app.include_router(search_router)
app.include_router(auth_router)
app.include_router(records_router)
app.include_router(recommendation_router)


@app.get("/health")
def health():
    return {"status": "ok"}
