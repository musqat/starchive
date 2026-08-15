"""줄거리가 있는 콘텐츠에 임베딩을 채운다

텍스트가 바뀐 것과 아직 없는 것만 다시 만든다.
증분 수집으로 새 책이 들어와도 이 스크립트를 통해 임베딩 가능

    uv run python -m scripts.embed          # 대상 개수만
    uv run python -m scripts.embed --apply  # 실행
"""

import asyncio
import sys
from datetime import UTC, datetime

import httpx
from sqlalchemy import or_, select

from app.core.clients.openai import BATCH, embed
from app.domains.content.models import Content
from app.ingestion.db import Session
from app.ingestion.normalizer import build_embedding_text


def targets(session):
    """줄거리가 있고, 아직 없거나 텍스트가 달라진 것"""
    rows = session.scalars(
        select(Content).where(
            Content.description.isnot(None),
            or_(Content.embedding.is_(None), Content.embedding_text.is_(None)),
        )
    ).all()

    pending = []
    for row in rows:
        text = build_embedding_text(row.title, row.genre, row.creator, row.description)
        if text:
            pending.append((row, text))
    return pending


async def main() -> None:
    apply = "--apply" in sys.argv

    with Session() as session:
        pending = targets(session)
        chars = sum(len(t) for _, t in pending)
        print(f"대상 {len(pending):,}건 / 총 {chars:,}자")

        if not apply:
            print("--apply 를 붙이면 실행한다")
            return

        async with httpx.AsyncClient(timeout=60) as client:
            for start in range(0, len(pending), BATCH):
                chunk = pending[start : start + BATCH]
                vectors = await embed(client, [text for _, text in chunk])

                now = datetime.now(UTC)
                for (row, text), vector in zip(chunk, vectors, strict=True):
                    row.embedding = vector
                    row.embedding_text = text
                    row.embedded_at = now
                session.commit()
                print(f"  {min(start + BATCH, len(pending)):,} / {len(pending):,}")


asyncio.run(main())
