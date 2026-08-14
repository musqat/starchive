import httpx
from tenacity import retry, stop_after_attempt, wait_exponential

from app.core.config import settings

BASE = "https://api.themoviedb.org/3"

@retry(stop=stop_after_attempt(3), wait=wait_exponential(min=1, max=10))
async def fetch_movie(client: httpx.AsyncClient, tmdb_id: int) -> dict | None:
    headers = {"Authorization": f"Bearer {settings.TMDB_API_KEY}"}
    # append_to_response 로 감독·출연과 시청 가능한 곳을 한 번에
    url = (
        f"{BASE}/movie/{tmdb_id}"
        "?language=ko-KR&append_to_response=credits,watch/providers"
    )

    res = await client.get(url, headers=headers)

    if res.status_code == 404:
        return None

    res.raise_for_status()   # 에러(429, 5xx)만 예외로

    return res.json()