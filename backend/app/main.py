from fastapi import FastAPI

app = FastAPI(title="starchive")


@app.get("/health")
def health():
    return {"status": "ok"}
