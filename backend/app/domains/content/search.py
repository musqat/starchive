"""검색 — 정확 매칭과 의미 검색을 합친다 (하이브리드)

벡터 검색은 의미가 비슷한 것을 찾지 글자를 못 맞춘다. "인터스텔라" 를 쳐도 그게 1등이
아니고, "크리스토퍼 놀란" 같은 이름은 아예 못 찾는다. 이건 정확 매칭이 할 일이다

제목·감독·배우는 SQL 로 정확히 잡고(exact), 분위기·내용은 벡터로 찾는다(semantic).
정확 매칭을 위에 두고 그 아래 의미 검색을 붙인다
"""

from sqlalchemy import Select, or_, select
from sqlalchemy.orm import Session

from app.domains.content.models import Content, ContentType

MIN_SIMILARITY = 0.2  # 추천(0.35)보다 낮다. 질의가 짧아 유사도가 전반적으로 낮게 나온다
LIMIT = 20


def by_exact(
    db: Session,
    query: str,
    type_: ContentType | None = None,
    limit: int = LIMIT,
) -> list[str]:
    """제목·감독·저자·배우에 검색어가 든 것. 인기순

    배우는 content_metadata.cast(JSONB 배열)에 있다. 문자열로 캐스팅해 부분 일치
    """
    like = f"%{query}%"
    cast_text = Content.content_metadata["cast"].astext
    stmt: Select = (
        select(Content.id)
        .where(
            or_(
                Content.title.ilike(like),
                Content.creator.ilike(like),
                cast_text.ilike(like),
            )
        )
        .order_by(Content.external_popularity.desc().nulls_last())
        .limit(limit)
    )
    if type_:
        stmt = stmt.where(Content.type == type_)
    return list(db.scalars(stmt))


def by_query(
    db: Session,
    vector: list[float],
    type_: ContentType | None = None,
    limit: int = LIMIT,
) -> list[tuple[str, float]]:
    """(content_id, 유사도) 를 가까운 순으로"""
    similarity = (1 - Content.embedding.cosine_distance(vector)).label("similarity")
    stmt: Select = (
        select(Content.id, similarity)
        .where(Content.embedding.isnot(None), similarity >= MIN_SIMILARITY)
        .order_by(similarity.desc())
        .limit(limit)
    )
    if type_:
        stmt = stmt.where(Content.type == type_)
    return [(row.id, float(row.similarity)) for row in db.execute(stmt)]
