""" 
Sistema LIA - Modelo TRS
=========================
Termo de Referência Simplificado.

Autor: Equipe TRE-GO
Data: Fevereiro 2026
"""

from sqlalchemy import Column, Integer, Text, Float, ForeignKey, JSON
from sqlalchemy.orm import relationship
from .base import ArtefatoBase


class TRSimplificado(ArtefatoBase):
    """
    Termo de Referência Simplificado (TRS)
    Lei 14.133/2021, Art. 75. Fluxo: Dispensa por Valor Baixo.
    """
    __tablename__ = "trs_simplificados"
    
    projeto_id = Column(Integer, ForeignKey("projetos.id"), nullable=False)
    etp_id = Column(Integer, ForeignKey("etps.id"), nullable=True)
    projeto = relationship("Projeto", foreign_keys=[projeto_id])
    etp = relationship("ETP", foreign_keys=[etp_id])
    
    especificacao_objeto = Column(Text, nullable=True,
        comment="Especificação técnica do objeto (simplificada)")
    
    criterios_qualidade_simplificados = Column(JSON, nullable=True,
        comment="JSON: [{criterio, descricao}, ...]")
    
    prazos_simplificados = Column(Text, nullable=True,
        comment="Prazos resumidos de execução/entrega")
    
    valor_referencia_dispensa = Column(Float, nullable=True,
        comment="Valor de referência para justificar dispensa")
    
    justificativa_dispensa_valor = Column(Text, nullable=True,
        comment="Por que valor baixo justifica esta dispensa")
