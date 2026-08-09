from fastapi import FastAPI

from app.domains.content.router import router as content_router

app = FastAPI(title="starchive")


@app.get("/health")
def health():
    return {"status": "ok"}

app.include_router(content_router)
