"""후보 생성 — 내용 점수 + 이웃 점수

내용 점수 - 취향 중심과 줄거리가 가까운 것. 임베딩만 필요
이웃 점수 - 나와 겹치는 사람들이 좋아한 것. 평점만 필요

임베딩은 '어바웃 타임'을 인터스텔라 옆에 못 놓음. 평점과 임베딩을 통합하면 가능
"""

import random
from dataclasses import dataclass
from datetime import date, timedelta

from sqlalchemy import Float, Select, cast, func, select
from sqlalchemy.orm import Session

from app.domains.content.models import Content, ContentType
from app.domains.recommendation import dedupe, profile
from app.domains.user.models import UserContent

# (내용, 이웃) 매체마다 쓸 수 있는 신호가 다르다
#
# 영화 — 내용 점수는 자기 힘으로 한 편도 못 올리고 이웃 점수가 뽑은 것의 순서만 흔든다.
#        0.3 -> 0.0 으로 Recall 0.178 -> 0.190, NDCG 0.285 -> 0.332
# 책   — 시드가 MovieLens 라 도서 평점이 0건이다. 이웃 점수가 전부 0이라 내용 점수만 돈다.
#        측정된 적 없다
WEIGHTS = {
    ContentType.MOVIE: (0.0, 1.0),
    ContentType.BOOK: (0.3, 0.7),
}
DEFAULT_WEIGHT = (0.3, 0.7)  # 매체를 안 가릴 때

MIN_SIMILARITY = 0.35  # 최소 유사도 - 이 유사도 이상만 체크
MIN_PEER_OVERLAP = 2  # 최소 작품 겹친 이웃수 - 1의 경우 하나만 겹쳐도 추천되서 2 이상으로

# 이웃 점수를 좋아요 수의 몇 제곱으로 나누나. 0 이면 안 나눔, 1 이면 인기를 완전히 지움
# 나누기 전 이웃 점수는 인기 순서와 83.5% 일치했다 — 모두가 좋아하는 작품은
# 내 취향을 알려주지 않는다. 남들 안 보는 작품을 겹쳐 좋아하는 것이 신호다
#       Recall  NDCG  작품수
# 0      0.149 0.258    199
# 0.7    0.190 0.332    369
# 0.8    0.159 0.260    628   좋아요 두세 개짜리가 상위를 덮는다
POPULARITY_POWER = 0.7
POOL = 100  # 뽑아 섞을 개수
LIMIT = 30

# 한 시리즈에서 몇 편까지. 200명 중 90명이 같은 시리즈를 2편 이상 받았고
# 대부분 스타워즈와 반지의 제왕이었다. 값은 측정으로 정한다
MAX_PER_SERIES = 1

# 신작은 시드 평점이 없어 이웃 점수가 0이다. 점수 경쟁으로는 상위 10에 못 올라온다
# 2칸일 때 아래 칸이 2018~2024 에서 뽑혀 신작이 아니었다. 1칸으로 줄이니
# Recall 0.131 -> 0.143 (0칸은 0.149), 같은 영화를 추천받은 사람 최대 15 -> 12명
RECENT_SLOTS = 1
RECENT_SINCE = date(2018, 1, 1)  # MovieLens 가 여기서 끝난다
FRESH_DAYS = 730  # 최근 2년. 1년으로 좁히면 풀이 274 -> 107편이라 반복이 심해진다
# 유사도 상위 몇 개에서 무작위로 뽑나. 순서 하나로 갈려 모두가 1등을 가져가던 것을 막는다
# 풀은 274편인데 20이면 41종만 나갔다. 50 이면 72종,
# 같은 영화를 추천받은 사람 최대 17 -> 9명
# 100 은 103종까지 늘지만 평균 유사도가 0.623 -> 0.578 로 빠져 장르가 흐른다
RECENT_SAMPLE = 50


@dataclass
class Candidate:
    content_id: str
    title: str
    type: ContentType
    score: float
    content_score: float
    taste_score: float
    series: str | None = None  # TMDB 컬렉션 id. 없으면 단독 영화


def _exclude_mine(user_id: int) -> Select:
    return select(UserContent.content_id).where(UserContent.user_id == user_id)


def _with_series() -> Select:
    """후보 표시용 컬럼 + 시리즈 id

    JSONB 를 통째로 꺼내면 출연진·시청처까지 딸려온다. 경로만 뽑는다
    """
    series = Content.content_metadata["collection"]["id"].astext.label("series")
    return select(Content.id, Content.title, Content.type, series)


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

    # 인기 = 나 말고 다른 사람들이 좋아한 횟수. 나를 넣으면 평가에서 정답만 1 줄어 유리해진다
    popularity = (
        select(UserContent.content_id, func.count().label("n"))
        .where(UserContent.rating >= profile.LIKED_RATING, UserContent.user_id != user_id)
        .group_by(UserContent.content_id)
        .subquery()
    )

    # 모두가 좋아하는 작품은 내 취향을 알려주지 않는다. 인기로 나눠 겹침의 희소성만 남긴다
    signal = (
        func.sum(peers.c.weight) / func.power(cast(popularity.c.n, Float), POPULARITY_POWER)
    ).label("signal")
    stmt = (
        select(UserContent.content_id, signal)
        .join(peers, peers.c.user_id == UserContent.user_id)
        .join(popularity, popularity.c.content_id == UserContent.content_id)
        .where(
            UserContent.rating >= profile.LIKED_RATING,
            UserContent.content_id.not_in(_exclude_mine(user_id)),
        )
        .group_by(UserContent.content_id, popularity.c.n)
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

    rows = db.execute(_with_series().where(Content.id.in_(scores))).all()
    content_weight, taste_weight = WEIGHTS.get(type_, DEFAULT_WEIGHT)

    candidates = [
        Candidate(
            content_id=row.id,
            title=row.title,
            type=row.type,
            score=content_weight * scores[row.id][0] + taste_weight * scores[row.id][1],
            content_score=scores[row.id][0],
            taste_score=scores[row.id][1],
            series=row.series,
        )
        for row in rows
    ]
    candidates.sort(key=lambda c: c.score, reverse=True)
    # 판본만 다른 것과 같은 시리즈를 빼려면 점수순으로 정렬
    kept = dedupe.drop_duplicates(candidates, _recorded_titles(db, user_id))
    return dedupe.cap_series(kept, MAX_PER_SERIES)[:limit]


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
    rng: random.Random | None = None,
) -> list[Candidate]:
    """신작 자리. 내용 점수로만 뽑는다 — 이웃 점수가 0이라 쓸 수 없다

    최근 2년에서 절반을 먼저 채운다. 한 풀에서 뽑으면 편수가 많은 옛날 것이 이긴다
    """
    vector = profile.build(db, user_id, type_)
    if not vector or limit <= 0:
        return []

    picker = rng or random
    fresh_n = max(1, limit // 2)
    picked: dict[str, float] = {}
    for want, fresh in ((fresh_n, True), (limit - fresh_n, False)):
        pool = _recent_ids(db, type_, fresh) - set(picked)
        if not pool or want <= 0:
            continue
        scored = by_content(db, vector, user_id, type_, limit=RECENT_SAMPLE, only_ids=pool)
        for cid in picker.sample(sorted(scored), min(want, len(scored))):
            picked[cid] = scored[cid]

    if not picked:
        return []

    rows = db.execute(_with_series().where(Content.id.in_(picked))).all()
    found = [
        Candidate(
            content_id=row.id,
            title=row.title,
            type=row.type,
            score=picked[row.id],  # 이웃 점수가 없어 내용 점수가 곧 점수다
            content_score=picked[row.id],
            taste_score=0.0,
            series=row.series,
        )
        for row in rows
    ]
    found.sort(key=lambda c: c.score, reverse=True)
    return found[:limit]
