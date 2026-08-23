"""검색 엔드포인트 — 하이브리드 + 코멘트 (RAG)

제목·감독·배우는 SQL 로 정확히 잡고, 분위기·내용은 벡터로 찾는다.
자연어 질의(정확 매칭이 없는)일 때는 결과를 LLM 에 넣어 한 줄 코멘트를 만든다
— 검색(Retrieval) + 생성(Generation) 이 붙은 RAG 다

질의 확장(LLM 으로 질의를 부풀리기)은 안 붙인다 — 측정에서 오히려 손해였다
(범용어가 질의를 카탈로그 중심으로 끌어당긴다)
"""

import json

import httpx
from fastapi import APIRouter, Depends, Query
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.clients.openai import complete_json, embed
from app.core.config import settings
from app.core.db import get_db
from app.core.deps import get_current_user_optional
from app.domains.content import search
from app.domains.content.models import Content, ContentType
from app.domains.content.router import attach_records
from app.domains.content.schemas import SearchResult
from app.domains.user.models import User

router = APIRouter(tags=["search"])

COMMENT_ITEMS = 6  # 코멘트에 참고할 상위 결과 수

COMMENT_SYSTEM = """사용자의 검색어와 찾아준 작품 목록을 보고, 어떤 작품들을 골랐는지
한 문장으로 짧게 말한다. 제목을 나열하지 않는다. 분위기·결로 요약한다.
"~ 위주로 골랐어요" 같은 다정한 말투. JSON {"comment": "..."} 로만 답한다."""


async def _embed_query(query: str) -> list[float] | None:
    """질의 벡터. 키가 없거나 실패하면 None — 검색은 정확 매칭만으로 넘어간다"""
    if not settings.OPENAI_API_KEY:
        return None
    try:
        async with httpx.AsyncClient(timeout=settings.LLM_TIMEOUT_SECONDS) as client:
            vectors = await embed(client, [query])
        return vectors[0]
    except Exception:
        return None


async def _comment(query: str, items: list[Content]) -> str | None:
    """검색 결과를 보고 LLM 이 쓴 한 줄. 실패하면 None — 코멘트는 없어도 된다"""
    if not settings.OPENAI_API_KEY or not items:
        return None
    lines = [f"- {c.title} ({', '.join(c.genre or [])})" for c in items[:COMMENT_ITEMS]]
    user = f"검색어: {query}\n찾은 작품:\n" + "\n".join(lines)
    try:
        async with httpx.AsyncClient(timeout=settings.LLM_TIMEOUT_SECONDS) as client:
            body = await complete_json(client, COMMENT_SYSTEM, user)
        return json.loads(body).get("comment", "").strip() or None
    except Exception:
        return None


@router.get("/search", summary="검색 (하이브리드 + 코멘트)", response_model=SearchResult)
async def search_contents(
    q: str = Query(min_length=1),
    type: ContentType | None = None,
    user: User | None = Depends(get_current_user_optional),
    db: Session = Depends(get_db),
):
    query = q.strip()
    if not query:
        return SearchResult(comment=None, items=[])

    # 정확 매칭 먼저 — 제목·감독·배우. "인터스텔라", "크리스토퍼 놀란" 은 이쪽이 잡는다
    exact = search.by_exact(db, query, type_=type)
    ordered = list(exact)
    seen = set(ordered)

    # 의미 검색 — 분위기·내용. 정확 매칭에 없는 것만 뒤에 붙인다
    vector = await _embed_query(query)
    if vector is not None:
        for cid, _ in search.by_query(db, vector, type_=type):
            if cid not in seen:
                seen.add(cid)
                ordered.append(cid)

    if not ordered:
        return SearchResult(comment=None, items=[])

    rank = {cid: i for i, cid in enumerate(ordered)}
    rows = db.scalars(select(Content).where(Content.id.in_(rank))).unique().all()
    items = sorted(rows, key=lambda c: rank[c.id])  # 정확 매칭 → 의미 순

    # 코멘트는 자연어 질의일 때만. 제목·이름으로 찾으면(정확 매칭) 어색하다
    comment = None if exact else await _comment(query, items)

    attach_records(db, user, items)
    return SearchResult(comment=comment, items=items)
