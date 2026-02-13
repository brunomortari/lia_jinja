"""remove_icone_tipos_artefato_skills

Revision ID: remove_skills_fields
Revises: previous_revision
Create Date: 2026-02-07 12:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = 'd5e6f7a8b901'
down_revision = 'c4d5e6f7a8b9' # Adjust this to the actual previous revision
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Remove columns from skills table
    op.drop_column('skills', 'icone')
    op.drop_column('skills', 'tipos_artefato')


def downgrade() -> None:
    # Re-add columns to skills table
    op.add_column('skills', sa.Column('tipos_artefato', sa.VARCHAR(length=200), autoincrement=False, nullable=True, comment='CSV dos tipos: dfd,etp,tr,riscos,edital,pesquisa_precos. Null = todos'))
    op.add_column('skills', sa.Column('icone', sa.VARCHAR(length=10), autoincrement=False, nullable=True, comment='Emoji representativo'))
