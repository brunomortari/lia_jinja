"""add_justificativa_excepcionalidade_table

Revision ID: j6k7l8m9n0p1
Revises: i5j6k7l8m9n0
Create Date: 2026-02-08 19:00:00.000000

Adds justificativas_excepcionalidade table for projects without PAC.
Lei 14.133/2021 - Justificativa de Contratação não Planejada.
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = 'j6k7l8m9n0p1'
down_revision = 'i5j6k7l8m9n0'
branch_labels = None
depends_on = None


def upgrade():
    op.create_table('justificativas_excepcionalidade',
        # Campos base (ArtefatoBase)
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('versao', sa.Integer(), nullable=False, server_default='1'),
        sa.Column('status', sa.String(length=50), nullable=False, server_default='rascunho'),
        sa.Column('gerado_por_ia', sa.Boolean(), nullable=True, server_default='False'),
        sa.Column('prompt_ia', sa.Text(), nullable=True),
        sa.Column('metadata_ia', postgresql.JSON(astext_type=sa.Text()), nullable=True),
        sa.Column('campos_editados', postgresql.JSON(astext_type=sa.Text()), nullable=True),
        sa.Column('campos_regenerados', postgresql.JSON(astext_type=sa.Text()), nullable=True),
        sa.Column('data_criacao', sa.DateTime(), nullable=True),
        sa.Column('data_atualizacao', sa.DateTime(), nullable=True),
        sa.Column('data_aprovacao', sa.DateTime(), nullable=True),
        sa.Column('protocolo_sei', postgresql.JSON(astext_type=sa.Text()), nullable=True),
        # FK
        sa.Column('projeto_id', sa.Integer(), nullable=False),
        # Campos específicos
        sa.Column('motivo_inclusao', sa.Text(), nullable=True,
            comment='Justificativa da falha na previsão inicial do PAC'),
        sa.Column('risco_adiamento', sa.Text(), nullable=True,
            comment='O que acontece se a contratação for adiada para o próximo ciclo'),
        sa.Column('impacto_planejamento', sa.Text(), nullable=True,
            comment='Análise do impacto da inclusão nas contratações já planejadas no PAC'),
        sa.Column('alinhamento_estrategico', sa.Text(), nullable=True,
            comment='Como a contratação contribui para os objetivos estratégicos do órgão'),
        sa.Column('parecer_autoridade', sa.Text(), nullable=True,
            comment='Parecer e decisão da autoridade competente sobre a excepcionalidade'),
        sa.Column('autorizacao_especial', sa.Boolean(), nullable=True, server_default='False',
            comment='Se a autoridade competente autorizou a quebra do planejamento original'),
        sa.Column('tipo_excepcionalidade', sa.String(length=100), nullable=True,
            comment='Tipo: emergencia, alteracao_legislativa, tecnologia_superveniente, outro'),
        # Constraints
        sa.ForeignKeyConstraint(['projeto_id'], ['projetos.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_justificativas_excepcionalidade_id'), 'justificativas_excepcionalidade', ['id'], unique=False)
    op.create_index(op.f('ix_justificativas_excepcionalidade_projeto_id'), 'justificativas_excepcionalidade', ['projeto_id'], unique=False)


def downgrade():
    op.drop_index(op.f('ix_justificativas_excepcionalidade_projeto_id'), table_name='justificativas_excepcionalidade')
    op.drop_index(op.f('ix_justificativas_excepcionalidade_id'), table_name='justificativas_excepcionalidade')
    op.drop_table('justificativas_excepcionalidade')
