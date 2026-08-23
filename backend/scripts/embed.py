"""줄거리가 있는 콘텐츠에 임베딩을 채운다

영화는 분위기 문장(mood)을 LLM 으로 만들어 함께 넣는다 — 검색용. 영화 줄거리는
사건 나열이라 "비 오는 날 볼 영화" 같은 질의와 안 맞는다. 분위기·감정으로 다시 쓴
문장을 얹으면 질의 공간에 가까워진다. 책은 소개가 이미 분위기라 안 만든다

아직 임베딩이 없는 것만 처리해 여러 번 돌려도 된다. 수집 후 이 스크립트 한 번이면
새 영화도 mood 까지 채워진다

    uv run python -m scripts.embed          # 대상 개수만
    uv run python -m scripts.embed --apply
"""

import asyncio
import json
import sys
from datetime import UTC, datetime

import httpx
from sqlalchemy import or_, select

from app.core.clients.openai import BATCH, complete_json, embed
from app.core.config import settings
from app.domains.content.models import Content, ContentType
from app.ingestion.db import Session
from app.ingestion.normalizer import build_embedding_text

CONCURRENCY = 6

MOOD_SYSTEM = """영화 정보를 보고, 사용자가 이 영화를 찾을 때 떠올릴 분위기·감정·상황·소재를
문장으로 쓴다. 줄거리를 요약하지 않는다. 제목·인물 이름은 쓰지 않는다.
2~3문장. JSON {"mood": "..."} 로만 답한다."""


def _mood_prompt(row: Content) -> str:
    parts = [row.title]
    if row.genre:
        parts.append(", ".join(row.genre))
    if row.description:
        parts.append(row.description[:400])
    return "\n".join(parts)


async def _make_mood(client, sem, row: Content) -> tuple[str, str] | None:
    async with sem:
        try:
            body = await complete_json(client, MOOD_SYSTEM, _mood_prompt(row))
            mood = json.loads(body).get("mood", "").strip()
        except Exception as exc:  # 개별 실패는 mood 없이 넘어간다
            print(f"  분위기 실패 {row.title[:20]} — {type(exc).__name__}")
            return None
    return (row.id, mood) if mood else None


def targets(session) -> list[Content]:
    """줄거리가 있고, 아직 임베딩이 없는 것"""
    return list(
        session.scalars(
            select(Content).where(
                Content.description.isnot(None),
                or_(Content.embedding.is_(None), Content.embedding_text.is_(None)),
            )
        ).all()
    )


async def main() -> None:
    apply = "--apply" in sys.argv

    with Session() as session:
        rows = targets(session)
        movies = [r for r in rows if r.type == ContentType.MOVIE]
        print(f"대상 {len(rows):,}건 (영화 {len(movies):,} — 분위기 문장 생성)")

        if not apply:
            print("--apply 를 붙이면 실행한다")
            return

        # 영화 분위기 문장 — 병렬
        sem = asyncio.Semaphore(CONCURRENCY)
        async with httpx.AsyncClient(timeout=settings.LLM_TIMEOUT_SECONDS) as client:
            made = await asyncio.gather(*[_make_mood(client, sem, r) for r in movies])
        moods = dict(m for m in made if m)
        print(f"분위기 문장 {len(moods):,}편")

        # 텍스트 조립 — 영화는 mood 를 얹는다
        pending = []
        for row in rows:
            text = build_embedding_text(
                row.title, row.genre, row.creator, row.description, moods.get(row.id)
            )
            if text:
                pending.append((row, text))

        chars = sum(len(t) for _, t in pending)
        print(f"임베딩 대상 {len(pending):,}건 / {chars:,}자")

        async with httpx.AsyncClient(timeout=60) as client:
            for start in range(0, len(pending), BATCH):
                chunk = pending[start : start + BATCH]
                vectors = await embed(client, [text for _, text in chunk])

                now = datetime.now(UTC)
                for (row, text), vector in zip(chunk, vectors, strict=True):
                    row.embedding = vector
                    row.embedding_text = text
                    row.embedded_at = now
                    if row.id in moods:
                        row.content_metadata = {
                            **(row.content_metadata or {}),
                            "mood": moods[row.id],
                        }
                session.commit()
                print(f"  {min(start + BATCH, len(pending)):,} / {len(pending):,}")


if __name__ == "__main__":  # import 시 실행 방지
    asyncio.run(main())
