"""add_deployments_table

Revision ID: b7c8d9e0f1a2
Revises: a1b2c3d4e5f6
Create Date: 2025-10-22 23:18:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import ARRAY, JSON


# revision identifiers, used by Alembic.
revision: str = 'b7c8d9e0f1a2'
down_revision: Union[str, None] = 'a1b2c3d4e5f6'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Create deployments table
    op.create_table(
        'deployments',
        sa.Column('deployment_id', sa.Integer(), nullable=False, autoincrement=True),
        sa.Column('model_name', sa.String(length=200), nullable=False, comment='모델 이름'),
        sa.Column('model_uri', sa.String(length=500), nullable=True, comment='모델 경로'),
        sa.Column('framework', sa.String(length=50), nullable=True, comment='프레임워크 (vllm, transformers 등)'),
        sa.Column('status', sa.String(length=20), nullable=False, comment='배포 상태 (building, ready, serving, stopped, failed)'),
        sa.Column('gpu_ids', ARRAY(sa.Integer()), nullable=True, comment='사용 중인 GPU ID 목록'),
        sa.Column('port', sa.Integer(), nullable=True, comment='서비스 포트'),
        sa.Column('endpoint_url', sa.String(length=500), nullable=True, comment='엔드포인트 URL'),
        sa.Column('vllm_config', JSON, nullable=True, comment='vLLM 설정 (JSON)'),
        sa.Column('process_id', sa.Integer(), nullable=True, comment='vLLM 서버 프로세스 ID'),
        sa.Column('deployed_by', sa.String(length=100), nullable=True, comment='배포자'),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.PrimaryKeyConstraint('deployment_id')
    )

    # Create indexes
    op.create_index('ix_deployments_deployment_id', 'deployments', ['deployment_id'], unique=False)
    op.create_index('ix_deployments_model_name', 'deployments', ['model_name'], unique=False)
    op.create_index('ix_deployments_status', 'deployments', ['status'], unique=False)


def downgrade() -> None:
    # Drop indexes
    op.drop_index('ix_deployments_status', table_name='deployments')
    op.drop_index('ix_deployments_model_name', table_name='deployments')
    op.drop_index('ix_deployments_deployment_id', table_name='deployments')

    # Drop table
    op.drop_table('deployments')
