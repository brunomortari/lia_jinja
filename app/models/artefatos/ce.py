""" 
Sistema LIA - Modelo CE
========================
Certidão de Enquadramento na Modalidade de Dispensa.

Autor: Equipe TRE-GO
Data: Fevereiro 2026
"""

from sqlalchemy import Column, Integer, String, Text, Float, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from .base import ArtefatoBase


class CertidaoEnquadramento(ArtefatoBase):
    """
    Certidão de Enquadramento na Modalidade de Dispensa (CE)
    Lei 14.133/2021, Art. 75. Fluxo: Dispensa por Valor Baixo.
    """
    __tablename__ = "certidoes_enquadramento"
    
    projeto_id = Column(Integer, ForeignKey("projetos.id"), nullable=False)
    etp_id = Column(Integer, ForeignKey("etps.id"), nullable=True)
    projeto = relationship("Projeto", foreign_keys=[projeto_id])
    etp = relationship("ETP", foreign_keys=[etp_id])
    
    limite_legal_aplicavel = Column(Float, nullable=True,
        comment="Limite legal para enquadramento (ex: R$ 8.800)")
    
    valor_contratacao_analisada = Column(Float, nullable=True,
        comment="Valor da contratação analisada")
    
    conclusao_enquadramento = Column(Text, nullable=True,
        comment="Conclusão sobre o enquadramento legal")
    
    artigo_lei_aplicavel = Column(String(50), nullable=True,
        comment="Artigo da Lei 14.133/21 aplicável (ex: Art. 75, I)")
    
    responsavel_certificacao = Column(String(200), nullable=True,
        comment="Nome e cargo do responsável")
    
    data_certificacao = Column(DateTime, nullable=True)
