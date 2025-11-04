"""add finetuning mlops tables

Revision ID: e1f2g3h4i5j6
Revises: d0e1f2g3h4i5
Create Date: 2025-10-30 10:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = 'e1f2g3h4i5j6'
down_revision: Union[str, None] = 'd0e1f2g3h4i5'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Training datasets table
    op.create_table(
        'training_datasets',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('name', sa.String(length=255), nullable=False),
        sa.Column('version', sa.String(length=50), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('format', sa.String(length=50), nullable=True, server_default='jsonl'),
        sa.Column('file_path', sa.Text(), nullable=False),
        sa.Column('total_samples', sa.Integer(), nullable=True),
        sa.Column('train_samples', sa.Integer(), nullable=True),
        sa.Column('val_samples', sa.Integer(), nullable=True),
        sa.Column('test_samples', sa.Integer(), nullable=True),
        sa.Column('dataset_metadata', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('quality_score', sa.Float(), nullable=True),
        sa.Column('created_by', sa.Integer(), nullable=True),
        sa.Column('created_at', sa.TIMESTAMP(), server_default=sa.text('now()'), nullable=True),
        sa.Column('status', sa.String(length=50), nullable=True, server_default='active'),
        sa.ForeignKeyConstraint(['created_by'], ['users.id'], ),
        sa.PrimaryKeyConstraint('id'),
        comment='Fine-tuning용 학습 데이터셋'
    )
    op.create_index(op.f('ix_training_datasets_id'), 'training_datasets', ['id'], unique=False)
    op.create_index(op.f('ix_training_datasets_name'), 'training_datasets', ['name'], unique=False)

    # Dataset quality logs table
    op.create_table(
        'dataset_quality_logs',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('dataset_id', sa.Integer(), nullable=True),
        sa.Column('check_type', sa.String(length=100), nullable=True),
        sa.Column('passed', sa.Boolean(), nullable=True),
        sa.Column('issues', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('created_at', sa.TIMESTAMP(), server_default=sa.text('now()'), nullable=True),
        sa.ForeignKeyConstraint(['dataset_id'], ['training_datasets.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        comment='데이터셋 품질 검증 로그'
    )
    op.create_index(op.f('ix_dataset_quality_logs_id'), 'dataset_quality_logs', ['id'], unique=False)

    # Finetuning jobs table
    op.create_table(
        'finetuning_jobs',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('job_name', sa.String(length=255), nullable=False),
        sa.Column('base_model', sa.String(length=255), nullable=False),
        sa.Column('dataset_id', sa.Integer(), nullable=True),
        sa.Column('method', sa.String(length=50), nullable=False),
        sa.Column('hyperparameters', postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column('mlflow_run_id', sa.String(length=255), nullable=True),
        sa.Column('status', sa.String(length=50), nullable=True, server_default='pending'),
        sa.Column('start_time', sa.TIMESTAMP(), nullable=True),
        sa.Column('end_time', sa.TIMESTAMP(), nullable=True),
        sa.Column('output_dir', sa.Text(), nullable=True),
        sa.Column('checkpoint_dir', sa.Text(), nullable=True),
        sa.Column('logs_path', sa.Text(), nullable=True),
        sa.Column('gpu_ids', sa.String(length=50), nullable=True),
        sa.Column('error_message', sa.Text(), nullable=True),
        sa.Column('created_by', sa.Integer(), nullable=True),
        sa.Column('created_at', sa.TIMESTAMP(), server_default=sa.text('now()'), nullable=True),
        sa.ForeignKeyConstraint(['created_by'], ['users.id'], ),
        sa.ForeignKeyConstraint(['dataset_id'], ['training_datasets.id'], ),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('job_name'),
        comment='Fine-tuning 작업'
    )
    op.create_index(op.f('ix_finetuning_jobs_id'), 'finetuning_jobs', ['id'], unique=False)
    op.create_index(op.f('ix_finetuning_jobs_job_name'), 'finetuning_jobs', ['job_name'], unique=True)
    op.create_index(op.f('ix_finetuning_jobs_status'), 'finetuning_jobs', ['status'], unique=False)

    # Training checkpoints table
    op.create_table(
        'training_checkpoints',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('job_id', sa.Integer(), nullable=True),
        sa.Column('checkpoint_name', sa.String(length=255), nullable=True),
        sa.Column('step', sa.Integer(), nullable=True),
        sa.Column('epoch', sa.Float(), nullable=True),
        sa.Column('metrics', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('file_path', sa.Text(), nullable=True),
        sa.Column('file_size_gb', sa.Float(), nullable=True),
        sa.Column('created_at', sa.TIMESTAMP(), server_default=sa.text('now()'), nullable=True),
        sa.ForeignKeyConstraint(['job_id'], ['finetuning_jobs.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        comment='Fine-tuning 체크포인트'
    )
    op.create_index(op.f('ix_training_checkpoints_id'), 'training_checkpoints', ['id'], unique=False)

    # Model registry table
    op.create_table(
        'model_registry',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('model_name', sa.String(length=255), nullable=False),
        sa.Column('version', sa.String(length=50), nullable=False),
        sa.Column('base_model', sa.String(length=255), nullable=True),
        sa.Column('finetuning_job_id', sa.Integer(), nullable=True),
        sa.Column('model_path', sa.Text(), nullable=False),
        sa.Column('model_format', sa.String(length=50), nullable=True, server_default='huggingface'),
        sa.Column('model_size_gb', sa.Float(), nullable=True),
        sa.Column('status', sa.String(length=50), nullable=True, server_default='staging'),
        sa.Column('deployment_config', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('mlflow_model_uri', sa.Text(), nullable=True),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('tags', postgresql.ARRAY(sa.String()), nullable=True),
        sa.Column('created_by', sa.Integer(), nullable=True),
        sa.Column('created_at', sa.TIMESTAMP(), server_default=sa.text('now()'), nullable=True),
        sa.Column('updated_at', sa.TIMESTAMP(), server_default=sa.text('now()'), nullable=True),
        sa.ForeignKeyConstraint(['created_by'], ['users.id'], ),
        sa.ForeignKeyConstraint(['finetuning_job_id'], ['finetuning_jobs.id'], ),
        sa.PrimaryKeyConstraint('id'),
        comment='Fine-tuned 모델 레지스트리'
    )
    op.create_index(op.f('ix_model_registry_id'), 'model_registry', ['id'], unique=False)
    op.create_index(op.f('ix_model_registry_model_name'), 'model_registry', ['model_name'], unique=False)
    op.create_index(op.f('ix_model_registry_status'), 'model_registry', ['status'], unique=False)

    # Model evaluations table
    op.create_table(
        'model_evaluations',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('job_id', sa.Integer(), nullable=True),
        sa.Column('checkpoint_id', sa.Integer(), nullable=True),
        sa.Column('eval_dataset_id', sa.Integer(), nullable=True),
        sa.Column('metrics', postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column('test_cases', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('evaluated_at', sa.TIMESTAMP(), server_default=sa.text('now()'), nullable=True),
        sa.Column('evaluator', sa.Integer(), nullable=True),
        sa.ForeignKeyConstraint(['checkpoint_id'], ['training_checkpoints.id'], ),
        sa.ForeignKeyConstraint(['eval_dataset_id'], ['training_datasets.id'], ),
        sa.ForeignKeyConstraint(['evaluator'], ['users.id'], ),
        sa.ForeignKeyConstraint(['job_id'], ['finetuning_jobs.id'], ),
        sa.PrimaryKeyConstraint('id'),
        comment='모델 평가 결과'
    )
    op.create_index(op.f('ix_model_evaluations_id'), 'model_evaluations', ['id'], unique=False)

    # Model benchmarks table
    op.create_table(
        'model_benchmarks',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('model_id', sa.Integer(), nullable=True),
        sa.Column('benchmark_name', sa.String(length=255), nullable=True),
        sa.Column('score', sa.Float(), nullable=True),
        sa.Column('details', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('benchmark_date', sa.TIMESTAMP(), server_default=sa.text('now()'), nullable=True),
        sa.ForeignKeyConstraint(['model_id'], ['model_registry.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        comment='모델 벤치마크 결과'
    )
    op.create_index(op.f('ix_model_benchmarks_id'), 'model_benchmarks', ['id'], unique=False)

    # A/B experiments table
    op.create_table(
        'ab_experiments',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('experiment_name', sa.String(length=255), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('model_a_id', sa.Integer(), nullable=True),
        sa.Column('model_b_id', sa.Integer(), nullable=True),
        sa.Column('traffic_split', postgresql.JSONB(astext_type=sa.Text()), nullable=True, server_default='{"a": 0.5, "b": 0.5}'),
        sa.Column('status', sa.String(length=50), nullable=True, server_default='running'),
        sa.Column('start_date', sa.TIMESTAMP(), server_default=sa.text('now()'), nullable=True),
        sa.Column('end_date', sa.TIMESTAMP(), nullable=True),
        sa.Column('target_samples', sa.Integer(), nullable=True, server_default='200'),
        sa.Column('success_metric', sa.String(length=100), nullable=True, server_default='user_rating'),
        sa.Column('created_by', sa.Integer(), nullable=True),
        sa.ForeignKeyConstraint(['created_by'], ['users.id'], ),
        sa.ForeignKeyConstraint(['model_a_id'], ['model_registry.id'], ),
        sa.ForeignKeyConstraint(['model_b_id'], ['model_registry.id'], ),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('experiment_name'),
        comment='A/B 테스트 실험'
    )
    op.create_index(op.f('ix_ab_experiments_id'), 'ab_experiments', ['id'], unique=False)
    op.create_index(op.f('ix_ab_experiments_experiment_name'), 'ab_experiments', ['experiment_name'], unique=True)
    op.create_index(op.f('ix_ab_experiments_status'), 'ab_experiments', ['status'], unique=False)

    # A/B test logs table
    op.create_table(
        'ab_test_logs',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('experiment_id', sa.Integer(), nullable=True),
        sa.Column('user_id', sa.Integer(), nullable=True),
        sa.Column('session_id', sa.String(length=255), nullable=True),
        sa.Column('variant', sa.String(length=10), nullable=True),
        sa.Column('model_id', sa.Integer(), nullable=True),
        sa.Column('query', sa.Text(), nullable=True),
        sa.Column('response', sa.Text(), nullable=True),
        sa.Column('response_time_ms', sa.Integer(), nullable=True),
        sa.Column('user_rating', sa.Integer(), nullable=True),
        sa.Column('user_feedback', sa.Text(), nullable=True),
        sa.Column('created_at', sa.TIMESTAMP(), server_default=sa.text('now()'), nullable=True),
        sa.ForeignKeyConstraint(['experiment_id'], ['ab_experiments.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['model_id'], ['model_registry.id'], ),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
        sa.PrimaryKeyConstraint('id'),
        comment='A/B 테스트 로그'
    )
    op.create_index(op.f('ix_ab_test_logs_id'), 'ab_test_logs', ['id'], unique=False)
    op.create_index(op.f('ix_ab_test_logs_session_id'), 'ab_test_logs', ['session_id'], unique=False)
    op.create_index(op.f('ix_ab_test_logs_created_at'), 'ab_test_logs', ['created_at'], unique=False)

    # A/B test results table
    op.create_table(
        'ab_test_results',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('experiment_id', sa.Integer(), nullable=True),
        sa.Column('variant', sa.String(length=10), nullable=True),
        sa.Column('total_samples', sa.Integer(), nullable=True),
        sa.Column('avg_rating', sa.Float(), nullable=True),
        sa.Column('avg_response_time_ms', sa.Float(), nullable=True),
        sa.Column('confidence_interval', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('statistical_significance', sa.Boolean(), nullable=True),
        sa.Column('winner', sa.Boolean(), nullable=True),
        sa.Column('calculated_at', sa.TIMESTAMP(), server_default=sa.text('now()'), nullable=True),
        sa.ForeignKeyConstraint(['experiment_id'], ['ab_experiments.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        comment='A/B 테스트 결과 (통계)'
    )
    op.create_index(op.f('ix_ab_test_results_id'), 'ab_test_results', ['id'], unique=False)


def downgrade() -> None:
    # Drop tables in reverse order
    op.drop_index(op.f('ix_ab_test_results_id'), table_name='ab_test_results')
    op.drop_table('ab_test_results')

    op.drop_index(op.f('ix_ab_test_logs_created_at'), table_name='ab_test_logs')
    op.drop_index(op.f('ix_ab_test_logs_session_id'), table_name='ab_test_logs')
    op.drop_index(op.f('ix_ab_test_logs_id'), table_name='ab_test_logs')
    op.drop_table('ab_test_logs')

    op.drop_index(op.f('ix_ab_experiments_status'), table_name='ab_experiments')
    op.drop_index(op.f('ix_ab_experiments_experiment_name'), table_name='ab_experiments')
    op.drop_index(op.f('ix_ab_experiments_id'), table_name='ab_experiments')
    op.drop_table('ab_experiments')

    op.drop_index(op.f('ix_model_benchmarks_id'), table_name='model_benchmarks')
    op.drop_table('model_benchmarks')

    op.drop_index(op.f('ix_model_evaluations_id'), table_name='model_evaluations')
    op.drop_table('model_evaluations')

    op.drop_index(op.f('ix_model_registry_status'), table_name='model_registry')
    op.drop_index(op.f('ix_model_registry_model_name'), table_name='model_registry')
    op.drop_index(op.f('ix_model_registry_id'), table_name='model_registry')
    op.drop_table('model_registry')

    op.drop_index(op.f('ix_training_checkpoints_id'), table_name='training_checkpoints')
    op.drop_table('training_checkpoints')

    op.drop_index(op.f('ix_finetuning_jobs_status'), table_name='finetuning_jobs')
    op.drop_index(op.f('ix_finetuning_jobs_job_name'), table_name='finetuning_jobs')
    op.drop_index(op.f('ix_finetuning_jobs_id'), table_name='finetuning_jobs')
    op.drop_table('finetuning_jobs')

    op.drop_index(op.f('ix_dataset_quality_logs_id'), table_name='dataset_quality_logs')
    op.drop_table('dataset_quality_logs')

    op.drop_index(op.f('ix_training_datasets_name'), table_name='training_datasets')
    op.drop_index(op.f('ix_training_datasets_id'), table_name='training_datasets')
    op.drop_table('training_datasets')
