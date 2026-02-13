"""add_prompt_templates_table

Revision ID: h4i5j6k7l8m9
Revises: 2e4c64609f95
Create Date: 2026-02-08 13:38:00

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = 'h4i5j6k7l8m9'
down_revision = '2e4c64609f95'
branch_labels = None
depends_on = None


def upgrade():
    # Criar tabela prompt_templates
    op.create_table(
        'prompt_templates',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('agent_type', sa.String(length=50), nullable=False),
        sa.Column('prompt_type', sa.String(length=50), nullable=False),
        sa.Column('conteudo', sa.Text(), nullable=False),
        sa.Column('versao', sa.String(length=20), nullable=False, server_default='1.0'),
        sa.Column('ativa', sa.Boolean(), nullable=False, server_default='true'),
        sa.Column('ordem', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('descricao', sa.Text(), nullable=True),
        sa.Column('data_criacao', sa.DateTime(), nullable=False, server_default=sa.text('now()')),
        sa.Column('data_atualizacao', sa.DateTime(), nullable=False, server_default=sa.text('now()')),
        sa.PrimaryKeyConstraint('id')
    )
    
    # Criar índices
    op.create_index('ix_prompt_templates_id', 'prompt_templates', ['id'])
    op.create_index('ix_prompt_templates_agent_type', 'prompt_templates', ['agent_type'])
    op.create_index('ix_prompt_templates_prompt_type', 'prompt_templates', ['prompt_type'])
    op.create_index('ix_prompt_templates_ativa', 'prompt_templates', ['ativa'])
    op.create_index('idx_agent_prompt_active', 'prompt_templates', ['agent_type', 'prompt_type', 'ativa'])
    
    # Seed: Popular com prompts dos agentes existentes
    from app.services.agents.prompts_seed import SEED_PROMPTS
    from sqlalchemy.orm import Session
    from sqlalchemy import create_engine
    from app.config import settings
    from app.models.prompt_template import PromptTemplate
    
    engine = create_engine(settings.DATABASE_URL)
    session = Session(bind=engine)
    
    try:
        for prompt_data in SEED_PROMPTS:
            prompt = PromptTemplate(**prompt_data)
            session.add(prompt)
        session.commit()
    except Exception as e:
        session.rollback()
        print(f"Erro ao popular prompts: {e}")
    finally:
        session.close()


def downgrade():
    op.drop_index('idx_agent_prompt_active', table_name='prompt_templates')
    op.drop_index('ix_prompt_templates_ativa', table_name='prompt_templates')
    op.drop_index('ix_prompt_templates_prompt_type', table_name='prompt_templates')
    op.drop_index('ix_prompt_templates_agent_type', table_name='prompt_templates')
    op.drop_index('ix_prompt_templates_id', table_name='prompt_templates')
    op.drop_table('prompt_templates')
