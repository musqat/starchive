"""add memo to user_contents

Revision ID: a41666ee666b
Revises: eb9b60d2f89b
Create Date: 2026-08-14 22:51:54.568641

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'a41666ee666b'
down_revision: Union[str, Sequence[str], None] = 'eb9b60d2f89b'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.add_column('user_contents', sa.Column('memo', sa.String(length=500), nullable=True))
    # 기존 행을 채우려면 server_default 가 필요하다
    op.add_column(
        'user_contents',
        sa.Column('memo_public', sa.Boolean(), nullable=False, server_default=sa.false()),
    )
    op.create_index(
        'ix_user_contents_public_memo', 'user_contents', ['content_id', 'memo_public'], unique=False
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_index('ix_user_contents_public_memo', table_name='user_contents')
    op.drop_column('user_contents', 'memo_public')
    op.drop_column('user_contents', 'memo')
