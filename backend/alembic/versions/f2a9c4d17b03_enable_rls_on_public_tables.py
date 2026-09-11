"""enable rls on public tables

Revision ID: f2a9c4d17b03
Revises: d41b7e2d8217
Create Date: 2026-09-11 14:10:00.000000

"""
from typing import Sequence, Union

from alembic import op


# revision identifiers, used by Alembic.
revision: str = 'f2a9c4d17b03'
down_revision: Union[str, Sequence[str], None] = 'd41b7e2d8217'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

# Supabase 는 public 스키마를 PostgREST 로도 연다. anon 키만 있으면 이 테이블들을 REST 로 읽고 쓴다.
# 앱은 그 경로를 안 쓴다. RLS 를 정책 없이 켜면 anon·authenticated 는 0행, 테이블 소유자(앱)는 그대로
TABLES = ("users", "contents", "user_contents", "recommendations", "alembic_version")


def upgrade() -> None:
    """Upgrade schema."""
    for table in TABLES:
        op.execute(f"ALTER TABLE {table} ENABLE ROW LEVEL SECURITY")


def downgrade() -> None:
    """Downgrade schema."""
    for table in TABLES:
        op.execute(f"ALTER TABLE {table} DISABLE ROW LEVEL SECURITY")
