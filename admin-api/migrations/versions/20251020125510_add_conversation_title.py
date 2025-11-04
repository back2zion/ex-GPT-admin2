"""add conversation_title to usage_history

Revision ID: add_conversation_title
Revises: 
Create Date: 2025-10-20 13:00:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'add_conversation_title'
down_revision = None  # 나중에 확인 필요

def upgrade():
    op.add_column('usage_history', sa.Column('conversation_title', sa.String(length=200), nullable=True))


def downgrade():
    op.drop_column('usage_history', 'conversation_title')
