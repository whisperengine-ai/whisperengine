"""add generic keyword templates

Revision ID: 2230add_keyword_templates
Revises: 1fd48f6d9650
Create Date: 2025-10-12 22:30:00.000000+00:00

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = '2230add_keyword_templates'
down_revision: Union[str, None] = '1fd48f6d9650'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

def upgrade():
    # Create generic_keyword_templates table
    op.create_table(
        'generic_keyword_templates',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('category', sa.String(50), nullable=False),
        sa.Column('template_name', sa.String(100), nullable=False),
        sa.Column('keywords', postgresql.ARRAY(sa.String()), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('priority_order', sa.Integer(), nullable=False, default=1),
        sa.Column('is_active', sa.Boolean(), nullable=False, default=True),
        sa.Column('created_at', sa.TIMESTAMP(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.TIMESTAMP(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.PrimaryKeyConstraint('id')
    )
    
    # Create indexes
    op.create_index('idx_generic_keyword_templates_category', 'generic_keyword_templates', ['category'])
    op.create_index('idx_generic_keyword_templates_active', 'generic_keyword_templates', ['is_active'])

def downgrade():
    op.drop_table('generic_keyword_templates')