"""add_skills_system

Revision ID: f1a2b3c4d5e6
Revises: e9d598ac5740
Create Date: 2026-02-07 12:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'f1a2b3c4d5e6'
down_revision: Union[str, None] = 'e9d598ac5740'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table('skills',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('nome', sa.String(length=200), nullable=False, comment='Nome da skill'),
        sa.Column('descricao', sa.Text(), nullable=True, comment='Descricao curta da skill'),
        sa.Column('instrucoes', sa.Text(), nullable=False, comment='Instrucoes injetadas no prompt do agente'),
        sa.Column('icone', sa.String(length=10), nullable=True, comment='Emoji representativo'),
        sa.Column('escopo', sa.String(length=20), nullable=False, comment='system ou user'),
        sa.Column('tipos_artefato', sa.String(length=200), nullable=True, comment='CSV dos tipos de artefato aplicaveis'),
        sa.Column('ativa', sa.Boolean(), nullable=False, server_default='true', comment='Se a skill esta ativa'),
        sa.Column('usuario_id', sa.Integer(), nullable=True, comment='ID do usuario criador'),
        sa.Column('data_criacao', sa.DateTime(), nullable=False),
        sa.Column('data_atualizacao', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['usuario_id'], ['usuarios.id'], ),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index(op.f('ix_skills_id'), 'skills', ['id'], unique=False)

    op.create_table('projeto_skills',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('projeto_id', sa.Integer(), nullable=False, comment='ID do projeto'),
        sa.Column('skill_id', sa.Integer(), nullable=False, comment='ID da skill'),
        sa.Column('ativa_no_projeto', sa.Boolean(), nullable=False, server_default='true', comment='Se a skill esta ativa neste projeto'),
        sa.ForeignKeyConstraint(['projeto_id'], ['projetos.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['skill_id'], ['skills.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index(op.f('ix_projeto_skills_id'), 'projeto_skills', ['id'], unique=False)


def downgrade() -> None:
    op.drop_index(op.f('ix_projeto_skills_id'), table_name='projeto_skills')
    op.drop_table('projeto_skills')
    op.drop_index(op.f('ix_skills_id'), table_name='skills')
    op.drop_table('skills')
