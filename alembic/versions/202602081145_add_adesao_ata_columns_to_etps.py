"""add_adesao_ata_columns_to_etps

Revision ID: g3h4i5j6k7l8
Revises: f2g3h4i5j6k7
Create Date: 2026-02-08 11:45:00.000000

Adds columns to etps table for Adesão de Ata workflow:
- adesao_ata_habilitada: Flag indicating user enabled ATA adhesion search
- fase_adesao_ata: Current phase of ATA adhesion process
- ata_selecionada: JSON with selected ATA data
- deep_research_ativado: Flag indicating deep research was activated
- modalidade_sugerida: Suggested contracting modality
- modalidade_definida: Final contracting modality chosen by user
- data_definicao_modalidade: When modality was defined
- justificativa_modalidade: Technical/legal justification for modality choice
- criterios_analise_modalidade: JSON with analysis criteria for modality
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = 'g3h4i5j6k7l8'
down_revision = 'f2g3h4i5j6k7'
branch_labels = None
depends_on = None


def upgrade():
    # Add ATA Adhesion workflow columns to etps table
    op.add_column('etps', sa.Column('adesao_ata_habilitada', sa.Boolean(), nullable=False, server_default='false'))
    op.add_column('etps', sa.Column('fase_adesao_ata', sa.String(length=50), nullable=True))
    op.add_column('etps', sa.Column('ata_selecionada', postgresql.JSON(astext_type=sa.Text()), nullable=True))
    op.add_column('etps', sa.Column('deep_research_ativado', sa.Boolean(), nullable=False, server_default='false'))
    
    # Add modality definition columns to etps table
    op.add_column('etps', sa.Column('modalidade_sugerida', sa.String(length=50), nullable=True))
    op.add_column('etps', sa.Column('modalidade_definida', sa.String(length=50), nullable=True))
    op.add_column('etps', sa.Column('data_definicao_modalidade', sa.DateTime(), nullable=True))
    op.add_column('etps', sa.Column('justificativa_modalidade', sa.Text(), nullable=True))
    op.add_column('etps', sa.Column('criterios_analise_modalidade', postgresql.JSON(astext_type=sa.Text()), nullable=True))


def downgrade():
    op.drop_column('etps', 'criterios_analise_modalidade')
    op.drop_column('etps', 'justificativa_modalidade')
    op.drop_column('etps', 'data_definicao_modalidade')
    op.drop_column('etps', 'modalidade_definida')
    op.drop_column('etps', 'modalidade_sugerida')
    op.drop_column('etps', 'deep_research_ativado')
    op.drop_column('etps', 'ata_selecionada')
    op.drop_column('etps', 'fase_adesao_ata')
    op.drop_column('etps', 'adesao_ata_habilitada')
