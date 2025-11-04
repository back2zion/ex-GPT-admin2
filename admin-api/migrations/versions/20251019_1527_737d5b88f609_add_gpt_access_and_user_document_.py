"""Add GPT access and user document permissions

Revision ID: 737d5b88f609
Revises:
Create Date: 2025-10-19 15:27:17.434104

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '737d5b88f609'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Add GPT access columns to users table
    op.add_column('users', sa.Column('gpt_access_granted', sa.Boolean(), server_default='false', nullable=False, comment='GPT 접근 허용 여부'))
    op.add_column('users', sa.Column('allowed_model', sa.String(length=100), nullable=True, comment='허용된 모델명'))
    op.add_column('users', sa.Column('last_login_at', sa.DateTime(timezone=True), nullable=True, comment='마지막 로그인 시간'))

    # Create access_requests table for GPT access requests
    op.create_table('access_requests',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False, comment='신청 사용자'),
        sa.Column('status', sa.Enum('PENDING', 'APPROVED', 'REJECTED', name='accessrequeststatus'), nullable=False, comment='신청 상태'),
        sa.Column('requested_at', sa.DateTime(timezone=True), nullable=False, comment='신청 일시'),
        sa.Column('processed_at', sa.DateTime(timezone=True), nullable=True, comment='처리 일시'),
        sa.Column('processed_by', sa.Integer(), nullable=True, comment='처리자'),
        sa.Column('reject_reason', sa.String(length=500), nullable=True, comment='거부 사유'),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(['processed_by'], ['users.id'], ),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_access_requests_id'), 'access_requests', ['id'], unique=False)

    # Create user_document_permissions table for user-department document access
    op.create_table('user_document_permissions',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False, comment='사용자 ID'),
        sa.Column('department_id', sa.Integer(), nullable=False, comment='접근 가능 부서 ID'),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(['department_id'], ['departments.id'], ),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_user_document_permissions_id'), 'user_document_permissions', ['id'], unique=False)


def downgrade() -> None:
    # Remove user_document_permissions table
    op.drop_index(op.f('ix_user_document_permissions_id'), table_name='user_document_permissions')
    op.drop_table('user_document_permissions')

    # Remove access_requests table
    op.drop_index(op.f('ix_access_requests_id'), table_name='access_requests')
    op.drop_table('access_requests')

    # Remove GPT access columns from users table
    op.drop_column('users', 'last_login_at')
    op.drop_column('users', 'allowed_model')
    op.drop_column('users', 'gpt_access_granted')
