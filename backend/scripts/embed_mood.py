"""영화에 분위기 문장을 만들어 임베딩을 다시 채운다 — 검색용 색인 개선

영화 줄거리는 사건 나열이라 "비 오는 날 볼 영화" 같은 질의와 안 맞는다.
LLM 으로 분위기·감정·상황 문장을 만들어 임베딩 텍스트에 얹는다
(측정: 영화 검색 R@10 0.223 -> 0.290, 질의 확장은 오히려 손해였다)

분위기 문장은 content_metadata.mood 에 저장해 다시 안 만든다.
이미 mood 가 있는 영화는 건너뛴다

    uv run python -m scripts.embed_mood          # 대상 개수만
    uv run python -m scripts.embed_mood --apply
"""

import asyncio
import json
import sys
from datetime import UTC, datetime

import httpx
from sqlalchemy import select

from app.core.clients.openai import BATCH, complete_json, embed
from app.core.config import settings
from app.domains.content.models import Content, ContentType
from app.ingestion.db import Session
from app.ingestion.normalizer import build_embedding_text

CONCURRENCY = 6

SYSTEM = """영화 정보를 보고, 사용자가 이 영화를 찾을 때 떠올릴 분위기·감정·상황·소재를
문장으로 쓴다. 줄거리를 요약하지 않는다. 제목·인물 이름은 쓰지 않는다.
2~3문장. JSON {"mood": "..."} 로만 답한다."""


def prompt(row) -> str:
    parts = [row.title]
    if row.genre:
        parts.append(", ".join(row.genre))
    if row.description:
        parts.append(row.description[:400])
    return "\n".join(parts)


async def make_mood(client, sem, row) -> tuple[str, str] | None:
    async with sem:
        try:
            body = await complete_json(client, SYSTEM, prompt(row))
            mood = json.loads(body).get("mood", "").strip()
        except Exception as exc:
            print(f"  실패 {row.title[:20]} — {type(exc).__name__}")
            return None
    return (row.id, mood) if mood else None


async def main() -> None:
    apply = "--apply" in sys.argv

    with Session() as session:
        rows = session.scalars(
            select(Content).where(
                Content.type == ContentType.MOVIE,
                Content.description.isnot(None),
                Content.embedding.isnot(None),
            )
        ).all()
        pending = [r for r in rows if not (r.content_metadata or {}).get("mood")]

    print(f"영화 {len(rows):,}편 중 분위기 없는 것 {len(pending):,}편")
    if not apply:
        print("--apply 를 붙이면 실행한다")
        return

    sem = asyncio.Semaphore(CONCURRENCY)
    async with httpx.AsyncClient(timeout=settings.LLM_TIMEOUT_SECONDS) as client:
        made = await asyncio.gather(*[make_mood(client, sem, r) for r in pending])
    moods = dict(m for m in made if m)
    print(f"분위기 문장 {len(moods):,}편 생성")

    # 재임베딩 — 분위기를 얹은 새 텍스트로
    with Session() as session:
        rows = session.scalars(select(Content).where(Content.id.in_(moods))).all()
        targets = []
        for row in rows:
            text = build_embedding_text(
                row.title, row.genre, row.creator, row.description, moods[row.id]
            )
            if text:
                targets.append((row, text))

        async with httpx.AsyncClient(timeout=60) as client:
            for start in range(0, len(targets), BATCH):
                chunk = targets[start : start + BATCH]
                vectors = await embed(client, [t for _, t in chunk])
                now = datetime.now(UTC)
                for (row, text), vector in zip(chunk, vectors, strict=True):
                    row.embedding = vector
                    row.embedding_text = text
                    row.embedded_at = now
                    row.content_metadata = {**(row.content_metadata or {}), "mood": moods[row.id]}
                session.commit()
                print(f"  {min(start + BATCH, len(targets)):,} / {len(targets):,}")


if __name__ == "__main__":  # import 시 실행 방지
    asyncio.run(main())
