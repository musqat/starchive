"""자연어 검색 평가용 질의를 만든다

작품마다 "사용자가 이걸 찾을 때 칠 만한 문장" 을 LLM 에 쓰게 하고 파일로 남긴다.
검색이 그 문장으로 원래 작품을 찾아내는지가 평가다

    사용자가 쓰는 말로 쓰게 한다
    나쁨  황폐해진 지구에서 웜홀을 통해 새로운 행성을 찾는 우주비행사들
    좋음  가족 생각나는 우주 영화

    uv run python -m scripts.make_search_eval           # 대상 수만
    uv run python -m scripts.make_search_eval --apply
"""

import asyncio
import json
import random
import sys
from pathlib import Path

import httpx
from sqlalchemy import select

from app.core.clients.openai import complete_json
from app.core.config import settings
from app.domains.content.models import Content, ContentType
from app.ingestion.db import Session

OUT = Path("data/search_eval.json")
PER_TYPE = 100  # 매체마다 몇 작품
QUERIES = 2  # 작품마다 질의 몇 개
SEED = 42

SYSTEM = """너는 영화·책 검색 서비스의 사용자다.
주어진 작품을 찾으려고 검색창에 칠 문장을 만든다.

규칙
- 제목, 등장인물 이름, 감독·작가 이름을 쓰지 않는다
- 줄거리를 요약하지 않는다. 분위기·감정·상황으로 쓴다
- 8~20자 정도의 짧은 구어체
- 서로 다른 각도로 2개

예
  작품: 인터스텔라
  {"queries": ["가족 생각나는 우주 영화", "마지막에 눈물 나는 SF"]}

  작품: 기생충
  {"queries": ["계급 차이 보여주는 한국 영화", "웃다가 소름 돋는 스릴러"]}

답은 JSON 으로만 한다. {"queries": ["...", "..."]} 형식."""


MIN_TITLE_WORD = 2  # 한 글자 겹침은 우연이다


def _leaks_title(title: str, query: str) -> bool:
    """제목 단어가 질의에 그대로 들어갔나 확인
    """
    head = title.split(" - ")[0].split(":")[0]  # 부제는 뺀다
    words = [w for w in head.split() if len(w) >= MIN_TITLE_WORD]
    return any(w in query for w in words)


def prompt(row) -> str:
    parts = [f"제목: {row.title}"]
    if row.genre:
        parts.append(f"장르: {', '.join(row.genre)}")
    if row.description:
        parts.append(f"줄거리: {row.description[:400]}")
    return "\n".join(parts)


def pick(db) -> list:
    """매체마다 무작위. 인기순으로 뽑으면 유명 작품만 남아 쉬워진다"""
    rng = random.Random(SEED)
    chosen = []
    for type_ in (ContentType.MOVIE, ContentType.BOOK):
        rows = db.execute(
            select(Content.id, Content.title, Content.genre, Content.description).where(
                Content.type == type_,
                Content.embedding.isnot(None),
                Content.description.isnot(None),
            )
        ).all()
        chosen += rng.sample(rows, min(PER_TYPE, len(rows)))
    return chosen


async def main() -> None:
    with Session() as db:
        rows = pick(db)
    print(f"대상 {len(rows)}작품 → 질의 {len(rows) * QUERIES}개")

    if "--apply" not in sys.argv:
        print("--apply 를 붙이면 실행한다")
        return

    sem = asyncio.Semaphore(settings.MAX_CONCURRENCY)

    async def one(client, row) -> dict | None:
        async with sem:
            try:
                body = await complete_json(client, SYSTEM, prompt(row))
                queries = json.loads(body).get("queries", [])
            except Exception as exc:  # 개별 실패는 건너뛴다
                print(f"  실패 {row.title[:20]} — {type(exc).__name__}")
                return None
        queries = [q.strip() for q in queries if isinstance(q, str) and q.strip()]
        queries = [q for q in queries if not _leaks_title(row.title, q)]
        if not queries:
            return None
        return {"content_id": row.id, "title": row.title, "queries": queries[:QUERIES]}

    async with httpx.AsyncClient(timeout=settings.LLM_TIMEOUT_SECONDS) as client:
        made = await asyncio.gather(*[one(client, r) for r in rows])

    items = [m for m in made if m]
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(items, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"저장 {len(items)}작품 / 질의 {sum(len(i['queries']) for i in items)}개 → {OUT}")

    for item in items[:3]:
        print(f"  {item['title'][:26]:28} {' / '.join(item['queries'])}")


if __name__ == "__main__":  # import 시 실행 방지
    asyncio.run(main())
