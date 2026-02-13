""" 
Sistema LIA - Modelo JPEF
==========================
Justificativa de Preço e Escolha de Fornecedor.

Autor: Equipe TRE-GO
Data: Fevereiro 2026
"""

from sqlalchemy import Column, Integer, Text, Float, ForeignKey
from sqlalchemy.orm import relationship
from .base import ArtefatoBase


class JustificativaPrecoEscolhaFornecedor(ArtefatoBase):
    """
    Justificativa de Preço e Escolha de Fornecedor (JPEF)
    Lei 14.133/2021, Art. 75. Fluxo: Dispensa por Valor Baixo.
    """
    __tablename__ = "justificativas_preco_escolha"
    
    projeto_id = Column(Integer, ForeignKey("projetos.id"), nullable=False)
    etp_id = Column(Integer, ForeignKey("etps.id"), nullable=True)
    projeto = relationship("Projeto", foreign_keys=[projeto_id])
    etp = relationship("ETP", foreign_keys=[etp_id])
    
    justificativa_fornecedor = Column(Text, nullable=True,
        comment="Motivos da escolha deste fornecedor específico")
    
    analise_preco_praticado = Column(Text, nullable=True,
        comment="Análise do preço praticado vs mercado")
    
    preco_final_contratacao = Column(Float, nullable=True,
        comment="Preço final negociado para a contratação")
