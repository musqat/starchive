import httpx
from tenacity import retry, stop_after_attempt, wait_exponential

from app.core.config import settings

BASE = "https://api.themoviedb.org/3"


@retry(stop=stop_after_attempt(3), wait=wait_exponential(min=1, max=10))
async def fetch_movie(client: httpx.AsyncClient, tmdb_id: int) -> dict | None:
    headers = {"Authorization": f"Bearer {settings.TMDB_API_KEY}"}
    # append_to_response 로 감독·출연과 시청 가능한 곳을 한 번에
    url = f"{BASE}/movie/{tmdb_id}?language=ko-KR&append_to_response=credits,watch/providers"

    res = await client.get(url, headers=headers)

    if res.status_code == 404:
        return None

    res.raise_for_status()  # 에러(429, 5xx)만 예외로

    return res.json()


# MovieLens 가 2018년에 끝난다. 그 뒤 영화는 여기서 목록을 만든다
DISCOVER_SINCE = "2018-01-01"
# MovieLens 상위 3,000편의 중앙값이 1,978표다. 500이면 자릿수가 맞는다
# 100 은 하위 1%(103표)에 붙어 있어 성격이 다르고, 그 문턱은 5,946편이 된다
MIN_VOTE_COUNT = 500
MAX_PAGE = 500  # TMDB 상한


@retry(stop=stop_after_attempt(3), wait=wait_exponential(min=1, max=10))
async def discover_movie_ids(client: httpx.AsyncClient, page: int) -> tuple[list[int], int]:
    """개봉일 기준 신작 id 와 전체 페이지 수. 상세는 fetch_movie 로 따로 받는다"""
    res = await client.get(
        f"{BASE}/discover/movie",
        headers={"Authorization": f"Bearer {settings.TMDB_API_KEY}"},
        params={
            "primary_release_date.gte": DISCOVER_SINCE,
            "vote_count.gte": MIN_VOTE_COUNT,
            "sort_by": "primary_release_date.desc",
            "page": page,
        },
    )
    res.raise_for_status()
    body = res.json()
    return [row["id"] for row in body["results"]], min(body["total_pages"], MAX_PAGE)
