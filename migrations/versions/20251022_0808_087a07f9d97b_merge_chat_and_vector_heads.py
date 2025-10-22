"""merge_chat_and_vector_heads

Revision ID: 087a07f9d97b
Revises: ff69bd7d1694, 20251022_1610
Create Date: 2025-10-22 08:08:23.468946

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '087a07f9d97b'
down_revision: Union[str, None] = ('ff69bd7d1694', '20251022_1610')
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass
