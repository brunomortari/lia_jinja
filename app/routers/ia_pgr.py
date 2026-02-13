"""
Sistema LIA - Router de Compatibilidade PGR (LEGADO - n8n removido)
====================================================================
⚠️ ⚠️ ⚠️ ATENÇÃO: ARQUIVO LEGADO - PROGRAMAÇÃO PARA REMOÇÃO ⚠️ ⚠️ ⚠️

Este arquivo é um WRAPPER de compatibilidade que redireciona para ia_native.py.
Endpoints de geração PGR são DEPRECATED.

**STATUS:**
- Endpoints /gerar e /gerar-stream: DEPRECATED (usar /api/ia-native/pgr/*)
- Endpoints CRUD ItemRisco: MOVIDOS para artefatos.py

**AÇÕES NECESSÁRIAS:**
1. Migrar frontend para /api/ia-native/pgr/*
2. REMOVER este arquivo após migração
3. Atualizar main.py para remover inclusão deste router

**NÃO ADICIONE NOVOS ENDPOINTS AQUI!**

Autor: Equipe TRE-GO
Data: Fevereiro 2026
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
import logging

from app.database import get_db
from app.models.user import User
from app.auth import current_active_user as auth_get_current_user
from app.models.artefatos import Riscos, ItemRisco
from app.schemas.ia_schemas import (
    GerarPGRPayload,
    ItemRiscoCreate,
    ItemRiscoUpdate,
    ItemRiscoResponse,
)
from app.utils.deprecation import log_deprecation

# Import from ia_native for delegation
from app.routers import ia_native

logger = logging.getLogger(__name__)

router = APIRouter()


# ========== COMPATIBILITY ENDPOINTS ==========

@router.post("/gerar")
async def gerar_pgr(
    payload: GerarPGRPayload,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(auth_get_current_user),
    use_test: bool = False
):
    """
    [DEPRECATED] Wrapper for ia_native.gerar_artefato_json (tipo='pgr')
    
    Mantido para compatibilidade com frontend.
    Internamente, usa agentes Python nativos.
    """
    log_deprecation("/api/pgr/gerar", "/api/ia-native/pgr/gerar")
    
    # Redirect to ia_native
    projeto_id = payload.projeto.get('projeto_id')
    prompt_adicional = payload.prompt_adicional
    
    return await ia_native.gerar_artefato_json(
        tipo_artefato="pgr",
        projeto_id=projeto_id,
        prompt_adicional=prompt_adicional,
        db=db,
        current_user=current_user
    )


@router.post("/gerar-stream")
async def gerar_pgr_stream(
    payload: GerarPGRPayload,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(auth_get_current_user),
    use_test: bool = False
):
    """
    [DEPRECATED] Wrapper for ia_native.gerar_artefato_stream (tipo='pgr')
    
    Mantido para compatibilidade com frontend.
    Internamente, usa agentes Python nativos.
    """
    log_deprecation("/api/pgr/gerar-stream", "/api/ia-native/pgr/gerar-stream")
    
    # Redirect to ia_native
    projeto_id = payload.projeto.get('projeto_id')
    prompt_adicional = payload.prompt_adicional
    
    return await ia_native.gerar_artefato_stream(
        tipo_artefato="pgr",
        projeto_id=projeto_id,
        prompt_adicional=prompt_adicional,
        db=db,
        current_user=current_user
    )


# ========== ENDPOINTS CRUD DE ITEMRISCO (Mantidos - não dependem de n8n) ==========

@router.post("/pgr/{pgr_id}/itens-risco")
async def criar_item_risco(
    pgr_id: int,
    payload: ItemRiscoCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(auth_get_current_user)
):
    """
    Cria um novo ItemRisco dentro de um PGR.
    
    Valida:
    - Probabilidade (1-5)
    - Impacto (1-5)
    - Calcula automaticamente nível_risco (probabilidade × impacto)
    - Alocação de responsabilidade (Lei 14.133/21)
    """
    # Validar que PGR existe
    result = await db.execute(
        select(Riscos).filter(Riscos.id == pgr_id)
    )
    pgr = result.scalars().first()
    if not pgr:
        raise HTTPException(status_code=404, detail="PGR não encontrado")

    # Calcular nível de risco (1-5 × 1-5 = 1-25)
    nivel_risco = payload.probabilidade * payload.impacto

    # Criar ItemRisco
    item_risco = ItemRisco(
        pgr_id=pgr_id,
        origem=payload.origem,
        fase_licitacao=payload.fase_licitacao,
        categoria=payload.categoria,
        evento=payload.evento,
        causa=payload.causa,
        consequencia=payload.consequencia,
        probabilidade=payload.probabilidade,
        impacto=payload.impacto,
        nivel_risco=nivel_risco,
        justificativa_probabilidade=payload.justificativa_probabilidade,
        justificativa_impacto=payload.justificativa_impacto,
        tipo_tratamento=payload.tipo_tratamento,
        acoes_preventivas=payload.acoes_preventivas,
        acoes_contingencia=payload.acoes_contingencia,
        alocacao_responsavel=payload.alocacao_responsavel,
        gatilho_monitoramento=payload.gatilho_monitoramento,
        responsavel_monitoramento=payload.responsavel_monitoramento,
        frequencia_monitoramento=payload.frequencia_monitoramento,
        status_risco="Identificado",
        notas=payload.notas,
    )

    db.add(item_risco)
    await db.commit()
    await db.refresh(item_risco)

    return ItemRiscoResponse.from_orm(item_risco)


@router.get("/pgr/{pgr_id}/itens-risco")
async def listar_itens_risco(
    pgr_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(auth_get_current_user)
):
    """
    Lista todos os itens de risco de um PGR.
    """
    result = await db.execute(
        select(ItemRisco).filter(ItemRisco.pgr_id == pgr_id).order_by(ItemRisco.id)
    )
    itens = result.scalars().all()

    return [ItemRiscoResponse.from_orm(item) for item in itens]


@router.get("/pgr/{pgr_id}/itens-risco/{item_id}")
async def obter_item_risco(
    pgr_id: int,
    item_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(auth_get_current_user)
):
    """
    Obtém um item de risco específico.
    """
    result = await db.execute(
        select(ItemRisco).filter(
            ItemRisco.pgr_id == pgr_id,
            ItemRisco.id == item_id
        )
    )
    item = result.scalars().first()

    if not item:
        raise HTTPException(status_code=404, detail="Item de risco não encontrado")

    return ItemRiscoResponse.from_orm(item)


@router.patch("/pgr/{pgr_id}/itens-risco/{item_id}")
async def atualizar_item_risco(
    pgr_id: int,
    item_id: int,
    payload: ItemRiscoUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(auth_get_current_user)
):
    """
    Atualiza um item de risco (PATCH - campos parciais).
    
    Recalcula nível_risco se probabilidade ou impacto forem atualizados.
    """
    result = await db.execute(
        select(ItemRisco).filter(
            ItemRisco.pgr_id == pgr_id,
            ItemRisco.id == item_id
        )
    )
    item = result.scalars().first()

    if not item:
        raise HTTPException(status_code=404, detail="Item de risco não encontrado")

    # Atualizar campos fornecidos
    update_data = payload.dict(exclude_unset=True)
    
    for key, value in update_data.items():
        setattr(item, key, value)

    # Recalcular nível se probabilidade ou impacto mudaram
    if 'probabilidade' in update_data or 'impacto' in update_data:
        item.nivel_risco = item.probabilidade * item.impacto

    await db.commit()
    await db.refresh(item)

    return ItemRiscoResponse.from_orm(item)


@router.delete("/pgr/{pgr_id}/itens-risco/{item_id}")
async def deletar_item_risco(
    pgr_id: int,
    item_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(auth_get_current_user)
):
    """
    Deleta um item de risco.
    """
    result = await db.execute(
        select(ItemRisco).filter(
            ItemRisco.pgr_id == pgr_id,
            ItemRisco.id == item_id
        )
    )
    item = result.scalars().first()

    if not item:
        raise HTTPException(status_code=404, detail="Item de risco não encontrado")

    await db.delete(item)
    await db.commit()

    return {"success": True, "message": "Item de risco deletado"}
