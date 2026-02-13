""" 
Sistema LIA - Modelo CHK
=========================
Checklist de Instrução (AGU/SEGES).

Autor: Equipe TRE-GO
Data: Fevereiro 2026
"""

from sqlalchemy import Column, Integer, String, Text, ForeignKey, JSON
from sqlalchemy.orm import relationship
from .base import ArtefatoBase


class ChecklistConformidade(ArtefatoBase):
    """
    Checklist de Instrução (AGU/SEGES)
    
    Lista de verificação baseada nos modelos da AGU para garantir conformidade legal.
    Lei 14.133/2021. Fluxo: Licitação Normal.
    """
    __tablename__ = "checklist_conformidade"
    
    projeto_id = Column(Integer, ForeignKey("projetos.id"), nullable=False)
    tr_id = Column(Integer, ForeignKey("trs.id"), nullable=True,
        comment="TR vinculado ao checklist")
    projeto = relationship("Projeto", foreign_keys=[projeto_id])
    tr = relationship("TR", foreign_keys=[tr_id])
    
    # Lista de verificação estruturada
    itens_verificacao = Column(JSON, nullable=True,
        comment="JSON: [{item, descricao, status, referencia_folhas, observacoes}, ...]. Status: sim/nao/nao_se_aplica")
    
    # Itens principais (podem ser campos individuais para facilitar consultas)
    dfd_presente = Column(String(20), nullable=True, comment="Enum: sim, nao, nao_se_aplica")
    dfd_folhas = Column(String(100), nullable=True, comment="Referência de páginas/ID no processo")
    
    etp_presente = Column(String(20), nullable=True, comment="Enum: sim, nao, nao_se_aplica")
    etp_folhas = Column(String(100), nullable=True)
    
    tr_presente = Column(String(20), nullable=True, comment="Enum: sim, nao, nao_se_aplica")
    tr_folhas = Column(String(100), nullable=True)
    
    matriz_riscos_presente = Column(String(20), nullable=True, comment="Enum: sim, nao, nao_se_aplica")
    matriz_riscos_folhas = Column(String(100), nullable=True)
    
    disponibilidade_orcamentaria_presente = Column(String(20), nullable=True, comment="Enum: sim, nao, nao_se_aplica")
    disponibilidade_orcamentaria_folhas = Column(String(100), nullable=True)
    
    parecer_juridico_presente = Column(String(20), nullable=True, comment="Enum: sim, nao, nao_se_aplica")
    parecer_juridico_folhas = Column(String(100), nullable=True)
    
    # Validação da autoridade
    validado_por = Column(String(200), nullable=True,
        comment="Nome e cargo da autoridade que validou")
    
    assinatura_eletronica = Column(JSON, nullable=True,
        comment="JSON: {nome, cargo, cpf, data, hash_assinatura}")
    
    # Observações gerais
    observacoes_gerais = Column(Text, nullable=True,
        comment="Observações ou pendências identificadas")
    
    status_conformidade = Column(String(50), nullable=True,
        comment="Enum: conforme, nao_conforme, conforme_com_ressalvas")
