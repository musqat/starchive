"""seed users and float rating

Revision ID: 91b16eed607c
Revises: a41666ee666b
Create Date: 2026-08-15 09:31:47.452570

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '91b16eed607c'
down_revision: Union[str, Sequence[str], None] = 'a41666ee666b'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # 값은 그대로다. 4 → 4.0
    op.alter_column('user_contents', 'rating',
               existing_type=sa.INTEGER(),
               type_=sa.Float(),
               existing_nullable=True)
    # 기존 행을 채우려면 server_default 가 필요하다
    op.add_column(
        'users',
        sa.Column('is_seed', sa.Boolean(), nullable=False, server_default=sa.false()),
    )


def downgrade() -> None:
    """Downgrade schema."""

    op.drop_column('users', 'is_seed')
    op.alter_column('user_contents', 'rating',
               existing_type=sa.Float(),
               type_=sa.INTEGER(),
               existing_nullable=True)

