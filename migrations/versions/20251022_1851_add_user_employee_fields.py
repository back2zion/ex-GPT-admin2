"""add_user_employee_fields

Revision ID: a1b2c3d4e5f6
Revises: f3a8b9c4d5e6
Create Date: 2025-10-22 18:51:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'a1b2c3d4e5f6'
down_revision: Union[str, None] = 'f3a8b9c4d5e6'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Add employee_number and job_category to users table
    op.add_column('users', sa.Column('employee_number', sa.String(length=50), nullable=True, comment='사번'))
    op.add_column('users', sa.Column('job_category', sa.String(length=50), nullable=True, comment='직종 (예: 사무, 기술, 관리)'))
    op.create_index('ix_users_employee_number', 'users', ['employee_number'], unique=True)


def downgrade() -> None:
    # Remove fields from users table
    op.drop_index('ix_users_employee_number', table_name='users')
    op.drop_column('users', 'job_category')
    op.drop_column('users', 'employee_number')
