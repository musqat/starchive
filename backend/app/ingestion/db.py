"""수집 스크립트 공용 DB 유틸"""

import os

from sqlalchemy import create_engine
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.engine import make_url
from sqlalchemy.orm import sessionmaker

from app.core.config import settings
from app.domains.content.models import Content

engine = create_engine(settings.DIRECT_URL)
Session = sessionmaker(bind=engine)

LOCAL_HOSTS = frozenset({"localhost", "127.0.0.1", "::1", "db"})


def require_local() -> None:
    """평가 스크립트 가드

    평가는 유저마다 임베딩을 읽고 홀드아웃을 지웠다 되돌린다. 한 회에 수백 MB 가 오간다
    Neon 무료 티어 전송량은 월 5GB 라 몇 번 돌리면 프로덕션 DB 가 통째로 막힌다
    """
    if os.getenv("ALLOW_REMOTE_EVAL"):
        return
    host = make_url(settings.DIRECT_URL or settings.DATABASE_URL).host or ""
    if host not in LOCAL_HOSTS:
        raise SystemExit(
            f"DIRECT_URL 이 {host} 를 가리킨다. 평가는 로컬에서 돌린다\n"
            "  docker compose up -d\n"
            "  .env 의 DATABASE_URL / DIRECT_URL 을 localhost:5433 으로"
        )


def upsert(session, row: dict) -> None:
    """id 충돌 시 나머지 컬럼을 새 값으로 덮어씀"""
    stmt = insert(Content).values(**row)
    stmt = stmt.on_conflict_do_update(
        index_elements=["id"],
        set_={k: stmt.excluded[k] for k in row if k != "id"},
    )
    session.execute(stmt)
