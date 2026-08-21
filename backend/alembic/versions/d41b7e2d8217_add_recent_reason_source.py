"""add recent reason source

Revision ID: d41b7e2d8217
Revises: c62aae84f2d4
Create Date: 2026-08-22 00:07:44.626942

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'd41b7e2d8217'
down_revision: Union[str, Sequence[str], None] = 'c62aae84f2d4'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # 신작 자리는 LLM 실패가 아니라 정상 경로다. TEMPLATE 과 섞이면 폴백 집계가 오염된다
    op.execute("ALTER TYPE reason_source ADD VALUE IF NOT EXISTS 'RECENT'")


def downgrade() -> None:
    """Downgrade schema."""
    # Postgres 는 enum 값을 못 지운다. 타입을 새로 만들어 갈아끼워야 한다
    op.execute("UPDATE recommendations SET reason_source = 'TEMPLATE' WHERE reason_source = 'RECENT'")
    op.execute("ALTER TYPE reason_source RENAME TO reason_source_old")
    op.execute("CREATE TYPE reason_source AS ENUM ('LLM', 'TEMPLATE')")
    op.execute(
        "ALTER TABLE recommendations ALTER COLUMN reason_source"
        " TYPE reason_source USING reason_source::text::reason_source"
    )
    op.execute("DROP TYPE reason_source_old")
