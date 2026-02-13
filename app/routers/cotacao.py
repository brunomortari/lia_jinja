"""
Sistema LIA - Router de Cotacao/Pesquisa de Precos
===================================================
Endpoints para geracao e gerenciamento de pesquisas de precos.

Autor: Equipe TRE-GO
Data: Janeiro 2026
"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from typing import Dict, Any, List, Optional
from datetime import datetime, timezone
import logging

from app.database import get_db
from app.models.projeto import Projeto
from app.models.user import User
from app.auth import current_active_user as auth_get_current_user
from app.models.artefatos import PesquisaPrecos
from app.schemas.compras import TipoCatalogo
from app.services.compras_service import (
    compras_service,
    detectar_outliers_iqr,
    calcular_estatisticas
)
from app.schemas.ia_schemas import (
    GerarCotacaoRequest,
    SalvarPesquisaPrecosRequest,
)

logger = logging.getLogger(__name__)

router = APIRouter()


# ========== FUNCOES AUXILIARES ==========

async def gerar_cotacao_local(
    projeto: Optional[Projeto],
    db: AsyncSession,
    itens: Optional[List[str]] = None,
    artefato_base_id: Optional[int] = None,
    palavras_chave: Optional[str] = None,
    codigo_catmat: Optional[int] = None,
    tipo_catalogo: Optional[str] = None,
    pesquisar_familia_pdm: Optional[bool] = False,
    estado: Optional[str] = None,
    incluir_detalhes_pncp: Optional[bool] = False
) -> Dict[str, Any]:
    """
    Executa a pesquisa de precos localmente usando o servico de compras.

    Args:
        projeto: Projeto relacionado (opcional)
        db: Sessao do banco de dados
        itens: Lista de itens para pesquisa
        artefato_base_id: ID do artefato base
        palavras_chave: Palavras-chave para busca
        codigo_catmat: Codigo CATMAT/CATSERV obrigatorio
        tipo_catalogo: 'material' ou 'servico'
        pesquisar_familia_pdm: Se deve pesquisar familia PDM
        estado: Estado para filtro
        incluir_detalhes_pncp: Se deve enriquecer com PNCP

    Returns:
        Dicionario com dados da cotacao

    Raises:
        HTTPException: Se codigo CATMAT nao informado ou nenhum preco encontrado
    """
    if not codigo_catmat:
        raise HTTPException(
            status_code=400,
            detail="Codigo CATMAT/CATSERV e obrigatorio para pesquisa de precos."
        )

    try:
        # 1. Definir tipo de catalogo
        tipo_enum = (
            TipoCatalogo.SERVICO
            if tipo_catalogo and tipo_catalogo.lower() == 'servico'
            else TipoCatalogo.MATERIAL
        )

        # 2. Buscar informacoes do item (descricao)
        descricao_item = "Item nao identificado"
        if tipo_enum == TipoCatalogo.MATERIAL:
            item_info = await compras_service.consultar_item_material(codigo_catmat)
            if item_info:
                descricao_item = item_info.descricao_item

        # 3. Buscar Precos
        itens_resultado = []
        if tipo_enum == TipoCatalogo.MATERIAL:
            if pesquisar_familia_pdm:
                itens_resultado, _, _, _ = await compras_service.consultar_precos_familia_pdm(
                    codigo_catmat=codigo_catmat,
                    estado=estado
                )
            else:
                itens_resultado, _ = await compras_service.consultar_todos_precos_material(
                    codigo_catmat=codigo_catmat,
                    estado=estado,
                    max_paginas=5
                )
        else:
            # Servico
            itens_resultado, _, _ = await compras_service.consultar_precos_servico(
                codigo_catserv=codigo_catmat,
                estado=estado
            )

        if not itens_resultado:
            raise HTTPException(
                status_code=404,
                detail="Nenhum preco encontrado para os parametros informados."
            )

        # 4. Detectar Outliers
        itens_resultado, q1, q3, iqr, lim_inf, lim_sup, qtd_outliers = detectar_outliers_iqr(
            itens_resultado
        )

        # 5. Enriquecer com PNCP se solicitado
        if incluir_detalhes_pncp:
            itens_resultado = await compras_service.enriquecer_itens_com_pncp(itens_resultado)

        # 6. Calcular Estatisticas
        stats = calcular_estatisticas(itens_resultado, incluir_outliers=True)

        # 7. Montar JSON de resposta
        resultado = {
            "versao_api": "2.0",
            "data_geracao": datetime.now(timezone.utc).isoformat(),
            "item": {
                "codigo_catmat": codigo_catmat,
                "tipo_catalogo": tipo_enum.value,
                "descricao": descricao_item,
                "unidade_medida": itens_resultado[0].unidade_medida if itens_resultado else ""
            },
            "cotacao": {
                "objeto": projeto.titulo if projeto else "",
                "justificativa": "",
                "responsavel": "",
            },
            "estatisticas": stats.dict(),
            "itens": [item.dict() for item in itens_resultado],
            "fonte": {
                "api": "Compras.gov.br - Dados Abertos",
                "url": "https://dadosabertos.compras.gov.br"
            }
        }
        return resultado

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Erro na cotacao local: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Erro ao processar cotacao: {str(e)}"
        )


# ========== ENDPOINTS ==========

@router.post("/gerar")
async def gerar_cotacao_automatica(
    request: GerarCotacaoRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(auth_get_current_user)
):
    """
    Executa a pesquisa de precos automatica.

    Busca precos no portal Compras.gov.br baseado no codigo CATMAT/CATSERV.

    Args:
        request: Parametros da pesquisa

    Returns:
        Dados da cotacao com estatisticas e itens encontrados
    """
    result = await db.execute(
        select(Projeto).filter(Projeto.id == request.projeto_id)
    )
    projeto = result.scalars().first()

    if not projeto:
        raise HTTPException(status_code=404, detail="Projeto nao encontrado")

    resultado = await gerar_cotacao_local(
        projeto=projeto,
        db=db,
        itens=request.itens,
        artefato_base_id=request.artefato_base_id,
        palavras_chave=request.palavras_chave,
        codigo_catmat=request.codigo_catmat,
        tipo_catalogo=request.tipo_catalogo,
        pesquisar_familia_pdm=request.pesquisar_familia_pdm,
        estado=request.estado,
        incluir_detalhes_pncp=request.incluir_detalhes_pncp
    )
    return resultado


@router.post("/salvar")
async def salvar_pesquisa_precos_versionada(
    request: SalvarPesquisaPrecosRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(auth_get_current_user)
):
    """
    Salva a Pesquisa de Precos como um artefato versionado.

    Args:
        request: Dados da cotacao para salvar

    Returns:
        Confirmacao com ID e versao do artefato criado
    """
    projeto_id = request.projeto_id
    cotacao_data = request.cotacao_data

    # Verificar projeto
    result = await db.execute(
        select(Projeto).filter(Projeto.id == projeto_id)
    )
    projeto = result.scalars().first()

    if not projeto:
        raise HTTPException(status_code=404, detail="Projeto nao encontrado")

    # Contar versoes existentes
    result = await db.execute(
        select(func.count()).filter(PesquisaPrecos.projeto_id == projeto_id)
    )
    versoes_existentes = result.scalar() or 0

    # Extrair conteudo
    content = cotacao_data.get('content_blocks', cotacao_data)
    audit = cotacao_data.get('audit_metadata', {})
    doc_header = cotacao_data.get('document_header', {})

    itens_lista = cotacao_data.get('itens', [])

    item_info = cotacao_data.get('item', {})
    estatisticas = cotacao_data.get('estatisticas', {})

    descricao_item = item_info.get('descricao') or "Item sem descricao"
    preco_medio = estatisticas.get('preco_medio')
    qtd_encontrada = estatisticas.get('quantidade_itens')

    valor_final = request.valor_total or preco_medio

    # Preparar artefatos_base
    artefatos_base = None
    if request.artefato_base_id:
        artefatos_base = {"dfd_ids": [request.artefato_base_id]}

    # Criar PesquisaPrecos (artefato versionado)
    pp = PesquisaPrecos(
        projeto_id=projeto_id,
        versao=versoes_existentes + 1,
        status="rascunho",
        gerado_por_ia=True,
        content_blocks=content,
        dados_cotacao=cotacao_data,
        valor_total_cotacao=valor_final,
        itens_cotados=itens_lista,
        item_descricao=descricao_item,
        preco_medio=preco_medio,
        quantidade_itens_encontrados=qtd_encontrada,
        document_header=doc_header,
        audit_metadata=audit,
        artefatos_base=artefatos_base,
    )
    db.add(pp)
    await db.commit()
    await db.refresh(pp)

    # Atualizar status do projeto
    projeto.status = "em_andamento"
    projeto.data_atualizacao = datetime.now(timezone.utc)
    await db.commit()

    logger.info(
        f"Cotacao salva: {len(itens_lista)} registros para projeto {projeto_id}"
    )

    return {
        "message": "Pesquisa de Precos salva com sucesso",
        "id": pp.id,
        "pesquisa_id": pp.id,
        "versao": pp.versao
    }
