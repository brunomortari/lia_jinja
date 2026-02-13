"""
Sistema LIA - Modelos de Skill (Habilidade)
============================================
Define as tabelas de skills e a associacao com projetos.

Skills sao instrucoes comportamentais que modificam o prompt
do agente conversacional durante a geracao de artefatos.

Autor: Equipe TRE-GO
Data: Fevereiro 2026
"""

from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey, Boolean, JSON
from sqlalchemy.orm import relationship
from datetime import datetime

from app.database import Base
from app.utils.datetime_utils import now_brasilia


class Skill(Base):
    """
    Modelo de Skill (Habilidade).

    Representa uma instrucao comportamental que pode ser injetada
    no prompt do agente conversacional. Pode ser do sistema (global)
    ou criada pelo usuario (privada).
    """
    __tablename__ = "skills"

    id = Column(Integer, primary_key=True, index=True)
    nome = Column(String(200), nullable=False, comment="Nome da skill")
    descricao = Column(Text, nullable=True, comment="Descricao curta da skill")
    instrucoes = Column(Text, nullable=False, comment="Instrucoes injetadas no prompt do agente")
    escopo = Column(String(20), default="user", nullable=False, comment="system ou user")
    ativa = Column(Boolean, default=True, nullable=False, comment="Se a skill esta ativa globalmente")

    # Dono da skill (null = skill do sistema)
    usuario_id = Column(
        Integer,
        ForeignKey("usuarios.id"),
        nullable=True,
        comment="ID do usuario criador. Null para skills do sistema"
    )

    # Tools / Capacidades (JSON)
    tools = Column(
        JSON,
        nullable=True,
        comment="Lista de ferramentas habilitadas pela skill. Ex: ['web_search', 'check_compliance']"
    )

    # Contexto documental (Knowledge Base)
    # Lista de objetos: [{"titulo": "Nome do Doc", "conteudo": "Texto completo extraido..."}]
    textos_base = Column(
        JSON,
        nullable=True,
        comment="Base de conhecimento textual (full-text) para injetar no prompt"
    )

    # Timestamps
    data_criacao = Column(DateTime, default=now_brasilia, nullable=False)
    data_atualizacao = Column(DateTime, default=now_brasilia, onupdate=now_brasilia, nullable=False)

    # Relacionamentos
    usuario = relationship("User", back_populates="skills")

    def __repr__(self):
        return f"<Skill(id={self.id}, nome='{self.nome}', escopo='{self.escopo}')>"

    def to_dict(self):
        """Converte para dicionario."""
        return {
            "id": self.id,
            "nome": self.nome,
            "descricao": self.descricao,
            "instrucoes": self.instrucoes,
            "escopo": self.escopo,
            "ativa": self.ativa,
            "tools": self.tools,
            "textos_base": self.textos_base,
            "usuario_id": self.usuario_id,
            "data_criacao": self.data_criacao.isoformat() if self.data_criacao else None,
            "data_atualizacao": self.data_atualizacao.isoformat() if self.data_atualizacao else None,
        }
