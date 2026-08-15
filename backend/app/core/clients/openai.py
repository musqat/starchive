import httpx
from tenacity import retry, stop_after_attempt, wait_exponential

from app.core.config import settings

BASE = "https://api.openai.com/v1"
MODEL = "text-embedding-3-small"  # contents.embedding 의 vector(1536) 과 맞춘다
BATCH = 100  # 한 요청에 넣는 문서 수


@retry(stop=stop_after_attempt(3), wait=wait_exponential(min=1, max=20))
async def embed(client: httpx.AsyncClient, texts: list[str]) -> list[list[float]]:
    """여러 문서를 한 번에. 순서는 입력과 같다"""
    res = await client.post(
        f"{BASE}/embeddings",
        headers={"Authorization": f"Bearer {settings.OPENAI_API_KEY}"},
        json={"model": MODEL, "input": texts},
    )
    res.raise_for_status()
    rows = sorted(res.json()["data"], key=lambda d: d["index"])
    return [row["embedding"] for row in rows]
