"""add_vector_data_management_tables

Revision ID: ff69bd7d1694
Revises: e7ce091bc296
Create Date: 2025-10-20 17:18:59.875851

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'ff69bd7d1694'
down_revision: Union[str, None] = 'e7ce091bc296'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """
    학습데이터 관리를 위한 테이블 생성
    - categories: 문서 카테고리
    - document_vectors: Qdrant 벡터 메타데이터
    - documents.category_id: 카테고리 외래키 추가
    """

    # 1. Create categories table
    op.create_table(
        'categories',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(length=255), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('parsing_pattern', sa.Enum('SENTENCE', 'PARAGRAPH', 'PAGE', 'CUSTOM', name='parsingpattern'), nullable=False, server_default='PARAGRAPH'),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('now()'), nullable=True),
        sa.Column('updated_at', sa.DateTime(), server_default=sa.text('now()'), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_categories_id'), 'categories', ['id'], unique=False)
    op.create_index(op.f('ix_categories_name'), 'categories', ['name'], unique=True)

    # 2. Create document_vectors table
    op.create_table(
        'document_vectors',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('document_id', sa.Integer(), nullable=False),
        sa.Column('qdrant_point_id', sa.String(length=255), nullable=False),
        sa.Column('qdrant_collection', sa.String(length=255), nullable=False),
        sa.Column('chunk_index', sa.Integer(), nullable=False),
        sa.Column('chunk_text', sa.String(length=10000), nullable=True),
        sa.Column('chunk_metadata', sa.JSON(), nullable=True),
        sa.Column('vector_dimension', sa.Integer(), nullable=True),
        sa.Column('embedding_model', sa.String(length=255), nullable=True),
        sa.Column('status', sa.Enum('PENDING', 'PROCESSING', 'COMPLETED', 'FAILED', name='vectorstatus'), nullable=False, server_default='PENDING'),
        sa.Column('error_message', sa.String(length=1000), nullable=True),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('now()'), nullable=True),
        sa.Column('updated_at', sa.DateTime(), server_default=sa.text('now()'), nullable=True),
        sa.ForeignKeyConstraint(['document_id'], ['documents.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_document_vectors_document_id'), 'document_vectors', ['document_id'], unique=False)
    op.create_index(op.f('ix_document_vectors_id'), 'document_vectors', ['id'], unique=False)
    op.create_index(op.f('ix_document_vectors_qdrant_point_id'), 'document_vectors', ['qdrant_point_id'], unique=False)

    # 3. Add category_id to documents table
    op.add_column('documents', sa.Column('category_id', sa.Integer(), nullable=True))
    op.create_index(op.f('ix_documents_category_id'), 'documents', ['category_id'], unique=False)
    op.create_foreign_key('fk_documents_category_id', 'documents', 'categories', ['category_id'], ['id'])


def downgrade() -> None:
    """
    롤백: 테이블 및 컬럼 제거
    """

    # 3. Remove category_id from documents
    op.drop_constraint('fk_documents_category_id', 'documents', type_='foreignkey')
    op.drop_index(op.f('ix_documents_category_id'), table_name='documents')
    op.drop_column('documents', 'category_id')

    # 2. Drop document_vectors table
    op.drop_index(op.f('ix_document_vectors_qdrant_point_id'), table_name='document_vectors')
    op.drop_index(op.f('ix_document_vectors_id'), table_name='document_vectors')
    op.drop_index(op.f('ix_document_vectors_document_id'), table_name='document_vectors')
    op.drop_table('document_vectors')

    # 1. Drop categories table
    op.drop_index(op.f('ix_categories_name'), table_name='categories')
    op.drop_index(op.f('ix_categories_id'), table_name='categories')
    op.drop_table('categories')

    # Drop enums
    sa.Enum(name='vectorstatus').drop(op.get_bind(), checkfirst=True)
    sa.Enum(name='parsingpattern').drop(op.get_bind(), checkfirst=True)
