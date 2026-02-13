""" 
Sistema LIA - Modelo ADE
=========================
Aviso de Dispensa Eletrônica.

Autor: Equipe TRE-GO
Data: Fevereiro 2026
"""

from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from .base import ArtefatoBase


class AvisoDispensaEletronica(ArtefatoBase):
    """
    Aviso de Dispensa Eletrônica (ADE)
    Lei 14.133/2021, Art. 75. Fluxo: Dispensa por Valor Baixo.
    """
    __tablename__ = "avisos_dispensa_eletronica"
    
    projeto_id = Column(Integer, ForeignKey("projetos.id"), nullable=False)
    etp_id = Column(Integer, ForeignKey("etps.id"), nullable=True)
    projeto = relationship("Projeto", foreign_keys=[projeto_id])
    etp = relationship("ETP", foreign_keys=[etp_id])
    
    numero_aviso = Column(String(50), nullable=True,
        comment="Número do aviso atribuído pelo portal")
    
    data_publicacao = Column(DateTime, nullable=True,
        comment="Data de publicação no portal eletrônico")
    
    descricao_objeto_aviso = Column(Text, nullable=True)
    
    link_portal = Column(String(500), nullable=True,
        comment="URL do aviso no portal eletrônico")
    
    protocolo_publicacao = Column(String(50), nullable=True,
        comment="Número de protocolo do aviso publicado")
