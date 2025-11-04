"""add_is_deleted_to_usage_history

Revision ID: c9d8e7f6g5h4
Revises: b7c8d9e0f1a2
Create Date: 2025-10-23 04:40:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'c9d8e7f6g5h4'
down_revision: Union[str, None] = 'b7c8d9e0f1a2'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Add is_deleted column to usage_history table
    op.add_column('usage_history', sa.Column('is_deleted', sa.Boolean(), nullable=False, server_default='false', comment='소프트 딜리트 플래그'))
    op.add_column('usage_history', sa.Column('deleted_at', sa.DateTime(timezone=True), nullable=True, comment='삭제 시간'))

    # Add index for filtering deleted records
    op.create_index('ix_usage_history_is_deleted', 'usage_history', ['is_deleted'])


def downgrade() -> None:
    # Remove index and columns
    op.drop_index('ix_usage_history_is_deleted', table_name='usage_history')
    op.drop_column('usage_history', 'deleted_at')
    op.drop_column('usage_history', 'is_deleted')
