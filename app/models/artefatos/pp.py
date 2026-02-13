""" 
Sistema LIA - Modelo PP
========================
Pesquisa de Preços.

Autor: Equipe TRE-GO
Data: Fevereiro 2026
"""

from sqlalchemy import Column, Integer, String, Float, ForeignKey, JSON
from sqlalchemy.orm import relationship
from .base import ArtefatoBase


class PesquisaPrecos(ArtefatoBase):
    """Pesquisa de Preços - documento versionado (PP)"""
    __tablename__ = "pesquisas_precos"

    # Override: PP não tem rascunho, sempre aprovado
    __mapper_args__ = {
        "polymorphic_identity": "pesquisa_precos",
    }

    projeto_id = Column(Integer, ForeignKey("projetos.id"), nullable=False)
    projeto = relationship("Projeto", back_populates="pesquisas_precos")

    artefatos_base = Column(JSON, nullable=True, comment="IDs dos artefatos (DFDs) usados como base")
    content_blocks = Column(JSON, nullable=True, comment="Estrutura JSON completa da pesquisa")
    dados_cotacao = Column(JSON, nullable=True, comment="JSON bruto retornado pela api_compras")
    valor_total_cotacao = Column(Float, nullable=True, comment="Valor total consolidado da cotacao")
    itens_cotados = Column(JSON, nullable=True, comment="Lista de itens cotados")
    fornecedores_selecionados = Column(JSON, nullable=True, comment="Lista de fornecedores selecionados")
    item_descricao = Column(String(500), nullable=True, comment="Descricao do item principal")
    preco_medio = Column(Float, nullable=True, comment="Preco medio calculado")
    quantidade_itens_encontrados = Column(Integer, nullable=True, comment="Quantidade de precos encontrados")
    document_header = Column(JSON, nullable=True, comment="Cabecalho do documento")
    audit_metadata = Column(JSON, nullable=True, comment="Metadados de auditoria")
