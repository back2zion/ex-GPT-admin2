"""add_user_org_and_category_fields

Revision ID: f3a8b9c4d5e6
Revises: 28d57bc39697
Create Date: 2025-10-22 18:42:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'f3a8b9c4d5e6'
down_revision: Union[str, None] = '28d57bc39697'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Add category fields to usage_history table
    op.add_column('usage_history', sa.Column('main_category', sa.String(length=50), nullable=True, comment='대분류: 경영분야, 기술분야, 경영/기술 외, 미분류'))
    op.add_column('usage_history', sa.Column('sub_category', sa.String(length=50), nullable=True, comment='소분류: 세부 카테고리'))
    op.create_index('ix_usage_history_main_category', 'usage_history', ['main_category'], unique=False)
    op.create_index('ix_usage_history_sub_category', 'usage_history', ['sub_category'], unique=False)

    # Add organization fields to users table
    op.add_column('users', sa.Column('position', sa.String(length=50), nullable=True, comment='직급 (예: 사원, 대리, 과장, 차장, 부장)'))
    op.add_column('users', sa.Column('rank', sa.String(length=50), nullable=True, comment='직위 (예: 팀원, 팀장, 본부장)'))
    op.add_column('users', sa.Column('team', sa.String(length=100), nullable=True, comment='팀명/부서명'))
    op.add_column('users', sa.Column('join_year', sa.Integer(), nullable=True, comment='입사년도'))


def downgrade() -> None:
    # Remove fields from users table
    op.drop_column('users', 'join_year')
    op.drop_column('users', 'team')
    op.drop_column('users', 'rank')
    op.drop_column('users', 'position')

    # Remove fields from usage_history table
    op.drop_index('ix_usage_history_sub_category', table_name='usage_history')
    op.drop_index('ix_usage_history_main_category', table_name='usage_history')
    op.drop_column('usage_history', 'sub_category')
    op.drop_column('usage_history', 'main_category')
