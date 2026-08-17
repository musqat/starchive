"""후보를 LLM 으로 다시 줄 세운다
실패시 점수순으로 줄 세움
"""

import json
import logging
from dataclasses import dataclass

import httpx

from app.core.clients.openai import complete_json
from app.domains.recommendation.candidates import Candidate
from app.domains.recommendation.models import REASON_MAX_LENGTH, ReasonSource
from app.domains.recommendation.prompts import SYSTEM, PromptItem, build_user

log = logging.getLogger(__name__)

TOP_K = 10
TEMPLATE_REASON = "비슷한 작품을 좋아한 분들이 높게 평가했어요"


@dataclass
class Ranked:
    candidate: Candidate
    rank: int  # 1 부터
    reason: str
    source: ReasonSource


def fallback(candidates: list[Candidate]) -> list[Ranked]:
    """점수순 상위 K. LLM 을 못 쓸 때의 결과"""
    return [
        Ranked(candidate=c, rank=i, reason=TEMPLATE_REASON, source=ReasonSource.TEMPLATE)
        for i, c in enumerate(candidates[:TOP_K], start=1)
    ]


def _parse(raw: str, candidates: list[Candidate]) -> list[Ranked]:
    """번호를 후보로 되돌린다. 범위 밖과 중복은 버린다"""
    picks = json.loads(raw)["picks"]

    ranked: list[Ranked] = []
    seen: set[int] = set()
    for pick in picks:
        index = int(pick["n"]) - 1
        if not 0 <= index < len(candidates) or index in seen:
            continue
        seen.add(index)
        ranked.append(
            Ranked(
                candidate=candidates[index],
                rank=len(ranked) + 1,
                reason=str(pick.get("reason", "")).strip()[:REASON_MAX_LENGTH] or TEMPLATE_REASON,
                source=ReasonSource.LLM,
            )
        )
        if len(ranked) == TOP_K:
            break
    return ranked


async def rerank(
    client: httpx.AsyncClient,
    liked: list[str],
    candidates: list[Candidate],
    items: list[PromptItem],
) -> list[Ranked]:
    """상위 10개와 이유. 실패·부족이면 점수순으로 채운다"""
    if not candidates:
        return []

    try:
        raw = await complete_json(client, SYSTEM, build_user(liked, items))
        ranked = _parse(raw, candidates)
    except (httpx.HTTPError, json.JSONDecodeError, KeyError, TypeError, ValueError) as exc:
        log.warning("재랭킹 실패, 점수순으로 대체: %s", exc)
        return fallback(candidates)

    # 10개를 못 채우면 남은 점수순으로 메운다
    if len(ranked) < TOP_K:
        chosen = {r.candidate.content_id for r in ranked}
        for candidate in candidates:
            if len(ranked) == TOP_K:
                break
            if candidate.content_id in chosen:
                continue
            ranked.append(
                Ranked(
                    candidate=candidate,
                    rank=len(ranked) + 1,
                    reason=TEMPLATE_REASON,
                    source=ReasonSource.TEMPLATE,
                )
            )
    return ranked
