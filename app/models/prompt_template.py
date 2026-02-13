"""
Modelo para armazenar templates de prompts dos agentes.
Permite editar, versionar e gerenciar prompts sem modificar código.
"""
from datetime import datetime
from sqlalchemy import Column, Integer, String, Text, Boolean, DateTime, Index
from sqlalchemy.sql import func
from app.database import Base


class PromptTemplate(Base):
    """
    Template de prompt para agentes de IA.
    
    Atributos:
        agent_type: tipo do agente (ex: "dfd", "etp", "pgr", "tr", "edital", etc.)
        prompt_type: tipo do prompt ("system", "system_chat", "system_generate", "user_template")
        conteudo: texto do prompt (pode conter placeholders Jinja2 como {{projeto_titulo}})
        versao: número da versão do prompt (ex: "1.0", "1.1")
        ativa: se este prompt está ativo (apenas 1 prompt ativo por agent_type+prompt_type)
        ordem: ordem de aplicação quando múltiplos prompts complementares (padrão 0)
        descricao: descrição opcional do que este prompt faz
        data_criacao: timestamp de criação
        data_atualizacao: timestamp de última atualização
    """
    __tablename__ = "prompt_templates"
    
    id = Column(Integer, primary_key=True, index=True)
    agent_type = Column(String(50), nullable=False, index=True)  # "dfd", "etp", "pgr", etc.
    prompt_type = Column(String(50), nullable=False, index=True)  # "system", "system_chat", "system_generate"
    conteudo = Column(Text, nullable=False)
    versao = Column(String(20), nullable=False, default="1.0")
    ativa = Column(Boolean, default=True, nullable=False, index=True)
    ordem = Column(Integer, default=0, nullable=False)  # Para ordenar múltiplos prompts complementares
    descricao = Column(Text, nullable=True)
    data_criacao = Column(DateTime, default=func.now(), nullable=False)
    data_atualizacao = Column(DateTime, default=func.now(), onupdate=func.now(), nullable=False)
    
    # Índice composto para busca rápida de prompts ativos por tipo de agente
    __table_args__ = (
        Index('idx_agent_prompt_active', 'agent_type', 'prompt_type', 'ativa'),
    )
    
    def __repr__(self):
        return f"<PromptTemplate(agent={self.agent_type}, type={self.prompt_type}, v={self.versao}, ativa={self.ativa})>"
