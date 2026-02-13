""" 
Sistema LIA - Modelo TAFO
==========================
Termo de Aceitação do Fornecedor Pela Administração.

Autor: Equipe TRE-GO
Data: Fevereiro 2026
"""

from sqlalchemy import Column, Integer, String, Text, Float, ForeignKey, JSON
from sqlalchemy.orm import relationship
from .base import ArtefatoBase


class TermoAceiteFornecedorOrgao(ArtefatoBase):
    """
    Termo de Aceitação do Fornecedor Pela Administração (TAFO)
    Lei 14.133/2021, Art. 37. Fluxo: Adesão a Ata.
    """
    __tablename__ = "termos_aceite_fornecedor"
    
    projeto_id = Column(Integer, ForeignKey("projetos.id"), nullable=False)
    etp_id = Column(Integer, ForeignKey("etps.id"), nullable=True)
    projeto = relationship("Projeto", foreign_keys=[projeto_id])
    etp = relationship("ETP", foreign_keys=[etp_id])
    
    nome_fornecedor = Column(String(300), nullable=True)
    cnpj_fornecedor = Column(String(20), nullable=True)
    
    descricao_objeto_aceito = Column(Text, nullable=True,
        comment="Descrição detalhada do objeto aceito da ata")
    
    preco_aceito = Column(Float, nullable=True, comment="Preço final aceito da ata")
    
    documentos_anexados = Column(JSON, nullable=True,
        comment="JSON: [{tipo, nome_arquivo, data_upload, tamanho}, ...]")
    
    responsaveis_assinatura = Column(JSON, nullable=True,
        comment="JSON: [{nome, cargo, data}, ...]")
    
    observacoes = Column(Text, nullable=True)
