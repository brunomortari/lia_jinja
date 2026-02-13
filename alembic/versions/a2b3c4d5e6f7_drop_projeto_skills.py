"""drop projeto_skills table

Revision ID: a2b3c4d5e6f7
Revises: f1a2b3c4d5e6
Create Date: 2026-02-07 07:30:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'a2b3c4d5e6f7'
down_revision: Union[str, None] = 'f1a2b3c4d5e6'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Drop projeto_skills table
    op.drop_table('projeto_skills')


def downgrade() -> None:
    # Recreate projeto_skills table (cópia simplificada do create original)
    op.create_table('projeto_skills',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('projeto_id', sa.Integer(), nullable=False, comment='ID do projeto'),
    sa.Column('skill_id', sa.Integer(), nullable=False, comment='ID da skill'),
    sa.Column('ativa_no_projeto', sa.Boolean(), nullable=False, comment='Se a skill esta ativa neste projeto'),
    sa.ForeignKeyConstraint(['projeto_id'], ['projetos.id'], ondelete='CASCADE'),
    sa.ForeignKeyConstraint(['skill_id'], ['skills.id'], ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_projeto_skills_id'), 'projeto_skills', ['id'], unique=False)
