"""Add STT system tables

Revision ID: 20251021_2050
Revises: e7ce091bc296
Create Date: 2025-10-21 20:50:00

STT 음성 전사 시스템 테이블 생성
- stt_batches: 배치 작업 관리
- stt_transcriptions: 전사 결과 저장
- stt_summaries: 요약 및 회의록
- stt_email_logs: 이메일 송출 내역
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '20251021_2050'
down_revision = '51d68a126cf7'
branch_labels = None
depends_on = None


def upgrade():
    # stt_batches 테이블 생성
    op.create_table(
        'stt_batches',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(length=255), nullable=False, comment='배치 작업 이름'),
        sa.Column('description', sa.Text(), nullable=True, comment='배치 작업 설명'),
        sa.Column('source_path', sa.String(length=500), nullable=False, comment='음성파일 경로 (S3/MinIO/로컬)'),
        sa.Column('file_pattern', sa.String(length=100), nullable=True, comment='파일 패턴 (예: *.mp3, *.wav)'),
        sa.Column('total_files', sa.Integer(), nullable=True, comment='총 파일 개수'),
        sa.Column('status', sa.String(length=20), nullable=False, comment='배치 상태: pending, processing, completed, failed, paused'),
        sa.Column('priority', sa.String(length=10), nullable=True, comment='우선순위: low, normal, high, urgent'),
        sa.Column('completed_files', sa.Integer(), nullable=True, comment='완료된 파일 수'),
        sa.Column('failed_files', sa.Integer(), nullable=True, comment='실패한 파일 수'),
        sa.Column('avg_processing_time', sa.Float(), nullable=True, comment='평균 처리 시간 (초)'),
        sa.Column('estimated_duration', sa.Integer(), nullable=True, comment='예상 소요 시간 (초)'),
        sa.Column('started_at', sa.DateTime(), nullable=True, comment='시작 시간'),
        sa.Column('completed_at', sa.DateTime(), nullable=True, comment='완료 시간'),
        sa.Column('created_by', sa.String(length=100), nullable=False, comment='생성자 (user_id)'),
        sa.Column('notify_emails', postgresql.ARRAY(sa.String()), nullable=True, comment='알림 받을 이메일 목록'),
        sa.Column('config', postgresql.JSONB(astext_type=sa.Text()), nullable=True, comment='배치 설정 (JSON)'),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_stt_batches_id'), 'stt_batches', ['id'], unique=False)

    # stt_transcriptions 테이블 생성
    op.create_table(
        'stt_transcriptions',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('batch_id', sa.Integer(), nullable=False),
        sa.Column('audio_file_path', sa.String(length=500), nullable=False, comment='음성파일 경로'),
        sa.Column('audio_file_size', sa.BigInteger(), nullable=True, comment='파일 크기 (bytes)'),
        sa.Column('audio_duration', sa.Float(), nullable=True, comment='음성 길이 (초)'),
        sa.Column('transcription_text', sa.Text(), nullable=False, comment='전사된 텍스트'),
        sa.Column('transcription_confidence', sa.Float(), nullable=True, comment='전사 신뢰도 (0.0 ~ 1.0)'),
        sa.Column('language_code', sa.String(length=10), nullable=True, comment='언어 코드'),
        sa.Column('speaker_labels', postgresql.JSONB(astext_type=sa.Text()), nullable=True, comment='화자 레이블 매핑'),
        sa.Column('segments', postgresql.JSONB(astext_type=sa.Text()), nullable=True, comment='타임스탬프 세그먼트'),
        sa.Column('processing_duration', sa.Float(), nullable=True, comment='처리 소요 시간 (초)'),
        sa.Column('stt_engine', sa.String(length=50), nullable=True, comment='STT 엔진'),
        sa.Column('status', sa.String(length=20), nullable=True, comment='상태: pending, processing, success, failed, partial'),
        sa.Column('error_message', sa.Text(), nullable=True, comment='에러 메시지'),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['batch_id'], ['stt_batches.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('audio_file_path')
    )
    op.create_index(op.f('ix_stt_transcriptions_audio_file_path'), 'stt_transcriptions', ['audio_file_path'], unique=False)
    op.create_index(op.f('ix_stt_transcriptions_batch_id'), 'stt_transcriptions', ['batch_id'], unique=False)
    op.create_index(op.f('ix_stt_transcriptions_id'), 'stt_transcriptions', ['id'], unique=False)

    # stt_summaries 테이블 생성
    op.create_table(
        'stt_summaries',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('transcription_id', sa.Integer(), nullable=False),
        sa.Column('summary_text', sa.Text(), nullable=False, comment='요약 텍스트'),
        sa.Column('summary_level', sa.String(length=20), nullable=True, comment='요약 레벨: brief, normal, detailed'),
        sa.Column('keywords', postgresql.ARRAY(sa.String()), nullable=True, comment='핵심 키워드 배열'),
        sa.Column('action_items', postgresql.JSONB(astext_type=sa.Text()), nullable=True, comment='액션 아이템'),
        sa.Column('meeting_title', sa.String(length=255), nullable=True, comment='회의 제목'),
        sa.Column('meeting_date', sa.DateTime(), nullable=True, comment='회의 날짜'),
        sa.Column('attendees', postgresql.ARRAY(sa.String()), nullable=True, comment='참석자 목록'),
        sa.Column('llm_model', sa.String(length=50), nullable=True, comment='사용된 LLM 모델'),
        sa.Column('tokens_used', sa.Integer(), nullable=True, comment='사용된 토큰 수'),
        sa.Column('generation_duration', sa.Float(), nullable=True, comment='요약 생성 소요 시간 (초)'),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['transcription_id'], ['stt_transcriptions.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('transcription_id')
    )
    op.create_index(op.f('ix_stt_summaries_id'), 'stt_summaries', ['id'], unique=False)
    op.create_index(op.f('ix_stt_summaries_transcription_id'), 'stt_summaries', ['transcription_id'], unique=False)

    # stt_email_logs 테이블 생성
    op.create_table(
        'stt_email_logs',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('summary_id', sa.Integer(), nullable=False),
        sa.Column('recipient_email', sa.String(length=255), nullable=False, comment='수신자 이메일'),
        sa.Column('recipient_name', sa.String(length=100), nullable=True, comment='수신자 이름'),
        sa.Column('cc_emails', postgresql.ARRAY(sa.String()), nullable=True, comment='참조(CC) 이메일 목록'),
        sa.Column('subject', sa.String(length=500), nullable=True, comment='이메일 제목'),
        sa.Column('status', sa.String(length=20), nullable=False, comment='상태: pending, sent, failed, bounced'),
        sa.Column('sent_at', sa.DateTime(), nullable=True, comment='발송 시간'),
        sa.Column('delivery_status', sa.String(length=50), nullable=True, comment='배달 상태'),
        sa.Column('error_message', sa.Text(), nullable=True, comment='에러 메시지'),
        sa.Column('retry_count', sa.Integer(), nullable=True, comment='재시도 횟수'),
        sa.Column('email_provider', sa.String(length=50), nullable=True, comment='이메일 제공자'),
        sa.Column('message_id', sa.String(length=255), nullable=True, comment='이메일 서비스 제공자 Message ID'),
        sa.Column('attachments', postgresql.JSONB(astext_type=sa.Text()), nullable=True, comment='첨부파일 정보'),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['summary_id'], ['stt_summaries.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_stt_email_logs_id'), 'stt_email_logs', ['id'], unique=False)
    op.create_index(op.f('ix_stt_email_logs_recipient_email'), 'stt_email_logs', ['recipient_email'], unique=False)
    op.create_index(op.f('ix_stt_email_logs_summary_id'), 'stt_email_logs', ['summary_id'], unique=False)


def downgrade():
    # 역순으로 테이블 삭제
    op.drop_index(op.f('ix_stt_email_logs_summary_id'), table_name='stt_email_logs')
    op.drop_index(op.f('ix_stt_email_logs_recipient_email'), table_name='stt_email_logs')
    op.drop_index(op.f('ix_stt_email_logs_id'), table_name='stt_email_logs')
    op.drop_table('stt_email_logs')

    op.drop_index(op.f('ix_stt_summaries_transcription_id'), table_name='stt_summaries')
    op.drop_index(op.f('ix_stt_summaries_id'), table_name='stt_summaries')
    op.drop_table('stt_summaries')

    op.drop_index(op.f('ix_stt_transcriptions_id'), table_name='stt_transcriptions')
    op.drop_index(op.f('ix_stt_transcriptions_batch_id'), table_name='stt_transcriptions')
    op.drop_index(op.f('ix_stt_transcriptions_audio_file_path'), table_name='stt_transcriptions')
    op.drop_table('stt_transcriptions')

    op.drop_index(op.f('ix_stt_batches_id'), table_name='stt_batches')
    op.drop_table('stt_batches')
