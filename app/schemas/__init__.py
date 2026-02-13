"""
Sistema LIA - Schemas Package
==============================
Centraliza todos os schemas Pydantic do sistema.

BREAKING CHANGES (Fev 2026):
- GerarDFDRequest → GerarArtefatoRequest
- GerarDFDPayload → GerarArtefatoPayload
- SalvarDFDRequest → SalvarArtefatoIARequest
- Campos: dfd_data → artefato_data, dfd_id → artefato_id, dfd_base_id → artefato_base_id

Schemas DEPRECATED mantidos para compatibilidade:
- AtualizarDFDRequest, EditarCampoRequest, RegenerarCampoIARequest
"""

# User schemas
from fastapi_users import schemas as fu_schemas
from typing import Optional


class UserRead(fu_schemas.BaseUser[int]):
    """Schema para leitura de usuário (retorno da API)"""
    nome: str
    cargo: Optional[str] = None
    setor: Optional[str] = None
    grupo: Optional[str] = None


class UserCreate(fu_schemas.BaseUserCreate):
    """Schema para cadastro de novo usuário"""
    nome: str
    cargo: Optional[str] = None
    setor: Optional[str] = None
    grupo: Optional[str] = None


class UserUpdate(fu_schemas.BaseUserUpdate):
    """Schema para atualização de usuário"""
    nome: Optional[str] = None
    cargo: Optional[str] = None
    setor: Optional[str] = None
    grupo: Optional[str] = None


# IA schemas
from .ia_schemas import (
    GerarArtefatoRequest,
    GerarArtefatoPayload,
    SalvarArtefatoIARequest,
    RegenerarCampoRequest,
    IACallback,
    GerarCotacaoRequest,
    SalvarPesquisaPrecosRequest,
    AtualizarDFDRequest,  # DEPRECATED - kept for backward compat
    EditarCampoRequest,   # DEPRECATED - kept for backward compat
    RegenerarCampoIARequest,  # DEPRECATED - kept for backward compat
)

# Artefato schemas
from .artefatos import (
    SalvarArtefatoRequest,
    EditarCampoArtefatoRequest,
    RegenerarCampoArtefatoRequest,
    AtualizarArtefatoRequest,
    ETPCreateSchema,
    ETPUpdateSchema,
    ETPResponseSchema,
)

__all__ = [
    # User schemas
    "UserRead",
    "UserCreate",
    "UserUpdate",
    # IA schemas
    "GerarArtefatoRequest",
    "GerarArtefatoPayload",
    "SalvarArtefatoIARequest",
    "RegenerarCampoRequest",
    "IACallback",
    "GerarCotacaoRequest",
    "SalvarPesquisaPrecosRequest",
    "AtualizarDFDRequest",  # DEPRECATED
    "EditarCampoRequest",   # DEPRECATED
    "RegenerarCampoIARequest",  # DEPRECATED
    # Artefato schemas
    "SalvarArtefatoRequest",
    "EditarCampoArtefatoRequest",
    "RegenerarCampoArtefatoRequest",
    "AtualizarArtefatoRequest",
    "ETPCreateSchema",
    "ETPUpdateSchema",
    "ETPResponseSchema",
]
