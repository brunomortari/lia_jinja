"""
Rotas da API para consulta de preços CATMAT/CATSERV
Versão 2.0 - Com detecção de outliers e integração PNCP
"""
from fastapi import APIRouter, Query, HTTPException
from typing import Optional
from datetime import datetime
import logging

from app.schemas.compras import (
    RespostaPrecos, TipoCatalogo, ParametrosPesquisa, DetalhesContratacao
)
from app.services.compras_service import (
    compras_service, calcular_estatisticas, detectar_outliers_iqr
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1", tags=["Preços CATMAT/CATSERV"])


@router.get(
    "/precos/{codigo_catmat}",
    response_model=RespostaPrecos,
    response_model_by_alias=True,
    summary="Consultar preços por código CATMAT ou CATSERV",
    description="""
    Consulta preços praticados nas compras públicas federais por código CATMAT (materiais) ou CATSERV (serviços).
    
    Retorna estatísticas incluindo média, mediana, coeficiente de variação (CV) e **análise de outliers**.
    
    **Novidades v2.0:**
    - Detecção automática de outliers (método IQR)
    - Estatísticas com e sem outliers
    - Campo `isOutlier` em cada item
    - Quartis Q1, Q3 e IQR
    
    **Parâmetros:**
    - `codigo_catmat`: Código do item no catálogo (CATMAT ou CATSERV)
    - `tipo`: Tipo de catálogo (material ou servico)
    - `pesquisar_familia_pdm`: Se True, pesquisa todos os itens da mesma família PDM
    - `estado`: Filtro por UF (opcional)
    - `incluir_detalhes_pncp`: Se True, enriquece cada item com detalhes do PNCP (marca, modelo, valores estimados, etc.)
    """,
    responses={
        200: {"description": "Consulta realizada com sucesso"},
        404: {"description": "Nenhum registro encontrado"},
        500: {"description": "Erro interno do servidor"}
    }
)
async def consultar_precos(
    codigo_catmat: int,
    tipo: TipoCatalogo = Query(
        TipoCatalogo.MATERIAL,
        description="Tipo de catálogo: material (CATMAT) ou servico (CATSERV)"
    ),
    pesquisar_familia_pdm: bool = Query(
        False,
        description="Pesquisar toda família PDM do item"
    ),
    estado: Optional[str] = Query(
        None,
        description="Filtro por estado (UF)",
        max_length=2,
        min_length=2
    ),
    incluir_detalhes_pncp: bool = Query(
        False,
        description="Enriquecer itens com detalhes do PNCP (marca, modelo, valores estimados, benefícios aplicados)"
    ),
    limit: int = Query(
        100,
        description="Limite máximo de registros retornados (padrão: 100)",
        ge=1,
        le=1000
    )
):
    """
    Endpoint principal para consulta de preços.
    Agora inclui detecção de outliers usando método IQR.
    """
    try:
        descricao_item = None
        codigo_pdm = None
        nome_pdm = None
        total_registros = 0
        total_paginas = 0
        
        # Buscar informações do item primeiro
        if tipo == TipoCatalogo.MATERIAL:
            item_info = await compras_service.consultar_item_material(codigo_catmat)
            if item_info:
                descricao_item = item_info.descricao_item
                codigo_pdm = item_info.codigo_pdm
                nome_pdm = item_info.nome_pdm
        
        # Realizar consulta de preços
        if tipo == TipoCatalogo.MATERIAL:
            if pesquisar_familia_pdm and codigo_pdm:
                # Pesquisa família PDM
                itens, total_registros, codigo_pdm, nome_pdm = await compras_service.consultar_precos_familia_pdm(
                    codigo_catmat=codigo_catmat,
                    estado=estado
                )
                total_paginas = 1  # Dados consolidados
            else:
                # Pesquisa normal - busca todas as páginas
                itens, total_registros = await compras_service.consultar_todos_precos_material(
                    codigo_catmat=codigo_catmat,
                    estado=estado
                )
                total_paginas = (total_registros // 500) + 1 if total_registros > 0 else 0
        else:
            # CATSERV
            itens, total_registros, total_paginas = await compras_service.consultar_precos_servico(
                codigo_catserv=codigo_catmat,
                estado=estado
            )
        
        # Se não encontrou registros
        if not itens:
            raise HTTPException(
                status_code=404,
                detail=f"Nenhum registro encontrado para o código {codigo_catmat}"
            )
        
        # Detectar outliers usando método IQR
        itens, q1, q3, iqr, limite_inf, limite_sup, qtd_outliers = detectar_outliers_iqr(itens)

        # Enriquecer com detalhes do PNCP se solicitado
        if incluir_detalhes_pncp:
            itens = await compras_service.enriquecer_itens_com_pncp(itens)

        # Calcular estatísticas (com todos os dados)
        estatisticas = calcular_estatisticas(itens, incluir_outliers=True)
        
        # Calcular estatísticas sem outliers
        estatisticas_sem_outliers = calcular_estatisticas(itens, incluir_outliers=False)
        
        # Montar resposta
        # Construir dicionário manualmente para garantir serialização e limitar tamanho
        itens_dict = []
        # Limita itens conforme parametro
        for item in itens[:limit]:
            d = item.dict() if hasattr(item, 'dict') else item.__dict__
            d['is_outlier'] = bool(getattr(item, "is_outlier", False))
            d['isOutlier'] = d['is_outlier'] # Compatibilidade
            itens_dict.append(d)

        return {
            "codigo_catmat": codigo_catmat,
            "tipo_catalogo": tipo,
            "descricao_item": descricao_item,
            "pesquisa_familia_pdm": pesquisar_familia_pdm,
            "codigo_pdm": codigo_pdm,
            "nome_pdm": nome_pdm,
            "estatisticas": estatisticas,
            "estatisticas_sem_outliers": estatisticas_sem_outliers,
            "itens": itens_dict,
            "total_registros": total_registros,
            "total_paginas": total_paginas,
            "data_consulta": datetime.now()
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Erro ao consultar preços: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Erro ao consultar preços: {str(e)}"
        )


@router.get(
    "/precos/{codigo_catmat}/estatisticas",
    summary="Obter apenas estatísticas de preços",
    description="Retorna apenas as estatísticas calculadas (média, mediana, CV, outliers) sem os itens individuais."
)
async def consultar_estatisticas(
    codigo_catmat: int,
    tipo: TipoCatalogo = Query(TipoCatalogo.MATERIAL),
    pesquisar_familia_pdm: bool = Query(False),
    estado: Optional[str] = Query(None, max_length=2, min_length=2)
):
    """
    Retorna apenas estatísticas, sem a lista completa de itens.
    """
    resposta = await consultar_precos(
        codigo_catmat=codigo_catmat,
        tipo=tipo,
        pesquisar_familia_pdm=pesquisar_familia_pdm,
        estado=estado,
        incluir_detalhes_pncp=False
    )
    
    return {
        "codigo_catmat": resposta.codigo_catmat,
        "tipo_catalogo": resposta.tipo_catalogo,
        "descricao_item": resposta.descricao_item,
        "pesquisa_familia_pdm": resposta.pesquisa_familia_pdm,
        "codigo_pdm": resposta.codigo_pdm,
        "nome_pdm": resposta.nome_pdm,
        "estatisticas": resposta.estatisticas,
        "estatisticas_sem_outliers": resposta.estatisticas_sem_outliers,
        "total_registros": resposta.total_registros,
        "data_consulta": resposta.data_consulta
    }


@router.get(
    "/item/{codigo_catmat}",
    summary="Consultar informações do item no catálogo",
    description="Retorna informações cadastrais do item (descrição, classe, PDM, etc.)"
)
async def consultar_item(codigo_catmat: int):
    """
    Consulta informações do item no catálogo CATMAT.
    """
    try:
        item = await compras_service.consultar_item_material(codigo_catmat)
        
        if not item:
            raise HTTPException(
                status_code=404,
                detail=f"Item {codigo_catmat} não encontrado no catálogo"
            )
        
        return item
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Erro ao consultar item: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Erro ao consultar item: {str(e)}"
        )


@router.get(
    "/pdm/{codigo_pdm}/itens",
    summary="Listar itens de uma família PDM",
    description="Retorna todos os itens pertencentes a uma família PDM específica."
)
async def listar_itens_pdm(
    codigo_pdm: int,
    pagina: int = Query(1, ge=1),
    tamanho_pagina: int = Query(100, ge=1, le=500)
):
    """
    Lista todos os itens de uma família PDM.
    """
    try:
        itens, total = await compras_service.consultar_itens_por_pdm(
            codigo_pdm=codigo_pdm,
            pagina=pagina,
            tamanho_pagina=tamanho_pagina
        )
        
        if not itens:
            raise HTTPException(
                status_code=404,
                detail=f"Nenhum item encontrado para o PDM {codigo_pdm}"
            )
        
        return {
            "codigo_pdm": codigo_pdm,
            "itens": itens,
            "total_itens": total,
            "pagina": pagina,
            "tamanho_pagina": tamanho_pagina
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Erro ao listar itens PDM: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Erro ao listar itens PDM: {str(e)}"
        )


# ============================================================
# Endpoint PNCP - Detalhes da Contratação
# ============================================================

@router.get(
    "/contratacao/{id_compra}",
    response_model=DetalhesContratacao,
    response_model_by_alias=True,
    summary="Consultar detalhes da contratação no PNCP",
    description="""
    Consulta detalhes completos de uma contratação no Portal Nacional de Contratações Públicas (PNCP).

    Utiliza o `idCompra` retornado na pesquisa de preços para buscar:
    - Dados gerais da contratação (modalidade, situação, órgão, objeto)
    - Itens da contratação (com valor estimado e quantidade)
    - Resultados/vencedores (com marca, modelo, fabricante)
    - URL construída do PNCP

    **Parâmetros:**
    - `codigo_item_catalogo`: Filtra itens e resultados por código CATMAT/CATSERV específico

    **Endpoints PNCP utilizados:**
    - 1.1_consultarContratacoes_PNCP_14133_Id
    - 2.1_consultarItensContratacoes_PNCP_14133_Id
    - 3.1_consultarResultadoItensContratacoes_PNCP_14133_Id
    """,
    responses={
        200: {"description": "Detalhes da contratação"},
        404: {"description": "Contratação não encontrada"},
        500: {"description": "Erro interno do servidor"}
    }
)
async def consultar_detalhes_contratacao(
    id_compra: str,
    codigo_item_catalogo: Optional[int] = Query(
        None,
        description="Filtrar itens por código CATMAT/CATSERV específico"
    )
):
    """
    Consulta detalhes completos de uma contratação no PNCP.
    """
    try:
        detalhes = await compras_service.consultar_detalhes_contratacao(
            id_compra,
            codigo_item_filtro=codigo_item_catalogo
        )
        
        if not detalhes.encontrado:
            raise HTTPException(
                status_code=404,
                detail=detalhes.mensagem or f"Contratação {id_compra} não encontrada"
            )
        
        return detalhes
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Erro ao consultar detalhes contratação: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Erro ao consultar detalhes da contratação: {str(e)}"
        )


@router.get(
    "/health",
    summary="Health check",
    description="Verifica se o serviço está funcionando"
)
async def health_check():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "service": "catmat-price-service",
        "version": "2.0.0"
    }
