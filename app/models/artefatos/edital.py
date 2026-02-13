""" 
Sistema LIA - Modelo Edital
============================
Edital de Licitação.

Autor: Equipe TRE-GO
Data: Fevereiro 2026
"""

from sqlalchemy import Column, Integer, Text, ForeignKey
from sqlalchemy.orm import relationship
from .base import ArtefatoBase


class Edital(ArtefatoBase):
    """Edital de Licitação"""
    __tablename__ = "editais"

    projeto_id = Column(Integer, ForeignKey("projetos.id"), nullable=False)
    projeto = relationship("Projeto", back_populates="editais")

    objeto = Column(Text, nullable=True)
    condicoes_participacao = Column(Text, nullable=True)
    criterios_julgamento = Column(Text, nullable=True)
    fase_lances = Column(Text, nullable=True)
