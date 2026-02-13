""" 
Sistema LIA - Modelo JVA
=========================
Justificativa de Vantagem e Conveniência da Adesão.

Autor: Equipe TRE-GO
Data: Fevereiro 2026
"""

from sqlalchemy import Column, Integer, Text, ForeignKey
from sqlalchemy.orm import relationship
from .base import ArtefatoBase


class JustificativaVantagemAdesao(ArtefatoBase):
    """
    Justificativa de Vantagem e Conveniência da Adesão (JVA)
    Lei 14.133/2021, Art. 37. Fluxo: Adesão a Ata.
    """
    __tablename__ = "justificativas_vantagem_adesao"
    
    projeto_id = Column(Integer, ForeignKey("projetos.id"), nullable=False)
    etp_id = Column(Integer, ForeignKey("etps.id"), nullable=True)
    projeto = relationship("Projeto", foreign_keys=[projeto_id])
    etp = relationship("ETP", foreign_keys=[etp_id])
    
    fundamentacao_legal = Column(Text, nullable=True,
        comment="Citação da Lei 14.133/21, Art. 37 e jurisprudência aplicável")
    
    justificativa_conveniencia = Column(Text, nullable=True,
        comment="Por que adesão é mais conveniente que contratação direta")
    
    declaracao_conformidade = Column(Text, nullable=True,
        comment="Declara conformidade com Lei 14.133/21 e regulamentos internos")
