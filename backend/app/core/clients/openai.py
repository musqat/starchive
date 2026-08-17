import httpx
from tenacity import retry, retry_if_exception, stop_after_attempt, wait_exponential

from app.core.config import settings

BASE = "https://api.openai.com/v1"
EMBED_MODEL = "text-embedding-3-small"  # contents.embedding 의 vector(1536) 과 맞춘다
CHAT_MODEL = "gpt-4o-mini"
BATCH = 100  # 한 요청에 넣는 문서 수


def _retryable(exc: BaseException) -> bool:
    """한도 초과와 서버 오류만 재시도"""
    if isinstance(exc, httpx.HTTPStatusError):
        return exc.response.status_code == 429 or exc.response.status_code >= 500
    return isinstance(exc, httpx.TransportError)  # 타임아웃 포함


_retry = retry(
    retry=retry_if_exception(_retryable),
    stop=stop_after_attempt(3),
    wait=wait_exponential(min=1, max=20),
)


def _headers() -> dict[str, str]:
    return {"Authorization": f"Bearer {settings.OPENAI_API_KEY}"}


@_retry
async def embed(client: httpx.AsyncClient, texts: list[str]) -> list[list[float]]:
    """여러 문서를 한 번에. 순서는 입력과 같다"""
    res = await client.post(
        f"{BASE}/embeddings",
        headers=_headers(),
        json={"model": EMBED_MODEL, "input": texts},
    )
    res.raise_for_status()
    rows = sorted(res.json()["data"], key=lambda d: d["index"])
    return [row["embedding"] for row in rows]


@_retry
async def complete_json(client: httpx.AsyncClient, system: str, user: str) -> str:
    """JSON 모드 응답 본문"""
    res = await client.post(
        f"{BASE}/chat/completions",
        headers=_headers(),
        json={
            "model": CHAT_MODEL,
            "messages": [
                {"role": "system", "content": system},
                {"role": "user", "content": user},
            ],
            "response_format": {"type": "json_object"},
            "temperature": 0.3,  # 어느정도 비슷하게 추천
        },
        timeout=settings.LLM_TIMEOUT_SECONDS,
    )
    res.raise_for_status()
    return res.json()["choices"][0]["message"]["content"]
