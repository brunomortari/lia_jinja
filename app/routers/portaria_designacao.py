"""
Sistema LIA - Router de Portaria de Designação
================================================
Endpoints para geração de Portaria de Designação (documento virtual do DFD aprovado).
Funções: Baixar PDF e Publicar no SEI.

Autor: Equipe TRE-GO
Data: Fevereiro 2026
"""

from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import HTMLResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from datetime import datetime
import random

from app.database import get_db
from app.models.projeto import Projeto
from app.models.artefatos import DFD, PortariaDesignacao
from app.models.user import User
from app.auth import current_active_user as auth_get_current_user
from app.routers.views.common import templates
from app.utils.datetime_utils import now_brasilia

router = APIRouter()


async def _get_dfd_aprovado(projeto_id: int, db: AsyncSession) -> DFD:
    """Busca o DFD aprovado do projeto. Retorna 404 se não houver."""
    result = await db.execute(
        select(DFD).filter(
            DFD.projeto_id == projeto_id,
            DFD.status.in_(["aprovado", "publicado"])
        ).order_by(DFD.data_aprovacao.desc())
    )
    dfd = result.scalars().first()
    if not dfd:
        raise HTTPException(
            status_code=404,
            detail="DFD aprovado não encontrado. Portaria só pode ser gerada a partir de DFD aprovado."
        )
    return dfd


async def _get_or_create_portaria(projeto_id: int, db: AsyncSession) -> PortariaDesignacao:
    """Busca ou cria a Portaria de Designação para o projeto."""
    result = await db.execute(
        select(PortariaDesignacao).filter(PortariaDesignacao.projeto_id == projeto_id)
    )
    portaria = result.scalars().first()
    
    if not portaria:
        # Criar novo registro de Portaria
        dfd = await _get_dfd_aprovado(projeto_id, db)
        portaria = PortariaDesignacao(
            projeto_id=projeto_id,
            dfd_id_referencia=dfd.id,
            versao=1,
            status="rascunho",
            data_criacao=now_brasilia(),
            data_atualizacao=now_brasilia()
        )
        db.add(portaria)
        await db.commit()
        await db.refresh(portaria)
    
    return portaria


@router.get("/{projeto_id}/print", response_class=HTMLResponse)
async def gerar_portaria_print(
    request: Request,
    projeto_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(auth_get_current_user)
):
    """
    Gera visualização de impressão (PDF via browser) da Portaria de Designação.
    A Portaria é renderizada a partir do DFD aprovado.
    """
    # Buscar projeto
    result = await db.execute(select(Projeto).filter(Projeto.id == projeto_id))
    projeto = result.scalars().first()
    if not projeto:
        raise HTTPException(status_code=404, detail="Projeto não encontrado")
    
    # Buscar/criar Portaria
    portaria = await _get_or_create_portaria(projeto_id, db)
    
    # Buscar DFD aprovado
    dfd = await _get_dfd_aprovado(projeto_id, db)
    
    # Renderizar template
    return templates.TemplateResponse(
        "portaria_designacao.html",
        {
            "request": request,
            "projeto": projeto,
            "portaria": portaria,
            "dfd": dfd,
            "autoridade_nome": "[NOME DA AUTORIDADE]",
            "autoridade_cargo": "[CARGO DA AUTORIDADE]",
            "data_geracao": now_brasilia()
        }
    )


@router.post("/{projeto_id}/publicar-sei")
async def publicar_portaria_sei(
    projeto_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(auth_get_current_user)
):
    """
    Publica a Portaria de Designação no SEI.
    Simula integração com SEI gerando protocolo mock.
    """
    # Buscar projeto
    result = await db.execute(select(Projeto).filter(Projeto.id == projeto_id))
    projeto = result.scalars().first()
    if not projeto:
        raise HTTPException(status_code=404, detail="Projeto não encontrado")
    
    # Buscar/criar Portaria
    portaria = await _get_or_create_portaria(projeto_id, db)
    
    # Buscar DFD aprovado (validação)
    dfd = await _get_dfd_aprovado(projeto_id, db)
    
    # Simular publicação SEI
    if portaria.protocolo_sei:
        return {
            "success": True,
            "message": "Portaria já foi publicada no SEI",
            "protocolo_sei": portaria.protocolo_sei
        }
    
    # Gerar protocolo SEI mock
    protocolo_number = f"000{random.randint(1000, 9999)}-{random.randint(10, 99)}.2026.6.09.0000"
    
    portaria.protocolo_sei = {
        "numero": protocolo_number,
        "assunto": f"Portaria de Designação - {projeto.titulo}",
        "link": f"https://sei.tre-go.gov.br/sei/modulos/pesquisa/md_pesq_documento_consulta_externa.php?{protocolo_number}",
        "data_publicacao": now_brasilia().isoformat()
    }
    portaria.status = "publicado"
    portaria.data_atualizacao = now_brasilia()
    
    db.add(portaria)
    await db.commit()
    await db.refresh(portaria)
    
    return {
        "success": True,
        "message": "Portaria publicada no SEI com sucesso",
        "protocolo_sei": portaria.protocolo_sei
    }


@router.get("/{projeto_id}/info")
async def obter_info_portaria(
    projeto_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(auth_get_current_user)
):
    """
    Obtém informações da Portaria de Designação (status, versão, protocolo SEI).
    Retorna None se DFD não estiver aprovado.
    """
    # Verificar se existe DFD aprovado
    result = await db.execute(
        select(DFD).filter(
            DFD.projeto_id == projeto_id,
            DFD.status.in_(["aprovado", "publicado"])
        )
    )
    dfd = result.scalars().first()
    
    if not dfd:
        return {
            "portaria_disponivel": False,
            "motivo": "DFD não aprovado"
        }
    
    # Buscar/criar Portaria
    portaria = await _get_or_create_portaria(projeto_id, db)
    
    return {
        "portaria_disponivel": True,
        "id": portaria.id,
        "versao": portaria.versao,
        "status": portaria.status,
        "data_criacao": portaria.data_criacao.isoformat() if portaria.data_criacao else None,
        "data_atualizacao": portaria.data_atualizacao.isoformat() if portaria.data_atualizacao else None,
        "protocolo_sei": portaria.protocolo_sei,
        "dfd_id_referencia": portaria.dfd_id_referencia
    }
