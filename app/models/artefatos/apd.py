""" 
Sistema LIA - Modelo APD
=========================
Aviso de Publicidade Direta (Dispensa de Licitação).

Autor: Equipe TRE-GO
Data: Fevereiro 2026
"""

from sqlalchemy import Column, Integer, String, Text, Float, Date, DateTime, ForeignKey, JSON
from sqlalchemy.orm import relationship
from .base import ArtefatoBase


class AvisoPublicidadeDireta(ArtefatoBase):
    """
    Aviso de Dispensa de Licitação
    
    Publicidade necessária para garantir que outros interessados possam ofertar
    (no caso de dispensa eletrônica).
    Lei 14.133/2021, Art. 75/74. Fluxo: Contratação Direta.
    """
    __tablename__ = "aviso_publicidade_direta"
    
    projeto_id = Column(Integer, ForeignKey("projetos.id"), nullable=False)
    tr_id = Column(Integer, ForeignKey("trs.id"), nullable=True,
        comment="TR vinculado ao aviso")
    projeto = relationship("Projeto", foreign_keys=[projeto_id])
    tr = relationship("TR", foreign_keys=[tr_id])
    
    # Fundamento Legal
    fundamento_legal = Column(String(100), nullable=True,
        comment="Inciso específico do Art. 75 ou Art. 74 da Lei 14.133/21")
    
    artigo_lei = Column(String(50), nullable=True,
        comment="Ex: 'Art. 75, II' ou 'Art. 74, I'")
    
    justificativa_legal = Column(Text, nullable=True,
        comment="Explicação do enquadramento na hipótese de dispensa")
    
    # Valor Estimado
    valor_estimado = Column(Float, nullable=True,
        comment="Teto que a administração se propõe a pagar")
    
    metodologia_valor = Column(Text, nullable=True,
        comment="Como foi calculado o valor estimado")
    
    # Prazo de Manifestação
    prazo_manifestacao_dias = Column(Integer, nullable=True,
        comment="Número de dias úteis para manifestação (mínimo 3 para dispensa eletrônica)")
    
    data_inicio_prazo = Column(Date, nullable=True,
        comment="Data de início do prazo para manifestação")
    
    data_fim_prazo = Column(Date, nullable=True,
        comment="Data de término do prazo para manifestação")
    
    # Publicação
    data_publicacao_pncp = Column(DateTime, nullable=True,
        comment="Data de publicação no PNCP")
    
    link_pncp = Column(String(500), nullable=True,
        comment="Link para o aviso no Portal Nacional de Contratações Públicas")
    
    data_publicacao_site_orgao = Column(DateTime, nullable=True,
        comment="Data de publicação no site do órgão")
    
    link_site_orgao = Column(String(500), nullable=True,
        comment="Link para o aviso no site do órgão")
    
    # Extrato publicado
    numero_aviso = Column(String(50), nullable=True,
        comment="Número de identificação do aviso")
    
    extrato_aviso = Column(Text, nullable=True,
        comment="Extrato resumido do aviso publicado")
