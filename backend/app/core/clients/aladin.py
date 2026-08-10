from tenacity import retry, stop_after_attempt, wait_exponential

from app.core.config import settings

BASE = "https://www.aladin.co.kr/ttb/api"

@retry(stop=stop_after_attempt(3), wait=wait_exponential(min=1, max=10))
async def fetch_bestsellers(client, start: int, max_results: int = 50) -> list[dict]:
    params = {
        "ttbkey": settings.ALADIN_TTB_KEY,
        "QueryType": "Bestseller",
        "SearchTarget": "Book",
        "MaxResults": max_results,
        "start": start,
        "output": "js",
        "Version": "20131101",
    }
    res = await client.get(f"{BASE}/ItemList.aspx", params=params)
    res.raise_for_status()
    return res.json()["item"]