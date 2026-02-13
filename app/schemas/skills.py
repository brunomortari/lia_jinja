"""
Schemas Pydantic para Skills (Habilidades).
"""
from pydantic import BaseModel, Field, field_validator
from typing import Optional, List
from datetime import datetime

# Tipos de artefato validos
TIPOS_ARTEFATO_VALIDOS = {"dfd", "etp", "tr", "riscos", "edital", "pesquisa_precos"}


class SkillCreate(BaseModel):
    """Schema para criacao de skill."""
    nome: str = Field(..., min_length=3, max_length=200)
    descricao: Optional[str] = Field(None, max_length=1000)
    instrucoes: str = Field(..., min_length=10, max_length=5000)


class SkillUpdate(BaseModel):
    """Schema para atualizacao de skill (todos opcionais)."""
    nome: Optional[str] = Field(None, min_length=3, max_length=200)
    descricao: Optional[str] = Field(None, max_length=1000)
    instrucoes: Optional[str] = Field(None, min_length=10, max_length=5000)
    ativa: Optional[bool] = None


class SkillResponse(BaseModel):
    """Schema de resposta de skill."""
    id: int
    nome: str
    descricao: Optional[str]
    instrucoes: str
    escopo: str
    ativa: bool
    usuario_id: Optional[int]
    data_criacao: datetime
    data_atualizacao: datetime

    class Config:
        from_attributes = True


class ProjetoSkillCreate(BaseModel):
    """Schema para associar skill a projeto."""
    skill_id: int


class ProjetoSkillUpdate(BaseModel):
    """Schema para atualizar associacao (ligar/desligar)."""
    ativa_no_projeto: bool


class ProjetoSkillResponse(BaseModel):
    """Schema de resposta da associacao projeto-skill."""
    id: int
    skill_id: int
    ativa_no_projeto: bool
    skill: SkillResponse

    class Config:
        from_attributes = True


class SkillChatMessage(BaseModel):
    """Schema para mensagem no wizard de criacao de skill."""
    content: str = Field(..., min_length=1, max_length=2000)
    history: List[dict] = Field(default_factory=list)
    model: Optional[str] = None
