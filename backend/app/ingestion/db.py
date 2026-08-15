"""수집 스크립트 공용 DB 유틸"""

from sqlalchemy import create_engine
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.orm import sessionmaker

from app.core.config import settings
from app.domains.content.models import Content

engine = create_engine(settings.DIRECT_URL)
Session = sessionmaker(bind=engine)


def upsert(session, row: dict) -> None:
    """id 충돌 시 나머지 컬럼을 새 값으로 덮어씀"""
    stmt = insert(Content).values(**row)
    stmt = stmt.on_conflict_do_update(
        index_elements=["id"],
        set_={k: stmt.excluded[k] for k in row if k != "id"},
    )
    session.execute(stmt)
