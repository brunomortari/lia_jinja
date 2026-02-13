"""add_adesao_ata_dispensa_artifact_tables

Revision ID: f2g3h4i5j6k7
Revises: e1f2g3h4i5j6
Create Date: 2026-02-08 04:30:00.000000

Adds 7 missing artifact tables for Adesão a Ata and Dispensa flows that were
already defined in models but never created in the database schema.
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = 'f2g3h4i5j6k7'
down_revision = 'e1f2g3h4i5j6'
branch_labels = None
depends_on = None


def upgrade():
    # ========== FLUXO DE ADESÃO A ATA ==========
    
    # Create relatorios_vantagem_economica table
    op.create_table('relatorios_vantagem_economica',
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
        sa.Column('etp_id', sa.Integer(), nullable=True),
        sa.Column('comparativo_precos', postgresql.JSON(astext_type=sa.Text()), nullable=True),
        sa.Column('custo_processamento_adesao', sa.Float(), nullable=True),
        sa.Column('custo_processamento_direto', sa.Float(), nullable=True),
        sa.Column('conclusao_tecnica', sa.Text(), nullable=True),
        sa.Column('percentual_economia', sa.Float(), nullable=True),
        sa.Column('valor_economia_total', sa.Float(), nullable=True),
        sa.ForeignKeyConstraint(['projeto_id'], ['projetos.id'], ),
        sa.ForeignKeyConstraint(['etp_id'], ['etps.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_relatorios_vantagem_economica_id'), 'relatorios_vantagem_economica', ['id'], unique=False)

    # Create justificativas_vantagem_adesao table
    op.create_table('justificativas_vantagem_adesao',
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
        sa.Column('etp_id', sa.Integer(), nullable=True),
        sa.Column('fundamentacao_legal', sa.Text(), nullable=True),
        sa.Column('justificativa_conveniencia', sa.Text(), nullable=True),
        sa.Column('declaracao_conformidade', sa.Text(), nullable=True),
        sa.ForeignKeyConstraint(['projeto_id'], ['projetos.id'], ),
        sa.ForeignKeyConstraint(['etp_id'], ['etps.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_justificativas_vantagem_adesao_id'), 'justificativas_vantagem_adesao', ['id'], unique=False)

    # Create termos_aceite_fornecedor table
    op.create_table('termos_aceite_fornecedor',
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
        sa.Column('etp_id', sa.Integer(), nullable=True),
        sa.Column('nome_fornecedor', sa.String(length=300), nullable=True),
        sa.Column('cnpj_fornecedor', sa.String(length=20), nullable=True),
        sa.Column('descricao_objeto_aceito', sa.Text(), nullable=True),
        sa.Column('preco_aceito', sa.Float(), nullable=True),
        sa.Column('documentos_anexados', postgresql.JSON(astext_type=sa.Text()), nullable=True),
        sa.Column('responsaveis_assinatura', postgresql.JSON(astext_type=sa.Text()), nullable=True),
        sa.Column('observacoes', sa.Text(), nullable=True),
        sa.ForeignKeyConstraint(['projeto_id'], ['projetos.id'], ),
        sa.ForeignKeyConstraint(['etp_id'], ['etps.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_termos_aceite_fornecedor_id'), 'termos_aceite_fornecedor', ['id'], unique=False)

    # ========== FLUXO DE DISPENSA POR VALOR BAIXO ==========

    # Create trs_simplificados table
    op.create_table('trs_simplificados',
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
        sa.Column('etp_id', sa.Integer(), nullable=True),
        sa.Column('especificacao_objeto', sa.Text(), nullable=True),
        sa.Column('criterios_qualidade_simplificados', postgresql.JSON(astext_type=sa.Text()), nullable=True),
        sa.Column('prazos_simplificados', sa.Text(), nullable=True),
        sa.Column('valor_referencia_dispensa', sa.Float(), nullable=True),
        sa.Column('justificativa_dispensa_valor', sa.Text(), nullable=True),
        sa.ForeignKeyConstraint(['projeto_id'], ['projetos.id'], ),
        sa.ForeignKeyConstraint(['etp_id'], ['etps.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_trs_simplificados_id'), 'trs_simplificados', ['id'], unique=False)

    # Create avisos_dispensa_eletronica table
    op.create_table('avisos_dispensa_eletronica',
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
        sa.Column('etp_id', sa.Integer(), nullable=True),
        sa.Column('numero_aviso', sa.String(length=50), nullable=True),
        sa.Column('data_publicacao', sa.DateTime(), nullable=True),
        sa.Column('descricao_objeto_aviso', sa.Text(), nullable=True),
        sa.Column('link_portal', sa.String(length=500), nullable=True),
        sa.Column('protocolo_publicacao', sa.String(length=50), nullable=True),
        sa.ForeignKeyConstraint(['projeto_id'], ['projetos.id'], ),
        sa.ForeignKeyConstraint(['etp_id'], ['etps.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_avisos_dispensa_eletronica_id'), 'avisos_dispensa_eletronica', ['id'], unique=False)

    # Create justificativas_preco_escolha table
    op.create_table('justificativas_preco_escolha',
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
        sa.Column('etp_id', sa.Integer(), nullable=True),
        sa.Column('justificativa_fornecedor', sa.Text(), nullable=True),
        sa.Column('analise_preco_praticado', sa.Text(), nullable=True),
        sa.Column('preco_final_contratacao', sa.Float(), nullable=True),
        sa.ForeignKeyConstraint(['projeto_id'], ['projetos.id'], ),
        sa.ForeignKeyConstraint(['etp_id'], ['etps.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_justificativas_preco_escolha_id'), 'justificativas_preco_escolha', ['id'], unique=False)

    # Create certidoes_enquadramento table
    op.create_table('certidoes_enquadramento',
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
        sa.Column('etp_id', sa.Integer(), nullable=True),
        sa.Column('limite_legal_aplicavel', sa.Float(), nullable=True),
        sa.Column('valor_contratacao_analisada', sa.Float(), nullable=True),
        sa.Column('conclusao_enquadramento', sa.Text(), nullable=True),
        sa.Column('artigo_lei_aplicavel', sa.String(length=50), nullable=True),
        sa.Column('responsavel_certificacao', sa.String(length=200), nullable=True),
        sa.Column('data_certificacao', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['projeto_id'], ['projetos.id'], ),
        sa.ForeignKeyConstraint(['etp_id'], ['etps.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_certidoes_enquadramento_id'), 'certidoes_enquadramento', ['id'], unique=False)


def downgrade():
    op.drop_index(op.f('ix_certidoes_enquadramento_id'), table_name='certidoes_enquadramento')
    op.drop_table('certidoes_enquadramento')
    op.drop_index(op.f('ix_justificativas_preco_escolha_id'), table_name='justificativas_preco_escolha')
    op.drop_table('justificativas_preco_escolha')
    op.drop_index(op.f('ix_avisos_dispensa_eletronica_id'), table_name='avisos_dispensa_eletronica')
    op.drop_table('avisos_dispensa_eletronica')
    op.drop_index(op.f('ix_trs_simplificados_id'), table_name='trs_simplificados')
    op.drop_table('trs_simplificados')
    op.drop_index(op.f('ix_termos_aceite_fornecedor_id'), table_name='termos_aceite_fornecedor')
    op.drop_table('termos_aceite_fornecedor')
    op.drop_index(op.f('ix_justificativas_vantagem_adesao_id'), table_name='justificativas_vantagem_adesao')
    op.drop_table('justificativas_vantagem_adesao')
    op.drop_index(op.f('ix_relatorios_vantagem_economica_id'), table_name='relatorios_vantagem_economica')
    op.drop_table('relatorios_vantagem_economica')
