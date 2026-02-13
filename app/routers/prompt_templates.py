"""
Router para gerenciamento de templates de prompts
Permite editar, versionar e ativar/desativar prompts sem deploy de código
"""
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, delete
from pydantic import BaseModel, Field

from app.database import get_db
from app.models.prompt_template import PromptTemplate
from app.services.agents.prompt_loader import clear_prompt_cache
from app.auth import current_active_user, User

router = APIRouter(
    prefix="/api/prompt-templates",
    tags=["Prompt Templates"]
)


# Schemas
class PromptTemplateCreate(BaseModel):
    agent_type: str = Field(..., description="Tipo do agente (dfd, etp, pgr, etc.)")
    prompt_type: str = Field(..., description="Tipo do prompt (system, system_chat, system_generate)")
    conteudo: str = Field(..., description="Conteúdo do prompt")
    versao: str = Field(default="1.0", description="Versão do prompt")
    ativa: bool = Field(default=True, description="Se este prompt está ativo")
    ordem: int = Field(default=0, description="Ordem de aplicação")
    descricao: Optional[str] = Field(None, description="Descrição opcional")


class PromptTemplateUpdate(BaseModel):
    conteudo: Optional[str] = None
    versao: Optional[str] = None
    ativa: Optional[bool] = None
    ordem: Optional[int] = None
    descricao: Optional[str] = None


class PromptTemplateResponse(BaseModel):
    id: int
    agent_type: str
    prompt_type: str
    conteudo: str
    versao: str
    ativa: bool
    ordem: int
    descricao: Optional[str]
    
    class Config:
        from_attributes = True


@router.get("/", response_model=List[PromptTemplateResponse])
async def listar_prompts(
    agent_type: Optional[str] = None,
    prompt_type: Optional[str] = None,
    ativa: Optional[bool] = None,
    session: AsyncSession = Depends(get_db),
    user: User = Depends(current_active_user)
):
    """
    Lista todos os templates de prompts com filtros opcionais.
    """
    stmt = select(PromptTemplate)
    
    if agent_type:
        stmt = stmt.where(PromptTemplate.agent_type == agent_type)
    if prompt_type:
        stmt = stmt.where(PromptTemplate.prompt_type == prompt_type)
    if ativa is not None:
        stmt = stmt.where(PromptTemplate.ativa == ativa)
    
    stmt = stmt.order_by(
        PromptTemplate.agent_type,
        PromptTemplate.prompt_type,
        PromptTemplate.ordem
    )
    
    result = await session.execute(stmt)
    prompts = result.scalars().all()
    
    return prompts


@router.get("/{prompt_id}", response_model=PromptTemplateResponse)
async def obter_prompt(
    prompt_id: int,
    session: AsyncSession = Depends(get_db),
    user: User = Depends(current_active_user)
):
    """
    Obtém um template de prompt específico.
    """
    stmt = select(PromptTemplate).where(PromptTemplate.id == prompt_id)
    result = await session.execute(stmt)
    prompt = result.scalar_one_or_none()
    
    if not prompt:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Prompt template {prompt_id} não encontrado"
        )
    
    return prompt


@router.post("/", response_model=PromptTemplateResponse, status_code=status.HTTP_201_CREATED)
async def criar_prompt(
    prompt_data: PromptTemplateCreate,
    session: AsyncSession = Depends(get_db),
    user: User = Depends(current_active_user)
):
    """
    Cria um novo template de prompt.
    
    Se ativa=True, desativa outros prompts do mesmo agent_type+prompt_type.
    """
    # Se o novo prompt é ativo, desativar outros do mesmo tipo
    if prompt_data.ativa:
        await _desativar_outros_prompts(
            session,
            prompt_data.agent_type,
            prompt_data.prompt_type
        )
    
    prompt = PromptTemplate(**prompt_data.model_dump())
    session.add(prompt)
    await session.commit()
    await session.refresh(prompt)
    
    # Limpar cache
    clear_prompt_cache()
    
    return prompt


@router.put("/{prompt_id}", response_model=PromptTemplateResponse)
async def atualizar_prompt(
    prompt_id: int,
    prompt_data: PromptTemplateUpdate,
    session: AsyncSession = Depends(get_db),
    user: User = Depends(current_active_user)
):
    """
    Atualiza um template de prompt existente.
    """
    stmt = select(PromptTemplate).where(PromptTemplate.id == prompt_id)
    result = await session.execute(stmt)
    prompt = result.scalar_one_or_none()
    
    if not prompt:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Prompt template {prompt_id} não encontrado"
        )
    
    # Atualizar campos
    update_data = prompt_data.model_dump(exclude_unset=True)
    
    # Se está ativando este prompt, desativar outros do mesmo tipo
    if update_data.get("ativa") is True:
        await _desativar_outros_prompts(
            session,
            prompt.agent_type,
            prompt.prompt_type,
            exclude_id=prompt_id
        )
    
    for field, value in update_data.items():
        setattr(prompt, field, value)
    
    await session.commit()
    await session.refresh(prompt)
    
    # Limpar cache
    clear_prompt_cache()
    
    return prompt


@router.post("/{prompt_id}/versionar", response_model=PromptTemplateResponse)
async def criar_versao(
    prompt_id: int,
    nova_versao: str,
    ativar: bool = False,
    session: AsyncSession = Depends(get_db),
    user: User = Depends(current_active_user)
):
    """
    Cria uma nova versão de um prompt existente.
    
    Args:
        nova_versao: Nome da nova versão (ex: "1.1", "2.0")
        ativar: Se deve ativar a nova versão (desativando as outras)
    """
    stmt = select(PromptTemplate).where(PromptTemplate.id == prompt_id)
    result = await session.execute(stmt)
    prompt_original = result.scalar_one_or_none()
    
    if not prompt_original:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Prompt template {prompt_id} não encontrado"
        )
    
    # Se vai ativar a nova versão, desativar outras
    if ativar:
        await _desativar_outros_prompts(
            session,
            prompt_original.agent_type,
            prompt_original.prompt_type
        )
    
    # Criar nova versão
    novo_prompt = PromptTemplate(
        agent_type=prompt_original.agent_type,
        prompt_type=prompt_original.prompt_type,
        conteudo=prompt_original.conteudo,
        versao=nova_versao,
        ativa=ativar,
        ordem=prompt_original.ordem,
        descricao=f"Versão {nova_versao} de {prompt_original.descricao or prompt_original.agent_type}"
    )
    
    session.add(novo_prompt)
    await session.commit()
    await session.refresh(novo_prompt)
    
    # Limpar cache
    clear_prompt_cache()
    
    return novo_prompt


@router.delete("/{prompt_id}", status_code=status.HTTP_204_NO_CONTENT)
async def deletar_prompt(
    prompt_id: int,
    session: AsyncSession = Depends(get_db),
    user: User = Depends(current_active_user)
):
    """
    Deleta um template de prompt.
    
    CUIDADO: Isso pode quebrar agentes se não houver outro prompt ativo!
    """
    stmt = delete(PromptTemplate).where(PromptTemplate.id == prompt_id)
    result = await session.execute(stmt)
    
    if result.rowcount == 0:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Prompt template {prompt_id} não encontrado"
        )
    
    await session.commit()
    
    # Limpar cache
    clear_prompt_cache()


# Função auxiliar
async def _desativar_outros_prompts(
    session: AsyncSession,
    agent_type: str,
    prompt_type: str,
    exclude_id: Optional[int] = None
):
    """
    Desativa todos os prompts do mesmo agent_type+prompt_type,
    opcionalmente excluindo um ID específico.
    """
    stmt = update(PromptTemplate).where(
        PromptTemplate.agent_type == agent_type,
        PromptTemplate.prompt_type == prompt_type
    ).values(ativa=False)
    
    if exclude_id:
        stmt = stmt.where(PromptTemplate.id != exclude_id)
    
    await session.execute(stmt)
