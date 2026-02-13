"""add contratacao_direta to TR

Revision ID: i5j6k7l8m9n0
Revises: h4i5j6k7l8m9
Create Date: 2026-02-08 15:30:00.000000

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'i5j6k7l8m9n0'
down_revision: Union[str, None] = 'h4i5j6k7l8m9'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Adiciona campo contratacao_direta ao modelo TR"""
    op.add_column('trs', sa.Column('contratacao_direta', sa.Boolean(), nullable=False, server_default='false'))


def downgrade() -> None:
    """Remove campo contratacao_direta do modelo TR"""
    op.drop_column('trs', 'contratacao_direta')
