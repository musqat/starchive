"""자연어 검색 성능 측정

make_search_eval 이 만든 질의로 검색해서 원래 작품이 상위에 나오는지 본다.
정답이 작품 하나뿐이라 Recall@K 는 찾았는지를 확인한다.

MRR 을 같이 본다 — 1위로 찾으면 1.0, 5위면 0.2. 순위까지 보는 지표

    uv run python -m scripts.evaluate_search
"""

import asyncio
import json
from pathlib import Path

import httpx

from app.core.clients.openai import embed
from app.core.config import settings
from app.domains.content import search
from app.ingestion.db import Session

DATA = Path("data/search_eval.json")
CUTS = (1, 5, 10, 20)
BATCH = 100  # 임베딩 한 요청에 넣는 질의 수


async def embed_all(queries: list[str]) -> list[list[float]]:
    async with httpx.AsyncClient(timeout=settings.LLM_TIMEOUT_SECONDS) as client:
        out: list[list[float]] = []
        for start in range(0, len(queries), BATCH):
            out += await embed(client, queries[start : start + BATCH])
        return out


async def main() -> None:
    if not DATA.exists():
        print(f"{DATA} 가 없다. scripts.make_search_eval --apply 를 먼저 돌린다")
        return

    items = json.loads(DATA.read_text(encoding="utf-8"))
    pairs = [(item["content_id"], item["title"], q) for item in items for q in item["queries"]]
    print(f"질의 {len(pairs)}개 / 작품 {len(items)}개\n")

    vectors = await embed_all([q for _, _, q in pairs])

    hits = dict.fromkeys(CUTS, 0)
    rr = 0.0
    misses = []
    with Session() as db:
        for (content_id, title, query), vector in zip(pairs, vectors, strict=True):
            found = [cid for cid, _ in search.by_query(db, vector, limit=max(CUTS))]
            rank = found.index(content_id) + 1 if content_id in found else None
            if rank:
                rr += 1 / rank
                for cut in CUTS:
                    if rank <= cut:
                        hits[cut] += 1
            else:
                misses.append((title, query))

    n = len(pairs)
    for cut in CUTS:
        print(f"Recall@{cut:<3} {hits[cut] / n:.3f}   ({hits[cut]}/{n})")
    print(f"MRR      {rr / n:.3f}")

    print(f"\n못 찾은 질의 {len(misses)}개 중 앞의 10개")
    for title, query in misses[:10]:
        print(f"  {title[:26]:28} {query}")


if __name__ == "__main__":  # import 시 실행 방지
    asyncio.run(main())
