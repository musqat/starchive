from collections.abc import Generator

from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from app.core.config import settings

engine = create_engine(
    url=settings.DATABASE_URL,
    pool_pre_ping=True,
    pool_size=1,
    max_overflow=0,
    # DB 가 안 받으면 5초 안에 실패한다. 풀이 1개라 응답을 기다리는 연결 하나가 전부를 막는다
    connect_args={"prepare_threshold": None, "connect_timeout": 5},
)

SessionLocal = sessionmaker(bind=engine, autoflush=False, expire_on_commit=False)


def get_db() -> Generator[Session, None, None]:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
