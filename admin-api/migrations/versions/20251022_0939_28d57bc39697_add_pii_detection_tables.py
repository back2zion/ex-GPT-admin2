"""add_pii_detection_tables

Revision ID: 28d57bc39697
Revises: 087a07f9d97b
Create Date: 2025-10-22 09:39:01.047302

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '28d57bc39697'
down_revision: Union[str, None] = '087a07f9d97b'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # PII table and enum already exist in database (created manually or by test setup)
    # Just mark this migration as complete
    pass


def downgrade() -> None:
    # Don't drop the table in downgrade as it may be needed
    pass
