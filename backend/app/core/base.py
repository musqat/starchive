from sqlalchemy.orm import DeclarativeBase


class Base(DeclarativeBase):
    """
    모든 모델의 공통 베이스.
    Alembic 의 target_metadata 가 이걸 확인
    """
