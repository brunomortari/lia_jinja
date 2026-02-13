""" 
Sistema LIA - Modelo RDVE
==========================
Relatório de Demonstração de Vantagem Econômica.

Autor: Equipe TRE-GO
Data: Fevereiro 2026
"""

from sqlalchemy import Column, Integer, Text, Float, ForeignKey, JSON
from sqlalchemy.orm import relationship
from .base import ArtefatoBase


class RelatorioVantagemEconomica(ArtefatoBase):
    """
    Relatório de Demonstração de Vantagem Econômica (RDVE)
    Lei 14.133/2021, Art. 37. Fluxo: Adesão a Ata.
    """
    __tablename__ = "relatorios_vantagem_economica"
    
    projeto_id = Column(Integer, ForeignKey("projetos.id"), nullable=False)
    etp_id = Column(Integer, ForeignKey("etps.id"), nullable=True)
    projeto = relationship("Projeto", foreign_keys=[projeto_id])
    etp = relationship("ETP", foreign_keys=[etp_id])
    
    comparativo_precos = Column(JSON, nullable=True,
        comment="JSON: [{fornecedor, preco_ata, preco_direto, economia_percentual}, ...]")
    
    custo_processamento_adesao = Column(Float, nullable=True,
        comment="Custos administrativos da adesão")
    
    custo_processamento_direto = Column(Float, nullable=True,
        comment="Custos administrativos de contratação direta")
    
    conclusao_tecnica = Column(Text, nullable=True,
        comment="Conclusão técnica sobre a vantagem econômica")
    
    percentual_economia = Column(Float, nullable=True, comment="Percentual de economia (%)")
    valor_economia_total = Column(Float, nullable=True, comment="Valor economizado (R$)")
