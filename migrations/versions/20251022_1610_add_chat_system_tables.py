"""Add chat system tables

Revision ID: 20251022_1610
Revises: 20251021_2050
Create Date: 2025-10-22 16:10:00

채팅 시스템 테이블 생성
- USR_CNVS_SMRY: 대화방 요약
- USR_CNVS: 대화 메시지
- USR_CNVS_REF_DOC_LST: 참조 문서
- USR_CNVS_ADD_QUES_LST: 추천 질문
- USR_UPLD_DOC_MNG: 업로드 파일 관리
"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = '20251022_1610'
down_revision = '20251021_2050'
branch_labels = None
depends_on = None


def upgrade():
    # USR_CNVS_SMRY 테이블 생성 (대화방 요약)
    op.create_table(
        'USR_CNVS_SMRY',
        sa.Column('CNVS_SMRY_ID', sa.Integer(), nullable=False, autoincrement=True, comment='대화방 요약 ID'),
        sa.Column('CNVS_IDT_ID', sa.String(length=100), nullable=False, comment='대화방 ID (고유)'),
        sa.Column('CNVS_SMRY_TXT', sa.Text(), nullable=False, comment='대화 요약 (첫 질문)'),
        sa.Column('REP_CNVS_NM', sa.String(length=500), nullable=True, comment='대화명 (사용자 지정)'),
        sa.Column('USR_ID', sa.String(length=50), nullable=False, comment='사용자 ID'),
        sa.Column('USE_YN', sa.String(length=1), nullable=False, server_default='Y', comment='사용 여부 (Y/N)'),
        sa.Column('REG_DT', sa.DateTime(), nullable=False, server_default=sa.func.current_timestamp(), comment='등록일시'),
        sa.Column('MOD_DT', sa.DateTime(), nullable=True, comment='수정일시'),
        sa.PrimaryKeyConstraint('CNVS_SMRY_ID'),
        sa.UniqueConstraint('CNVS_IDT_ID')
    )
    op.create_index('idx_usr_cnvs_smry_cnvs_idt_id', 'USR_CNVS_SMRY', ['CNVS_IDT_ID'])
    op.create_index('idx_usr_cnvs_smry_usr_id_reg_dt', 'USR_CNVS_SMRY', ['USR_ID', 'REG_DT'])
    op.create_index('idx_usr_cnvs_smry_use_yn', 'USR_CNVS_SMRY', ['USE_YN'])

    # USR_CNVS 테이블 생성 (대화 메시지)
    op.create_table(
        'USR_CNVS',
        sa.Column('CNVS_ID', sa.Integer(), nullable=False, autoincrement=True, comment='대화 ID'),
        sa.Column('CNVS_IDT_ID', sa.String(length=100), nullable=False, comment='대화방 ID (FK)'),
        sa.Column('QUES_TXT', sa.Text(), nullable=False, comment='질문 텍스트'),
        sa.Column('ANS_TXT', sa.Text(), nullable=True, comment='답변 텍스트'),
        sa.Column('TKN_USE_CNT', sa.Integer(), nullable=True, comment='토큰 사용 수'),
        sa.Column('RSP_TIM_MS', sa.Integer(), nullable=True, comment='응답 시간 (밀리초)'),
        sa.Column('SESN_ID', sa.String(length=100), nullable=True, comment='HTTP 세션 ID'),
        sa.Column('USE_YN', sa.String(length=1), nullable=False, server_default='Y', comment='사용 여부 (Y/N)'),
        sa.Column('REG_DT', sa.DateTime(), nullable=False, server_default=sa.func.current_timestamp(), comment='등록일시'),
        sa.Column('MOD_DT', sa.DateTime(), nullable=True, comment='수정일시'),
        sa.ForeignKeyConstraint(['CNVS_IDT_ID'], ['USR_CNVS_SMRY.CNVS_IDT_ID'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('CNVS_ID')
    )
    op.create_index('idx_usr_cnvs_cnvs_idt_id', 'USR_CNVS', ['CNVS_IDT_ID'])
    op.create_index('idx_usr_cnvs_cnvs_idt_id_reg_dt', 'USR_CNVS', ['CNVS_IDT_ID', 'REG_DT'])

    # USR_CNVS_REF_DOC_LST 테이블 생성 (참조 문서)
    op.create_table(
        'USR_CNVS_REF_DOC_LST',
        sa.Column('CNVS_REF_DOC_ID', sa.Integer(), nullable=False, autoincrement=True, comment='참조 문서 ID'),
        sa.Column('CNVS_ID', sa.Integer(), nullable=False, comment='대화 ID (FK)'),
        sa.Column('REF_SEQ', sa.Integer(), nullable=False, comment='참조 순서'),
        sa.Column('ATT_DOC_NM', sa.String(length=500), nullable=False, comment='문서명'),
        sa.Column('DOC_CHNK_TXT', sa.Text(), nullable=False, comment='문서 청크 텍스트'),
        sa.Column('SMLT_RTE', sa.Float(), nullable=False, comment='유사도 점수'),
        sa.Column('REG_DT', sa.DateTime(), nullable=False, server_default=sa.func.current_timestamp(), comment='등록일시'),
        sa.ForeignKeyConstraint(['CNVS_ID'], ['USR_CNVS.CNVS_ID'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('CNVS_REF_DOC_ID')
    )
    op.create_index('idx_usr_cnvs_ref_doc_cnvs_id', 'USR_CNVS_REF_DOC_LST', ['CNVS_ID'])

    # USR_CNVS_ADD_QUES_LST 테이블 생성 (추천 질문)
    op.create_table(
        'USR_CNVS_ADD_QUES_LST',
        sa.Column('CNVS_ADD_QUES_ID', sa.Integer(), nullable=False, autoincrement=True, comment='추천 질문 ID'),
        sa.Column('CNVS_ID', sa.Integer(), nullable=False, comment='대화 ID (FK)'),
        sa.Column('ADD_QUES_SEQ', sa.Integer(), nullable=False, comment='추천 질문 순서'),
        sa.Column('ADD_QUES_TXT', sa.Text(), nullable=False, comment='추천 질문 텍스트'),
        sa.Column('REG_DT', sa.DateTime(), nullable=False, server_default=sa.func.current_timestamp(), comment='등록일시'),
        sa.ForeignKeyConstraint(['CNVS_ID'], ['USR_CNVS.CNVS_ID'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('CNVS_ADD_QUES_ID')
    )
    op.create_index('idx_usr_cnvs_add_ques_cnvs_id', 'USR_CNVS_ADD_QUES_LST', ['CNVS_ID'])

    # USR_UPLD_DOC_MNG 테이블 생성 (업로드 파일 관리)
    op.create_table(
        'USR_UPLD_DOC_MNG',
        sa.Column('UPLD_DOC_ID', sa.Integer(), nullable=False, autoincrement=True, comment='업로드 문서 ID'),
        sa.Column('CNVS_IDT_ID', sa.String(length=100), nullable=False, comment='대화방 ID (FK)'),
        sa.Column('FILE_NM', sa.String(length=500), nullable=False, comment='파일명'),
        sa.Column('FILE_UID', sa.String(length=500), nullable=False, comment='MinIO Object Name (UUID)'),
        sa.Column('FILE_DOWN_URL', sa.String(length=1000), nullable=False, comment='파일 다운로드 URL'),
        sa.Column('FILE_SIZE', sa.BigInteger(), nullable=False, comment='파일 크기 (bytes)'),
        sa.Column('FILE_TYP_CD', sa.String(length=10), nullable=False, comment='파일 타입 (pdf, docx, xlsx, txt, png, jpg)'),
        sa.Column('USR_ID', sa.String(length=50), nullable=False, comment='업로드 사용자 ID'),
        sa.Column('REG_DT', sa.DateTime(), nullable=False, server_default=sa.func.current_timestamp(), comment='등록일시'),
        sa.ForeignKeyConstraint(['CNVS_IDT_ID'], ['USR_CNVS_SMRY.CNVS_IDT_ID'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('UPLD_DOC_ID')
    )
    op.create_index('idx_usr_upld_doc_cnvs_idt_id', 'USR_UPLD_DOC_MNG', ['CNVS_IDT_ID'])
    op.create_index('idx_usr_upld_doc_usr_id', 'USR_UPLD_DOC_MNG', ['USR_ID'])


def downgrade():
    # 역순으로 테이블 삭제
    op.drop_index('idx_usr_upld_doc_usr_id', table_name='USR_UPLD_DOC_MNG')
    op.drop_index('idx_usr_upld_doc_cnvs_idt_id', table_name='USR_UPLD_DOC_MNG')
    op.drop_table('USR_UPLD_DOC_MNG')

    op.drop_index('idx_usr_cnvs_add_ques_cnvs_id', table_name='USR_CNVS_ADD_QUES_LST')
    op.drop_table('USR_CNVS_ADD_QUES_LST')

    op.drop_index('idx_usr_cnvs_ref_doc_cnvs_id', table_name='USR_CNVS_REF_DOC_LST')
    op.drop_table('USR_CNVS_REF_DOC_LST')

    op.drop_index('idx_usr_cnvs_cnvs_idt_id_reg_dt', table_name='USR_CNVS')
    op.drop_index('idx_usr_cnvs_cnvs_idt_id', table_name='USR_CNVS')
    op.drop_table('USR_CNVS')

    op.drop_index('idx_usr_cnvs_smry_use_yn', table_name='USR_CNVS_SMRY')
    op.drop_index('idx_usr_cnvs_smry_usr_id_reg_dt', table_name='USR_CNVS_SMRY')
    op.drop_index('idx_usr_cnvs_smry_cnvs_idt_id', table_name='USR_CNVS_SMRY')
    op.drop_table('USR_CNVS_SMRY')
