"""
Sistema LIA - Router de DFD (Documento de Formalizacao da Demanda)
===================================================================
Endpoints para edicao, visualizacao e gerenciamento de DFDs.

Para geracao de DFD via IA, veja: routers/ia.py

Autor: Equipe TRE-GO
Data: Janeiro 2026
"""

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import HTMLResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload
from datetime import datetime
import json
import logging

from app.database import get_db
from app.utils.datetime_utils import now_brasilia
from app.models.artefatos import DFD, DFD_CAMPOS_CONFIG
from app.models.user import User
from app.auth import current_active_user as auth_get_current_user
from app.schemas.ia_schemas import (
    AtualizarDFDRequest,
    EditarCampoRequest,
)

logger = logging.getLogger(__name__)

router = APIRouter()


# ========== ENDPOINTS DE CONFIGURACAO ==========

@router.get("/campos-config")
async def obter_config_campos(
    current_user: User = Depends(auth_get_current_user)
):
    """
    Retorna a configuracao dos campos do DFD (tipos A e B).

    - Tipo A: Apenas edicao manual
    - Tipo B: Pode ser regenerado por IA
    """
    return DFD_CAMPOS_CONFIG


# ========== ENDPOINTS DE LEITURA ==========

@router.get("/{dfd_id}")
async def obter_dfd(
    dfd_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(auth_get_current_user)
):
    """
    Retorna os dados completos de um DFD.

    Args:
        dfd_id: ID do DFD

    Returns:
        DFD completo com configuracao de campos e historico de versoes
    """
    result = await db.execute(select(DFD).filter(DFD.id == dfd_id))
    dfd = result.scalars().first()

    if not dfd:
        raise HTTPException(status_code=404, detail="DFD nao encontrado")

    # Buscar todas as versoes para historico
    result = await db.execute(
        select(DFD)
        .filter(DFD.projeto_id == dfd.projeto_id)
        .order_by(DFD.versao.desc())
    )
    todas_versoes = result.scalars().all()

    return {
        "dfd": dfd.to_dict(),
        "campos_config": DFD_CAMPOS_CONFIG,
        "versoes": [
            {
                "versao": v.versao,
                "data": v.data_criacao.isoformat() if v.data_criacao else None,
                "id": v.id
            }
            for v in todas_versoes
        ]
    }


# ========== ENDPOINTS DE EDICAO ==========

@router.put("/{dfd_id}")
async def atualizar_dfd_completo(
    dfd_id: int,
    request: AtualizarDFDRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(auth_get_current_user)
):
    """
    Atualiza um DFD completo.

    Args:
        dfd_id: ID do DFD
        request: Dados para atualizacao

    Returns:
        DFD atualizado

    Raises:
        404: DFD nao encontrado
        400: DFD publicado no SEI (imutavel)
    """
    result = await db.execute(select(DFD).filter(DFD.id == dfd_id))
    dfd = result.scalars().first()

    if not dfd:
        raise HTTPException(status_code=404, detail="DFD nao encontrado")

    # Publicado no SEI: bloqueado para edição
    if dfd.protocolo_sei:
        raise HTTPException(
            status_code=400,
            detail="Este DFD ja foi publicado no SEI e nao pode ser modificado."
        )

    update_data = request.model_dump(exclude_unset=True)
    
    # Se está aprovando, verificar se já existe outro aprovado
    if update_data.get("status") == "aprovado" and dfd.status != "aprovado":
        if await DFD.tem_versao_aprovada(dfd.projeto_id, db, excluir_id=dfd.id):
            raise HTTPException(
                status_code=400,
                detail="Já existe uma versão aprovada deste DFD."
            )

    for field, value in update_data.items():
        if hasattr(dfd, field):
            setattr(dfd, field, value)

    dfd.data_atualizacao = now_brasilia()

    if update_data.get("status") == "aprovado":
        dfd.data_aprovacao = now_brasilia()

    await db.commit()
    await db.refresh(dfd)

    return {
        "message": "DFD atualizado com sucesso!",
        "dfd": dfd.to_dict()
    }


@router.post("/editar-campo")
async def editar_campo_manual(
    request: EditarCampoRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(auth_get_current_user)
):
    """
    Edita um campo do DFD manualmente.

    Args:
        request: ID do DFD, nome do campo e novo valor

    Returns:
        Confirmacao com campo atualizado
    """
    result = await db.execute(select(DFD).filter(DFD.id == request.dfd_id))
    dfd = result.scalars().first()

    if not dfd:
        raise HTTPException(status_code=404, detail="DFD nao encontrado")

    # Validar se pode editar
    dfd.validar_edicao()

    # Verificar se campo existe
    if request.campo not in DFD_CAMPOS_CONFIG:
        raise HTTPException(
            status_code=400,
            detail=f"Campo '{request.campo}' nao existe"
        )

    # Atualizar campo (tratamento especial para valor_estimado)
    if request.campo == "valor_estimado":
        try:
            valor = request.valor.replace(",", ".").replace("R$", "").strip()
            setattr(dfd, request.campo, float(valor) if valor else None)
        except ValueError:
            setattr(dfd, request.campo, None)
    else:
        setattr(dfd, request.campo, request.valor)

    # Registrar edição
    dfd.registrar_edicao_campo(request.campo)

    await db.commit()
    await db.refresh(dfd)

    return {
        "message": f"Campo '{request.campo}' atualizado com sucesso",
        "dfd_id": dfd.id,
        "campo": request.campo,
        "valor": getattr(dfd, request.campo)
    }


# ========== ENDPOINTS DE FLUXO ==========

@router.post("/{dfd_id}/aprovar")
async def aprovar_dfd(
    dfd_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(auth_get_current_user)
):
    """
    Aprova o DFD, tornando-o imutavel.

    Args:
        dfd_id: ID do DFD

    Returns:
        Confirmacao de aprovacao
    """
    result = await db.execute(select(DFD).filter(DFD.id == dfd_id))
    dfd = result.scalars().first()

    if not dfd:
        raise HTTPException(status_code=404, detail="DFD nao encontrado")

    # Validar se pode editar
    dfd.validar_edicao()
    
    # Verificar se já está aprovado
    if dfd.esta_aprovado:
        return {"message": "DFD já está aprovado", "status": "aprovado"}
    
    # Verificar se já existe OUTRA versão aprovada
    if await DFD.tem_versao_aprovada(dfd.projeto_id, db, excluir_id=dfd.id):
        raise HTTPException(
            status_code=400,
            detail="Já existe uma versão aprovada deste DFD. Apenas uma versão pode ser aprovada."
        )

    dfd.aprovar()

    await db.commit()

    return {"message": "DFD aprovado com sucesso", "status": "aprovado"}


@router.delete("/{dfd_id}")
async def deletar_dfd(
    dfd_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(auth_get_current_user)
):
    """
    Deleta um DFD permanentemente.

    Args:
        dfd_id: ID do DFD

    Returns:
        Confirmacao de delecao

    Raises:
        404: DFD nao encontrado
        400: DFD ja publicado no SEI
    """
    result = await db.execute(select(DFD).filter(DFD.id == dfd_id))
    dfd = result.scalars().first()

    if not dfd:
        raise HTTPException(status_code=404, detail="DFD nao encontrado")

    dfd.validar_edicao()

    await db.delete(dfd)
    await db.commit()

    return {"message": "DFD deletado com sucesso"}


async def criar_nova_versao(
    dfd_id: int,
    db: AsyncSession = Depends(get_db)
):
    """
    Cria uma nova versao do DFD (copia os dados para um novo registro).
    
    Regra de negócio: Não pode criar nova versão se já existe uma aprovada.

    Args:
        dfd_id: ID do DFD base

    Returns:
        Informacoes da nova versao criada
    """
    result = await db.execute(select(DFD).filter(DFD.id == dfd_id))
    dfd = result.scalars().first()

    if not dfd:
        raise HTTPException(status_code=404, detail="DFD nao encontrado")

    dfd.validar_edicao()

    # Verificar se já existe versão aprovada (bloqueia novas versões)
    if await DFD.tem_versao_aprovada(dfd.projeto_id, db):
        raise HTTPException(
            status_code=400, 
            detail="Já existe uma versão aprovada deste DFD. Não é possível criar novas versões."
        )

    # Calcular proxima versao e clonar
    nova_versao_num = await DFD.proxima_versao(dfd.projeto_id, db)
    novo_dfd = dfd.clonar_para_nova_versao(nova_versao_num)

    db.add(novo_dfd)
    await db.commit()
    await db.refresh(novo_dfd)

    return {
        "message": "Nova versao criada com sucesso",
        "versao_anterior": dfd.versao,
        "versao_atual": novo_dfd.versao,
        "id": novo_dfd.id
    }


# ========== EXPORTACAO ==========

@router.get("/{dfd_id}/pdf", response_class=HTMLResponse)
async def gerar_pdf_dfd(
    dfd_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(auth_get_current_user)
):
    """
    Gera uma versao HTML para impressao/PDF do DFD.

    Args:
        dfd_id: ID do DFD

    Returns:
        HTML formatado para impressao
    """
    result = await db.execute(
        select(DFD)
        .filter(DFD.id == dfd_id)
        .options(selectinload(DFD.projeto))
    )
    dfd = result.scalars().first()

    if not dfd:
        raise HTTPException(status_code=404, detail="DFD nao encontrado")

    projeto = dfd.projeto

    # Montar conteudo HTML
    campos_html = ""
    for campo_nome, campo_cfg in DFD_CAMPOS_CONFIG.items():
        valor = getattr(dfd, campo_nome, None)
        if valor:
            if isinstance(valor, (dict, list)):
                valor = json.dumps(valor, ensure_ascii=False, indent=2)
            campos_html += f"""
            <div class="campo">
                <h3>{campo_cfg.get('label', campo_nome)}</h3>
                <div class="valor">{valor}</div>
            </div>
            """

    html = f"""
    <!DOCTYPE html>
    <html lang="pt-BR">
    <head>
        <meta charset="UTF-8">
        <title>Documento de Formalizacao da Demanda - {projeto.titulo if projeto else 'Projeto'}</title>
        <style>
            body {{
                font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
                max-width: 800px;
                margin: 0 auto;
                padding: 40px;
                color: #333;
            }}
            h1 {{
                color: #2C7A7B;
                border-bottom: 2px solid #2C7A7B;
                padding-bottom: 10px;
            }}
            h2 {{
                color: #666;
                font-weight: normal;
                margin-top: 0;
            }}
            .meta {{
                background: #f7fafc;
                padding: 15px;
                border-radius: 8px;
                margin-bottom: 30px;
            }}
            .meta span {{
                display: inline-block;
                margin-right: 20px;
            }}
            .campo {{
                margin-bottom: 25px;
                page-break-inside: avoid;
            }}
            .campo h3 {{
                color: #2C7A7B;
                margin-bottom: 10px;
                font-size: 1.1em;
            }}
            .campo .valor {{
                background: #f9f9f9;
                padding: 15px;
                border-left: 3px solid #2C7A7B;
                white-space: pre-wrap;
            }}
            @media print {{
                body {{ padding: 20px; }}
                .no-print {{ display: none; }}
            }}
        </style>
    </head>
    <body>
        <h1>Documento de Formalizacao da Demanda (DFD)</h1>
        <h2>{projeto.titulo if projeto else 'Projeto'}</h2>
        <div class="meta">
            <span><strong>Versao:</strong> {dfd.versao}</span>
            <span><strong>Status:</strong> {dfd.status}</span>
            <span><strong>Data:</strong> {dfd.data_atualizacao.strftime('%d/%m/%Y %H:%M') if dfd.data_atualizacao else ''}</span>
        </div>
        {campos_html}
        <div class="no-print" style="margin-top: 40px; text-align: center;">
            <button onclick="window.print()" style="padding: 10px 20px; background: #2C7A7B; color: white; border: none; border-radius: 5px; cursor: pointer;">
                Imprimir / Salvar como PDF
            </button>
        </div>
    </body>
    </html>
    """

    return HTMLResponse(content=html)
