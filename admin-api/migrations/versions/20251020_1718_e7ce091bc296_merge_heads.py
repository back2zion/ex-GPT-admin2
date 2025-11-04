"""merge_heads

Revision ID: e7ce091bc296
Revises: 737d5b88f609, add_conversation_title
Create Date: 2025-10-20 17:18:53.714423

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'e7ce091bc296'
down_revision: Union[str, None] = ('737d5b88f609', 'add_conversation_title')
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass
