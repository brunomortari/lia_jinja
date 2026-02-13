""" 
Sistema LIA - Modelos DFD
=========================
Documento de Formalização da Demanda.

Autor: Equipe TRE-GO
Data: Fevereiro 2026
"""

from sqlalchemy import Column, Integer, String, Text, Float, Date, ForeignKey
from sqlalchemy.orm import relationship
from .base import ArtefatoBase


class DFD(ArtefatoBase):
    """Documento de Formalização da Demanda"""
    __tablename__ = "dfds"

    projeto_id = Column(Integer, ForeignKey("projetos.id"), nullable=False)
    projeto = relationship("Projeto", back_populates="dfds")

    descricao_objeto = Column(Text, nullable=True)
    justificativa = Column(Text, nullable=True)
    alinhamento_estrategico = Column(Text, nullable=True)
    valor_estimado = Column(Float, nullable=True)
    cronograma = Column(Text, nullable=True)
    
    responsavel_requisitante = Column(String(200), nullable=True)
    responsavel_gestor = Column(String(200), nullable=True)
    responsavel_fiscal = Column(String(200), nullable=True)
    
    # Novos campos para atender requisitos do especialista
    setor_requisitante = Column(String(200), nullable=True)
    grau_prioridade = Column(String(50), nullable=True)
    data_pretendida = Column(Date, nullable=True)
    alinhamento_pca = Column(Text, nullable=True)
