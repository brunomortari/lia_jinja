"""
Sistema LIA - Router do PAC
============================
Endpoints para consulta do Plano Anual de Contratações
============================

Autor: Equipe TRE-GO
Data: Janeiro 2026
"""

from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, or_, func
from typing import List, Optional
from app.database import get_db
from app.models.pac import PAC
from app.models.user import User
from app.auth import current_active_user as get_current_user
from pydantic import BaseModel


# ========== SCHEMAS PYDANTIC ==========

class PACResponse(BaseModel):
    """Schema de resposta de item do PAC"""
    id: int
    ano: int
    tipo_pac: str | None
    iniciativa: str | None
    objetivo: str | None
    unidade_tecnica: str | None
    unidade_administrativa: str | None
    detalhamento: str | None
    descricao: str | None
    quantidade: float | None
    unidade: str | None
    frequencia: str | None
    valor_previsto: str | None
    justificativa: str | None
    prioridade: int | None
    catmat_catser: str | None
    tipo_contratacao: str | None
    fase: str | None
    
    class Config:
        from_attributes = True


# ========== ROUTER ==========

router = APIRouter()


# ========== ENDPOINTS ==========

@router.get("/", response_model=List[PACResponse])
async def listar_pac(
    ano: Optional[int] = Query(None, description="Filtrar por ano"),
    tipo_pac: Optional[str] = Query(None, description="Filtrar por tipo (Ordinário, etc)"),
    unidade: Optional[str] = Query(None, description="Filtrar por unidade"),
    tipo_contratacao: Optional[str] = Query(None, description="Filtrar por tipo de contratação"),
    search: Optional[str] = Query(None, description="Busca textual"),
    limit: int = Query(100, ge=1, le=500, description="Quantidade de resultados"),
    offset: int = Query(0, ge=0, description="Pular N resultados"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Lista itens do PAC com filtros opcionais
    """
    query = select(PAC)
    
    # Aplicar filtros
    if ano:
        query = query.filter(PAC.ano == ano)
    
    if tipo_pac:
        query = query.filter(PAC.tipo_pac == tipo_pac)
    
    if unidade:
        query = query.filter(
            or_(
                PAC.unidade_tecnica.ilike(f"%{unidade}%"),
                PAC.unidade_administrativa.ilike(f"%{unidade}%")
            )
        )
    
    if tipo_contratacao:
        query = query.filter(PAC.tipo_contratacao == tipo_contratacao)
    
    if search:
        query = query.filter(
            or_(
                PAC.detalhamento.ilike(f"%{search}%"),
                PAC.descricao.ilike(f"%{search}%"),
                PAC.justificativa.ilike(f"%{search}%")
            )
        )
    
    # Aplicar paginação
    query = query.offset(offset).limit(limit)
    result = await db.execute(query)
    items = result.scalars().all()
    
    return items


@router.get("/anos", response_model=List[int])
async def listar_anos(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Lista todos os anos disponíveis no PAC
    """
    query = select(PAC.ano).distinct().order_by(PAC.ano.desc())
    result = await db.execute(query)
    anos = result.scalars().all()
    return anos


@router.get("/tipos", response_model=List[str])
async def listar_tipos(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Lista todos os tipos de PAC disponíveis
    """
    query = select(PAC.tipo_pac).distinct().where(PAC.tipo_pac.isnot(None))
    result = await db.execute(query)
    tipos = result.scalars().all()
    return [tipo for tipo in tipos if tipo]


@router.get("/unidades", response_model=List[str])
async def listar_unidades(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Lista todas as unidades (técnicas e administrativas)
    """
    # SQLite asyncpg distinct requires caution sometimes, but should be fine here
    q1 = select(PAC.unidade_tecnica).distinct().where(PAC.unidade_tecnica.isnot(None))
    q2 = select(PAC.unidade_administrativa).distinct().where(PAC.unidade_administrativa.isnot(None))
    
    r1 = await db.execute(q1)
    r2 = await db.execute(q2)
    
    unidades_tecnicas = r1.scalars().all()
    unidades_admin = r2.scalars().all()
    
    unidades = set()
    for u in unidades_tecnicas:
        if u:
            unidades.add(u)
    for u in unidades_admin:
        if u:
            unidades.add(u)
    
    return sorted(list(unidades))


@router.get("/{pac_id}", response_model=PACResponse)
async def obter_item_pac(
    pac_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Obtém detalhes de um item específico do PAC
    """
    query = select(PAC).filter(PAC.id == pac_id)
    result = await db.execute(query)
    item = result.scalars().first()
    
    if not item:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Item do PAC com ID {pac_id} não encontrado"
        )
    
    return item


@router.get("/stats/resumo")
async def obter_estatisticas_pac(
    ano: Optional[int] = Query(None, description="Filtrar por ano"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Obtém estatísticas resumidas do PAC
    """
    # Filtro base
    filters = []
    if ano:
        filters.append(PAC.ano == ano)
    
    # Total
    query_total = select(func.count()).select_from(PAC)
    if filters:
        query_total = query_total.where(*filters)
    
    result_total = await db.execute(query_total)
    total = result_total.scalar()
    
    # Contar por tipo de PAC
    # select tipo_pac, count(*) from pac where ... group by tipo_pac
    query_tipo = select(PAC.tipo_pac, func.count(PAC.id)).group_by(PAC.tipo_pac)
    if filters:
        query_tipo = query_tipo.where(*filters)
        
    result_tipo = await db.execute(query_tipo)
    por_tipo_raw = result_tipo.all()
    
    por_tipo = {}
    for tipo, count in por_tipo_raw:
        tipo_nome = tipo if tipo else "Não classificado"
        por_tipo[tipo_nome] = count
    
    # Contar por fase
    query_fase = select(PAC.fase, func.count(PAC.id)).group_by(PAC.fase)
    if filters:
        query_fase = query_fase.where(*filters)
        
    result_fase = await db.execute(query_fase)
    por_fase_raw = result_fase.all()
    
    por_fase = {}
    for fase, count in por_fase_raw:
        fase_nome = fase if fase else "Sem fase"
        por_fase[fase_nome] = count
    
    return {
        "total_itens": total,
        "por_tipo": por_tipo,
        "por_fase": por_fase,
        "ano": ano
    }
