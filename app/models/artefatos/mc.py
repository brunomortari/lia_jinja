""" 
Sistema LIA - Modelo MC
========================
Minuta de Contrato.

Autor: Equipe TRE-GO
Data: Fevereiro 2026
"""

from sqlalchemy import Column, Integer, String, Text, Float, Date, ForeignKey, JSON
from sqlalchemy.orm import relationship
from .base import ArtefatoBase


class MinutaContrato(ArtefatoBase):
    """
    Minuta de Contrato
    
    Rascunho do compromisso futuro entre a administração e o vencedor.
    Anexo obrigatório do edital que detalha a execução.
    Lei 14.133/2021. Fluxo: Licitação Normal.
    """
    __tablename__ = "minuta_contrato"
    
    projeto_id = Column(Integer, ForeignKey("projetos.id"), nullable=False)
    edital_id = Column(Integer, ForeignKey("editais.id"), nullable=True,
        comment="Edital ao qual esta minuta está vinculada")
    projeto = relationship("Projeto", foreign_keys=[projeto_id])
    edital = relationship("Edital", foreign_keys=[edital_id])
    
    # Cláusulas de Obrigações
    obrigacoes_contratada = Column(Text, nullable=True,
        comment="Responsabilidades da contratada")
    
    obrigacoes_contratante = Column(Text, nullable=True,
        comment="Responsabilidades da contratante")
    
    obrigacoes_estruturadas = Column(JSON, nullable=True,
        comment="JSON: {contratada: [{clausula, descricao}, ...], contratante: [{clausula, descricao}, ...]}")
    
    # Condições de Pagamento
    forma_pagamento = Column(Text, nullable=True,
        comment="Descrição da forma de pagamento")
    
    prazo_pagamento = Column(String(100), nullable=True,
        comment="Ex: '30 dias após apresentação da nota fiscal'")
    
    fluxo_liquidacao = Column(Text, nullable=True,
        comment="Fluxo de liquidação e emissão de nota fiscal")
    
    # Vigência e Prorrogação
    data_inicio = Column(Date, nullable=True,
        comment="Data de início do contrato")
    
    data_termino = Column(Date, nullable=True,
        comment="Data de término do contrato")
    
    prazo_vigencia = Column(String(100), nullable=True,
        comment="Ex: '12 meses'")
    
    possibilidade_prorrogacao = Column(String(20), nullable=True,
        comment="Enum: sim, nao")
    
    condicoes_prorrogacao = Column(Text, nullable=True,
        comment="Condições para prorrogação do contrato")
    
    prazo_maximo_prorrogacao = Column(String(100), nullable=True,
        comment="Ex: 'Até 60 meses conforme Art. 107 da Lei 14.133/21'")
    
    # Garantias
    exige_garantia = Column(String(20), nullable=True,
        comment="Enum: sim, nao")
    
    tipo_garantia = Column(String(100), nullable=True,
        comment="Ex: 'Seguro-garantia, caução em dinheiro, fiança bancária'")
    
    percentual_garantia = Column(Float, nullable=True,
        comment="Percentual sobre o valor do contrato (ex: 5%)")
    
    valor_garantia = Column(Float, nullable=True,
        comment="Valor da garantia em R$")
    
    # Outras cláusulas importantes
    rescisao = Column(Text, nullable=True,
        comment="Condições de rescisão do contrato")
    
    penalidades = Column(Text, nullable=True,
        comment="Penalidades por descumprimento")
    
    lei_aplicavel = Column(Text, nullable=True,
        comment="Lei e regulamentos aplicáveis ao contrato")
    
    foro_competente = Column(String(200), nullable=True,
        comment="Foro competente para dirimir conflitos")
