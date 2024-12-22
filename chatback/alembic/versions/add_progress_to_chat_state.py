"""add progress to chat state

Revision ID: 7850c9079d32
Revises: 6850c9079d31
Create Date: 2024-03-20 10:00:00.000000

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = '7850c9079d32'
down_revision: Union[str, None] = '6850c9079d31'  # Previous migration ID
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

def upgrade() -> None:
    op.add_column('chat_state', sa.Column('progress', sa.Float(), nullable=True))

def downgrade() -> None:
    op.drop_column('chat_state', 'progress') 