""" 
Sistema LIA - Modelo TR
========================
Termo de Referência.

Autor: Equipe TRE-GO
Data: Fevereiro 2026
"""

from sqlalchemy import Column, Integer, Text, Boolean, ForeignKey
from sqlalchemy.orm import relationship
from .base import ArtefatoBase


class TR(ArtefatoBase):
    """Termo de Referência"""
    __tablename__ = "trs"

    projeto_id = Column(Integer, ForeignKey("projetos.id"), nullable=False)
    projeto = relationship("Projeto", back_populates="trs")

    definicao_objeto = Column(Text, nullable=True)
    justificativa = Column(Text, nullable=True)
    especificacao_tecnica = Column(Text, nullable=True)
    obrigacoes = Column(Text, nullable=True)
    criterios_aceitacao = Column(Text, nullable=True)
    
    # Flag para indicar se é uma contratação direta (sem licitação formal)
    contratacao_direta = Column(Boolean, default=False, nullable=False)
