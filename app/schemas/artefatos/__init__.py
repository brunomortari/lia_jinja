"""
Schemas package for artefatos (ETP, DFD, PGR, etc).

This package centralizes all artefato-related schemas, mirroring the
organization of `app.models.artefatos`.
"""

from .base import (
    # Base request schemas
    SalvarArtefatoRequest,
    EditarCampoArtefatoRequest,
    RegenerarCampoArtefatoRequest,
    AtualizarArtefatoRequest,
    # ETP sub-schemas
    QuantidadeDetalhadaSchema,
    CenarioMercadoSchema,
    ContratacaoCorrelataSchema,
    ProvidenciaPreviaSchema,
    CriterioSustentabilidadeSchema,
    RiscoCriticoSchema,
    ResponsavelETPSchema,
    ChecklistConformidadeSchema,
    # ETP main schemas
    ETPCreateSchema,
    ETPUpdateSchema,
    ETPResponseSchema,
)

__all__ = [
    # Base request schemas
    "SalvarArtefatoRequest",
    "EditarCampoArtefatoRequest",
    "RegenerarCampoArtefatoRequest",
    "AtualizarArtefatoRequest",
    # ETP sub-schemas
    "QuantidadeDetalhadaSchema",
    "CenarioMercadoSchema",
    "ContratacaoCorrelataSchema",
    "ProvidenciaPreviaSchema",
    "CriterioSustentabilidadeSchema",
    "RiscoCriticoSchema",
    "ResponsavelETPSchema",
    "ChecklistConformidadeSchema",
    # ETP main schemas
    "ETPCreateSchema",
    "ETPUpdateSchema",
    "ETPResponseSchema",
]
