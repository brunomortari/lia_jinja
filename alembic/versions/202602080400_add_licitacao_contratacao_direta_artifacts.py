"""add_licitacao_contratacao_direta_artifacts

Revision ID: e1f2g3h4i5j6
Revises: d5e6f7a8b901
Create Date: 2026-02-08 04:00:00.000000

Adds 4 new artifact tables for final procurement flow:
- checklist_conformidade (Licitação Normal)
- minuta_contrato (Licitação Normal)
- aviso_publicidade_direta (Contratação Direta)
- justificativa_fornecedor_escolhido (Contratação Direta)
"""

revision = 'e1f2g3h4i5j6'
down_revision = 'd5e6f7a8b901'
branch_labels = None
depends_on = None

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

def upgrade():
    # Create checklist_conformidade table
    op.create_table('checklist_conformidade',
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
        sa.Column('projeto_id', sa.Integer(), nullable=False),
        sa.Column('tr_id', sa.Integer(), nullable=True),
        sa.Column('itens_verificacao', postgresql.JSON(astext_type=sa.Text()), nullable=True),
        sa.Column('dfd_presente', sa.String(length=20), nullable=True),
        sa.Column('dfd_folhas', sa.String(length=100), nullable=True),
        sa.Column('etp_presente', sa.String(length=20), nullable=True),
        sa.Column('etp_folhas', sa.String(length=100), nullable=True),
        sa.Column('tr_presente', sa.String(length=20), nullable=True),
        sa.Column('tr_folhas', sa.String(length=100), nullable=True),
        sa.Column('matriz_riscos_presente', sa.String(length=20), nullable=True),
        sa.Column('matriz_riscos_folhas', sa.String(length=100), nullable=True),
        sa.Column('disponibilidade_orcamentaria_presente', sa.String(length=20), nullable=True),
        sa.Column('disponibilidade_orcamentaria_folhas', sa.String(length=100), nullable=True),
        sa.Column('parecer_juridico_presente', sa.String(length=20), nullable=True),
        sa.Column('parecer_juridico_folhas', sa.String(length=100), nullable=True),
        sa.Column('validado_por', sa.String(length=200), nullable=True),
        sa.Column('assinatura_eletronica', postgresql.JSON(astext_type=sa.Text()), nullable=True),
        sa.Column('observacoes_gerais', sa.Text(), nullable=True),
        sa.Column('status_conformidade', sa.String(length=50), nullable=True),
        sa.ForeignKeyConstraint(['projeto_id'], ['projetos.id'], ),
        sa.ForeignKeyConstraint(['tr_id'], ['trs.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_checklist_conformidade_id'), 'checklist_conformidade', ['id'], unique=False)

    # Create minuta_contrato table
    op.create_table('minuta_contrato',
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
        sa.Column('projeto_id', sa.Integer(), nullable=False),
        sa.Column('edital_id', sa.Integer(), nullable=True),
        sa.Column('obrigacoes_contratada', sa.Text(), nullable=True),
        sa.Column('obrigacoes_contratante', sa.Text(), nullable=True),
        sa.Column('obrigacoes_estruturadas', postgresql.JSON(astext_type=sa.Text()), nullable=True),
        sa.Column('forma_pagamento', sa.Text(), nullable=True),
        sa.Column('prazo_pagamento', sa.String(length=100), nullable=True),
        sa.Column('fluxo_liquidacao', sa.Text(), nullable=True),
        sa.Column('data_inicio', sa.Date(), nullable=True),
        sa.Column('data_termino', sa.Date(), nullable=True),
        sa.Column('prazo_vigencia', sa.String(length=100), nullable=True),
        sa.Column('possibilidade_prorrogacao', sa.String(length=20), nullable=True),
        sa.Column('condicoes_prorrogacao', sa.Text(), nullable=True),
        sa.Column('prazo_maximo_prorrogacao', sa.String(length=100), nullable=True),
        sa.Column('exige_garantia', sa.String(length=20), nullable=True),
        sa.Column('tipo_garantia', sa.String(length=100), nullable=True),
        sa.Column('percentual_garantia', sa.Float(), nullable=True),
        sa.Column('valor_garantia', sa.Float(), nullable=True),
        sa.Column('rescisao', sa.Text(), nullable=True),
        sa.Column('penalidades', sa.Text(), nullable=True),
        sa.Column('lei_aplicavel', sa.Text(), nullable=True),
        sa.Column('foro_competente', sa.String(length=200), nullable=True),
        sa.ForeignKeyConstraint(['edital_id'], ['editais.id'], ),
        sa.ForeignKeyConstraint(['projeto_id'], ['projetos.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_minuta_contrato_id'), 'minuta_contrato', ['id'], unique=False)

    # Create aviso_publicidade_direta table
    op.create_table('aviso_publicidade_direta',
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
        sa.Column('projeto_id', sa.Integer(), nullable=False),
        sa.Column('tr_id', sa.Integer(), nullable=True),
        sa.Column('fundamento_legal', sa.String(length=100), nullable=True),
        sa.Column('artigo_lei', sa.String(length=50), nullable=True),
        sa.Column('justificativa_legal', sa.Text(), nullable=True),
        sa.Column('valor_estimado', sa.Float(), nullable=True),
        sa.Column('metodologia_valor', sa.Text(), nullable=True),
        sa.Column('prazo_manifestacao_dias', sa.Integer(), nullable=True),
        sa.Column('data_inicio_prazo', sa.Date(), nullable=True),
        sa.Column('data_fim_prazo', sa.Date(), nullable=True),
        sa.Column('data_publicacao_pncp', sa.DateTime(), nullable=True),
        sa.Column('link_pncp', sa.String(length=500), nullable=True),
        sa.Column('data_publicacao_site_orgao', sa.DateTime(), nullable=True),
        sa.Column('link_site_orgao', sa.String(length=500), nullable=True),
        sa.Column('numero_aviso', sa.String(length=50), nullable=True),
        sa.Column('extrato_aviso', sa.Text(), nullable=True),
        sa.ForeignKeyConstraint(['projeto_id'], ['projetos.id'], ),
        sa.ForeignKeyConstraint(['tr_id'], ['trs.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_aviso_publicidade_direta_id'), 'aviso_publicidade_direta', ['id'], unique=False)

    # Create justificativa_fornecedor_escolhido table
    op.create_table('justificativa_fornecedor_escolhido',
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
        sa.Column('projeto_id', sa.Integer(), nullable=False),
        sa.Column('aviso_id', sa.Integer(), nullable=True),
        sa.Column('nome_fornecedor', sa.String(length=300), nullable=True),
        sa.Column('cnpj_fornecedor', sa.String(length=20), nullable=True),
        sa.Column('endereco_fornecedor', sa.Text(), nullable=True),
        sa.Column('qualificacao_tecnica', sa.Text(), nullable=True),
        sa.Column('atestados_capacidade', postgresql.JSON(astext_type=sa.Text()), nullable=True),
        sa.Column('experiencia_comprovada', sa.Text(), nullable=True),
        sa.Column('certidao_federal', postgresql.JSON(astext_type=sa.Text()), nullable=True),
        sa.Column('certidao_estadual', postgresql.JSON(astext_type=sa.Text()), nullable=True),
        sa.Column('certidao_municipal', postgresql.JSON(astext_type=sa.Text()), nullable=True),
        sa.Column('certidao_fgts', postgresql.JSON(astext_type=sa.Text()), nullable=True),
        sa.Column('certidao_trabalhista', postgresql.JSON(astext_type=sa.Text()), nullable=True),
        sa.Column('certidoes_anexadas', postgresql.JSON(astext_type=sa.Text()), nullable=True),
        sa.Column('inviabilidade_competicao', sa.String(length=20), nullable=True),
        sa.Column('justificativa_inviabilidade', sa.Text(), nullable=True),
        sa.Column('tipo_inviabilidade', sa.String(length=100), nullable=True),
        sa.Column('documentacao_exclusividade', postgresql.JSON(astext_type=sa.Text()), nullable=True),
        sa.Column('preco_proposto', sa.Float(), nullable=True),
        sa.Column('analise_compatibilidade_preco', sa.Text(), nullable=True),
        sa.Column('valores_referencia', postgresql.JSON(astext_type=sa.Text()), nullable=True),
        sa.Column('conclusao_justificativa', sa.Text(), nullable=True),
        sa.ForeignKeyConstraint(['aviso_id'], ['aviso_publicidade_direta.id'], ),
        sa.ForeignKeyConstraint(['projeto_id'], ['projetos.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_justificativa_fornecedor_escolhido_id'), 'justificativa_fornecedor_escolhido', ['id'], unique=False)


def downgrade():
    op.drop_index(op.f('ix_justificativa_fornecedor_escolhido_id'), table_name='justificativa_fornecedor_escolhido')
    op.drop_table('justificativa_fornecedor_escolhido')
    op.drop_index(op.f('ix_aviso_publicidade_direta_id'), table_name='aviso_publicidade_direta')
    op.drop_table('aviso_publicidade_direta')
    op.drop_index(op.f('ix_minuta_contrato_id'), table_name='minuta_contrato')
    op.drop_table('minuta_contrato')
    op.drop_index(op.f('ix_checklist_conformidade_id'), table_name='checklist_conformidade')
    op.drop_table('checklist_conformidade')
