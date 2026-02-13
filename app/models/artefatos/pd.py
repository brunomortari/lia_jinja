""" 
Sistema LIA - Modelo PD
========================
Portaria de Designação.

Autor: Equipe TRE-GO
Data: Fevereiro 2026
"""

from sqlalchemy import Column, Integer, ForeignKey
from sqlalchemy.orm import relationship
from .base import ArtefatoBase


class PortariaDesignacao(ArtefatoBase):
    """
    Portaria de Designação - Documento virtual derivado do DFD aprovado.
    Lei 14.133/2021, Art. 7º - Designação da Equipe de Planejamento da Contratação.
    """
    __tablename__ = "portarias_designacao"

    projeto_id = Column(Integer, ForeignKey("projetos.id"), nullable=False)
    projeto = relationship("Projeto", back_populates="portarias_designacao")

    dfd_id_referencia = Column(Integer, nullable=True,
        comment="ID do DFD aprovado que originou esta portaria")
