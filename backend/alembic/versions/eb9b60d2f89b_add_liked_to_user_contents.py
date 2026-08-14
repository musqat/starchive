"""add liked to user_contents

Revision ID: eb9b60d2f89b
Revises: d36455f5f724
Create Date: 2026-08-14 21:33:04.893465

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'eb9b60d2f89b'
down_revision: Union[str, Sequence[str], None] = 'd36455f5f724'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # 기존 행을 채우려면 server_default 가 필요하다
    op.add_column(
        'user_contents',
        sa.Column('liked', sa.Boolean(), nullable=False, server_default=sa.false()),
    )
    op.create_index('ix_user_contents_liked', 'user_contents', ['user_id', 'liked'], unique=False)


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_index('ix_user_contents_liked', table_name='user_contents')
    op.drop_column('user_contents', 'liked')
