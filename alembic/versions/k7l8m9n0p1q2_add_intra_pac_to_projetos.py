"""add_intra_pac_column_to_projetos

Revision ID: k7l8m9n0p1q2
Revises: j6k7l8m9n0p1
Create Date: 2026-02-08 20:00:00.000000

Adds intra_pac boolean column to projetos table to identify 
whether the project is within the PAC (True) or outside the PAC (False).
"""
from alembic import op
import sqlalchemy as sa


revision = 'k7l8m9n0p1q2'
down_revision = 'j6k7l8m9n0p1'
branch_labels = None
depends_on = None


def upgrade():
    op.add_column('projetos', sa.Column('intra_pac', sa.Boolean(), nullable=False, server_default='True',
        comment='True para projetos dentro do PAC (intra-PAC), False para fora do PAC (extra-PAC)'))


def downgrade():
    op.drop_column('projetos', 'intra_pac')
