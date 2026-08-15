"""add content rating index

Revision ID: 3ed1c63782ed
Revises: 91b16eed607c
Create Date: 2026-08-15 23:30:42.269889

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '3ed1c63782ed'
down_revision: Union[str, Sequence[str], None] = '91b16eed607c'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.create_index('ix_user_contents_content_rating', 'user_contents', ['content_id', 'rating'], unique=False)


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_index('ix_user_contents_content_rating', table_name='user_contents')
