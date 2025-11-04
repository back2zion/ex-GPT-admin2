"""merge_heads_before_stt

Revision ID: 51d68a126cf7
Revises: 737d5b88f609, add_conversation_title
Create Date: 2025-10-21 13:14:56.305461

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '51d68a126cf7'
down_revision: Union[str, None] = ('737d5b88f609', 'add_conversation_title')
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass
