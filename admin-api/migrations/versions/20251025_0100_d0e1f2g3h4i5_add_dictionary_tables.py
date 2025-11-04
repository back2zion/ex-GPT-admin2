"""add_dictionary_tables

Revision ID: d0e1f2g3h4i5
Revises: c9d8e7f6g5h4
Create Date: 2025-10-25 01:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'd0e1f2g3h4i5'
down_revision: Union[str, None] = 'c9d8e7f6g5h4'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Create dictionary table
    op.create_table(
        'dictionary',
        sa.Column('dict_id', sa.Integer(), autoincrement=True, nullable=False, comment='사전 ID'),
        sa.Column('dict_type', sa.Enum('synonym', 'user', name='dicttype'), nullable=False, comment='사전 종류 (synonym: 동의어사전, user: 사용자사전)'),
        sa.Column('dict_name', sa.String(length=200), nullable=False, comment='사전명'),
        sa.Column('dict_desc', sa.Text(), nullable=True, comment='사전 설명'),
        sa.Column('use_yn', sa.Boolean(), nullable=False, server_default='true', comment='사용 여부'),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.PrimaryKeyConstraint('dict_id')
    )
    op.create_index('ix_dictionary_dict_type', 'dictionary', ['dict_type'])
    op.create_index('ix_dictionary_use_yn', 'dictionary', ['use_yn'])

    # Create dictionary_term table
    op.create_table(
        'dictionary_term',
        sa.Column('term_id', sa.Integer(), autoincrement=True, nullable=False, comment='용어 ID'),
        sa.Column('dict_id', sa.Integer(), nullable=False, comment='사전 ID'),
        sa.Column('main_term', sa.String(length=200), nullable=False, comment='정식명칭 (예: 기획재정부)'),
        sa.Column('main_alias', sa.String(length=200), nullable=True, comment='주요약칭 (예: 기재부)'),
        sa.Column('alias_1', sa.String(length=200), nullable=True, comment='추가약칭1'),
        sa.Column('alias_2', sa.String(length=200), nullable=True, comment='추가약칭2'),
        sa.Column('alias_3', sa.String(length=200), nullable=True, comment='추가약칭3'),
        sa.Column('english_name', sa.String(length=500), nullable=True, comment='영문명 (예: Ministry of Economy and Finance)'),
        sa.Column('english_alias', sa.String(length=100), nullable=True, comment='영문약칭 (예: MOEF)'),
        sa.Column('category', sa.String(length=100), nullable=True, comment='분류 (예: 중앙정부부처, 출연연, 공기업)'),
        sa.Column('definition', sa.Text(), nullable=True, comment='정의/설명'),
        sa.Column('use_yn', sa.Boolean(), nullable=False, server_default='true', comment='사용 여부'),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.PrimaryKeyConstraint('term_id'),
        sa.ForeignKeyConstraint(['dict_id'], ['dictionary.dict_id'], ondelete='CASCADE')
    )
    op.create_index('ix_dictionary_term_dict_id', 'dictionary_term', ['dict_id'])
    op.create_index('ix_dictionary_term_category', 'dictionary_term', ['category'])
    op.create_index('ix_dictionary_term_use_yn', 'dictionary_term', ['use_yn'])
    op.create_index('ix_dictionary_term_main_term', 'dictionary_term', ['main_term'])


def downgrade() -> None:
    # Drop dictionary_term table
    op.drop_index('ix_dictionary_term_main_term', table_name='dictionary_term')
    op.drop_index('ix_dictionary_term_use_yn', table_name='dictionary_term')
    op.drop_index('ix_dictionary_term_category', table_name='dictionary_term')
    op.drop_index('ix_dictionary_term_dict_id', table_name='dictionary_term')
    op.drop_table('dictionary_term')

    # Drop dictionary table
    op.drop_index('ix_dictionary_use_yn', table_name='dictionary')
    op.drop_index('ix_dictionary_dict_type', table_name='dictionary')
    op.drop_table('dictionary')

    # Drop enum type
    op.execute('DROP TYPE IF EXISTS dicttype')
