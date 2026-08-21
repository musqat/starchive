"""후보 생성 — 내용 점수 + 이웃 점수

내용 점수 - 취향 중심과 줄거리가 가까운 것. 임베딩만 필요
이웃 점수 - 나와 겹치는 사람들이 좋아한 것. 평점만 필요

임베딩은 '어바웃 타임'을 인터스텔라 옆에 못 놓음. 평점과 임베딩을 통합하면 가능
"""

from dataclasses import dataclass
from datetime import date, timedelta

from sqlalchemy import Float, Select, cast, func, select
from sqlalchemy.orm import Session

from app.domains.content.models import Content, ContentType
from app.domains.recommendation import dedupe, profile
from app.domains.user.models import UserContent

# 측정 결과 -> 0.7:0.3 은 Recall@10 0.021 로 인기순(0.097)에 졌다
# 두 점수의 범위 차이 때문 —> 내용 기반은 바닥이 0.35, 이웃은 바닥이 0
# -> 점수에서 차이가 나고 시작함
CONTENT_WEIGHT = 0.3
TASTE_WEIGHT = 0.7

MIN_SIMILARITY = 0.35  # 최소 유사도 - 이 유사도 이상만 체크
MIN_PEER_OVERLAP = 2  # 최소 작품 겹친 이웃수 - 1의 경우 하나만 겹쳐도 추천되서 2 이상으로
POOL = 100  # 뽑아 섞을 개수
LIMIT = 30

# 신작은 시드 평점이 없어 이웃 점수가 0이다. 점수 경쟁으로는 상위 10에 못 올라온다
# 2칸이면 Recall 0.150 -> 0.130 (인기순 0.097 대비 +34%), 커버리지 82 -> 101편
RECENT_SLOTS = 2
RECENT_SINCE = date(2018, 1, 1)  # MovieLens 가 여기서 끝난다
FRESH_DAYS = 730  # 편수로 밀려 최근작이 안 뽑히므로 최근 2년을 따로 본다


@dataclass
class Candidate:
    content_id: str
    title: str
    type: ContentType
    score: float
    content_score: float
    taste_score: float


def _exclude_mine(user_id: int) -> Select:
    return select(UserContent.content_id).where(UserContent.user_id == user_id)


def by_content(
    db: Session,
    vector: list[float],
    user_id: int,
    type_: ContentType | None,
    limit: int = POOL,
    only_ids: set[str] | None = None,
) -> dict[str, float]:
    """내용 점수 — 취향 중심과 줄거리가 가까운 작품

    값은 코사인 유사도. 1에 가까울수록 비슷함
    """
    similarity = (1 - Content.embedding.cosine_distance(vector)).label("similarity")
    stmt = (
        select(Content.id, similarity)
        .where(
            Content.embedding.isnot(None),
            Content.id.not_in(_exclude_mine(user_id)),
            similarity >= MIN_SIMILARITY,
        )
        .order_by(similarity.desc())
        .limit(limit)
    )
    if type_:
        stmt = stmt.where(Content.type == type_)
    if only_ids:
        stmt = stmt.where(Content.id.in_(only_ids))
    return {row.id: float(row.similarity) for row in db.execute(stmt)}


def by_taste(
    db: Session,
    user_id: int,
    type_: ContentType | None,
    limit: int = POOL,
    only_ids: set[str] | None = None,
) -> dict[str, float]:
    """이웃 점수 — 나와 겹치는 사람들이 좋아한 작품

    3홉 — 내가 좋아한 것 → 그걸 좋아한 사람들 → 그 사람들이 좋아한 다른 것

    가운데 홉이 content_id 로 조회. ix_user_contents_content_rating 없으면 전건 스캔
    """
    mine = (
        select(UserContent.content_id)
        .where(UserContent.user_id == user_id, UserContent.rating >= profile.LIKED_RATING)
        .subquery()
    )
    mine_count = (
        select(func.count())
        .select_from(UserContent)
        .where(UserContent.user_id == user_id, UserContent.rating >= profile.LIKED_RATING)
        .scalar_subquery()
    )
    totals = (
        select(UserContent.user_id, func.count().label("total"))
        .where(UserContent.rating >= profile.LIKED_RATING)
        .group_by(UserContent.user_id)
        .subquery()
    )

    # 자카드 — 겹침을 합집합으로 나눈다. 개수만 세면 많이 본 사람이 모두의 이웃이 된다
    overlap = func.count()
    weight = cast(overlap, Float) / (mine_count + totals.c.total - overlap)
    peers = (
        select(UserContent.user_id, weight.label("weight"))
        .join(mine, mine.c.content_id == UserContent.content_id)
        .join(totals, totals.c.user_id == UserContent.user_id)
        .where(UserContent.rating >= profile.LIKED_RATING, UserContent.user_id != user_id)
        .group_by(UserContent.user_id, totals.c.total)
        .having(overlap >= MIN_PEER_OVERLAP)
        .subquery()
    )

    signal = func.sum(peers.c.weight).label("signal")
    stmt = (
        select(UserContent.content_id, signal)
        .join(peers, peers.c.user_id == UserContent.user_id)
        .where(
            UserContent.rating >= profile.LIKED_RATING,
            UserContent.content_id.not_in(_exclude_mine(user_id)),
        )
        .group_by(UserContent.content_id)
        .order_by(signal.desc())
        .limit(limit)
    )
    if type_:
        stmt = stmt.join(Content, Content.id == UserContent.content_id).where(Content.type == type_)
    if only_ids:
        stmt = stmt.where(UserContent.content_id.in_(only_ids))

    rows = db.execute(stmt).all()
    if not rows:
        return {}

    # 절대값은 데이터 크기에 좌우돼 내용 점수와 못 섞음. 최댓값으로 나눔
    top = float(max(row.signal for row in rows))
    return {row.content_id: float(row.signal) / top for row in rows}


def generate(
    db: Session,
    user_id: int,
    type_: ContentType | None = None,
    limit: int = LIMIT,
    only_ids: set[str] | None = None,
) -> list[Candidate]:
    """후보 목록. 기록이 없으면 빈 목록 — 호출한 쪽에서 인기순으로 폴백"""
    vector = profile.build(db, user_id, type_)

    content = by_content(db, vector, user_id, type_, only_ids=only_ids) if vector else {}
    taste = by_taste(db, user_id, type_, only_ids=only_ids)

    scores: dict[str, tuple[float, float]] = {}
    for content_id in content.keys() | taste.keys():
        scores[content_id] = (content.get(content_id, 0.0), taste.get(content_id, 0.0))

    if not scores:
        return []

    rows = db.execute(
        select(Content.id, Content.title, Content.type).where(Content.id.in_(scores))
    ).all()

    candidates = [
        Candidate(
            content_id=row.id,
            title=row.title,
            type=row.type,
            score=CONTENT_WEIGHT * scores[row.id][0] + TASTE_WEIGHT * scores[row.id][1],
            content_score=scores[row.id][0],
            taste_score=scores[row.id][1],
        )
        for row in rows
    ]
    candidates.sort(key=lambda c: c.score, reverse=True)
    # 판본만 다른 것을 빼려면 점수순으로 정렬
    return dedupe.drop_duplicates(candidates, _recorded_titles(db, user_id))[:limit]


def _recorded_titles(db: Session, user_id: int) -> set[str]:
    """내가 기록한 작품의 정규화 제목 -> 판본 중복 제거용"""
    stmt = (
        select(Content.title)
        .join(UserContent, UserContent.content_id == Content.id)
        .where(UserContent.user_id == user_id)
    )
    return {dedupe.normalize(title) for title in db.scalars(stmt)}


def _recent_ids(db: Session, type_: ContentType | None, fresh: bool) -> set[str]:
    stmt = select(Content.id).where(
        Content.release_date >= RECENT_SINCE, Content.embedding.isnot(None)
    )
    cut = date.today() - timedelta(days=FRESH_DAYS)
    stmt = stmt.where(Content.release_date >= cut if fresh else Content.release_date < cut)
    if type_:
        stmt = stmt.where(Content.type == type_)
    return set(db.scalars(stmt))


def recent_picks(
    db: Session,
    user_id: int,
    type_: ContentType | None = None,
    limit: int = RECENT_SLOTS,
) -> list[Candidate]:
    """신작 자리. 내용 점수로만 뽑는다 — 이웃 점수가 0이라 쓸 수 없다

    최근 2년에서 절반을 먼저 채운다. 한 풀에서 뽑으면 편수가 많은 옛날 것이 이긴다
    """
    vector = profile.build(db, user_id, type_)
    if not vector or limit <= 0:
        return []

    fresh_n = max(1, limit // 2)
    picked: dict[str, float] = {}
    for want, fresh in ((fresh_n, True), (limit - fresh_n, False)):
        pool = _recent_ids(db, type_, fresh) - set(picked)
        if not pool or want <= 0:
            continue
        picked |= by_content(db, vector, user_id, type_, limit=want, only_ids=pool)

    if not picked:
        return []

    rows = db.execute(
        select(Content.id, Content.title, Content.type).where(Content.id.in_(picked))
    ).all()
    found = [
        Candidate(
            content_id=row.id,
            title=row.title,
            type=row.type,
            score=CONTENT_WEIGHT * picked[row.id],
            content_score=picked[row.id],
            taste_score=0.0,
        )
        for row in rows
    ]
    found.sort(key=lambda c: c.score, reverse=True)
    return found[:limit]
