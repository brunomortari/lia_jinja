"""
Sistema LIA - Router de ETP com Adesão de Ata
==============================================
Endpoints para geração de ETP e gerenciamento de adesão a Atas de Registro.

Autor: Equipe TRE-GO
Data: Fevereiro 2026
"""

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from datetime import datetime
import json

from app.database import get_db
from app.models.projeto import Projeto
from app.models.artefatos import ETP, DFD
from app.models.user import User
from app.auth import current_active_user as auth_get_current_user
from app.schemas.ia_schemas import (
    AdesaoAtaRequest,
    AdesaoAtaResponse,
    SelecionarAtaRequest,
    SelecionarAtaResponse,
    AtaRegistro
)
from app.utils.datetime_utils import now_brasilia

router = APIRouter()


# ========== HELPERS ==========

async def _get_etp_or_create(projeto_id: int, db: AsyncSession) -> ETP:
    """Busca ou cria ETP rascunho do projeto."""
    result = await db.execute(
        select(ETP).filter(
            ETP.projeto_id == projeto_id,
            ETP.status == "rascunho"
        ).order_by(ETP.data_criacao.desc())
    )
    etp = result.scalars().first()
    
    if not etp:
        # Criar novo ETP rascunho
        etp = ETP(
            projeto_id=projeto_id,
            versao=1,
            status="rascunho",
            data_criacao=now_brasilia(),
            data_atualizacao=now_brasilia(),
            adesao_ata_habilitada=False,
            fase_adesao_ata="nao_iniciada"
        )
        db.add(etp)
        await db.commit()
        await db.refresh(etp)
    
    return etp


# ========== ENDPOINTS ==========

@router.post("/{projeto_id}/adesao-ata/habilitar")
async def habilitar_adesao_ata(
    projeto_id: int,
    request: dict,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(auth_get_current_user)
):
    """
    Habilita ou desabilita a opção de adesão a ata para o projeto.
    """
    etp = await _get_etp_or_create(projeto_id, db)
    
    habilitar = request.get("habilitar", False)
    etp.adesao_ata_habilitada = habilitar
    etp.fase_adesao_ata = "buscando_atas" if habilitar else "nao_iniciada"
    etp.data_atualizacao = now_brasilia()
    
    db.add(etp)
    await db.commit()
    await db.refresh(etp)
    
    return {
        "sucesso": True,
        "adesao_habilitada": etp.adesao_ata_habilitada,
        "fase": etp.fase_adesao_ata
    }


@router.get("/{projeto_id}/atas-disponiveis")
async def buscar_atas_disponiveis(
    projeto_id: int,
    descricao: str = Query(..., min_length=3),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(auth_get_current_user)
):
    """
    Busca atas disponíveis baseado na descrição do item.
    Atualmente retorna mock data. Será integrado com API Compras.gov depois.
    """
    
    # Verificar se projeto existe
    result = await db.execute(select(Projeto).filter(Projeto.id == projeto_id))
    projeto = result.scalars().first()
    if not projeto:
        raise HTTPException(status_code=404, detail="Projeto não encontrado")
    
    # MOCK DATA - Simular atas disponíveis
    atas_mock = [
        {
            "id": "ata_001",
            "numero": "000001-2025",
            "descricao": f"Ata de Registro - {descricao.capitalize()}",
            "categoria": "Serviços",
            "valor": 15000.00,
            "validade": "31/12/2025",
            "fornecedor": "Fornecedor A LTDA",
            "link_sei": "https://sei.example.com/000001-2025",
            "data_vigencia": "01/02/2025"
        },
        {
            "id": "ata_002",
            "numero": "000045-2024",
            "descricao": f"Ata de Registro - {descricao.capitalize()}",
            "categoria": "Materiais",
            "valor": 25000.00,
            "validade": "30/06/2025",
            "fornecedor": "Fornecedor B & C",
            "link_sei": "https://sei.example.com/000045-2024",
            "data_vigencia": "15/01/2025"
        },
        {
            "id": "ata_003",
            "numero": "000102-2024",
            "descricao": f"Ata de Registro - {descricao.capitalize()}",
            "categoria": "Serviços Técnicos",
            "valor": 35000.00,
            "validade": "28/02/2026",
            "fornecedor": "Consultoria XYZ",
            "link_sei": "https://sei.example.com/000102-2024",
            "data_vigencia": "10/02/2025"
        }
    ]
    
    return {
        "sucesso": True,
        "descricao_busca": descricao,
        "quantidade_encontrada": len(atas_mock),
        "atas": atas_mock
    }


@router.post("/{projeto_id}/selecionar-ata")
async def selecionar_ata(
    projeto_id: int,
    request: SelecionarAtaRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(auth_get_current_user)
):
    """
    Registra a seleção de uma ata no ETP.
    Armazena dados da ata e ativa deep_research automaticamente.
    """
    
    etp = await _get_etp_or_create(projeto_id, db)
    
    # Armazenar ata selecionada
    etp.ata_selecionada = request.ata_dados
    etp.fase_adesao_ata = "ata_selecionada"
    etp.data_atualizacao = now_brasilia()
    
    db.add(etp)
    await db.commit()
    await db.refresh(etp)
    
    return {
        "sucesso": True,
        "mensagem": "Ata selecionada com sucesso",
        "projeto_id": projeto_id,
        "ata_selecionada": request.ata_dados,
        "deep_research_ativado": True,
        "proxima_fase": "deep_research_ativo"
    }


@router.delete("/{projeto_id}/selecionar-ata")
async def desmarcar_ata(
    projeto_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(auth_get_current_user)
):
    """
    Remove a seleção de ata, voltando para fase de busca.
    """
    
    etp = await _get_etp_or_create(projeto_id, db)
    
    etp.ata_selecionada = None
    etp.fase_adesao_ata = "buscando_atas"
    etp.data_atualizacao = now_brasilia()
    
    db.add(etp)
    await db.commit()
    await db.refresh(etp)
    
    return {
        "sucesso": True,
        "mensagem": "Seleção de ata removida",
        "projeto_id": projeto_id,
        "fase": "buscando_atas"
    }


@router.get("/{projeto_id}/adesao-ata/status")
async def obter_status_adesao(
    projeto_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(auth_get_current_user)
):
    """
    Retorna status atual da adesão de ata para o projeto.
    """
    
    etp = await _get_etp_or_create(projeto_id, db)
    
    return {
        "projeto_id": projeto_id,
        "adesao_habilitada": etp.adesao_ata_habilitada,
        "fase": etp.fase_adesao_ata,
        "ata_selecionada": etp.ata_selecionada,
        "deep_research_ativado": etp.deep_research_ativado
    }
