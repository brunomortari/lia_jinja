"""
Sistema LIA - Views de Projetos e Artefatos (Lean Refactor)
=============================================================
Dashboard de projetos, visualização e edição de artefatos.
Refatorado para usar helpers compartilhados.

Autor: Equipe TRE-GO
Data: Janeiro 2026
"""

from fastapi import APIRouter, Request, Depends, Form, HTTPException
from fastapi.responses import HTMLResponse, RedirectResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc


from sqlalchemy.orm import selectinload
from typing import Optional
import json

from app.database import get_db
from app.models.user import User
from app.models.projeto import Projeto
from app.models.artefatos import (
    DFD, DFD_CAMPOS_CONFIG,
    ETP, Riscos, ItemRisco, TR, Edital,
    PesquisaPrecos, ChecklistConformidade,
    ARTEFATO_MAP
)
from app.routers.cotacao import gerar_cotacao_local
from app.auth import optional_current_active_user

from .common import (
    templates,
    ARTEFATO_CONFIG,
    DFD_CONFIG_DICT,
    verificar_dependencias,
    get_projeto_context,
    buscar_itens_pac,
    serialize_item_pac,
    logger
)


router = APIRouter()


# ========== LISTAGEM DE PROJETOS ==========

@router.get("/projetos", response_class=HTMLResponse)
async def projetos_page(
    request: Request,
    db: AsyncSession = Depends(get_db),
    usuario: User = Depends(optional_current_active_user)
):
    """Renderiza a página de listagem de projetos do usuário.

    Args:
        request (Request): A requisição HTTP.
        db (AsyncSession): Sessão do banco de dados.
        usuario (User): Usuário autenticado (opcional).

    Returns:
        HTMLResponse: A página 'projetos.html' renderizada ou redirect para login.
    """
    if not usuario:
        return RedirectResponse(url="/login", status_code=303)

    query = select(Projeto).filter(Projeto.usuario_id == usuario.id).order_by(Projeto.data_criacao.desc()).options(
        selectinload(Projeto.dfds),
        selectinload(Projeto.riscos),
        selectinload(Projeto.pesquisas_precos),
        selectinload(Projeto.etps),
        selectinload(Projeto.trs),
        selectinload(Projeto.editais),
        selectinload(Projeto.usuario)
    )
    result = await db.execute(query)
    projetos = result.scalars().all()

    return templates.TemplateResponse(
        "pages/projetos.html",
        {
            "request": request,
            "usuario": usuario,
            "page": "projetos",
            "page_title": "Projetos",
            "projetos": projetos
        }
    )


# ========== DASHBOARD DO PROJETO ==========

@router.get("/projetos/{projeto_id}", response_class=HTMLResponse)
async def projeto_dashboard(
    request: Request,
    projeto_id: int,
    db: AsyncSession = Depends(get_db),
    usuario: User = Depends(optional_current_active_user)
):
    """Renderiza o dashboard de um projeto específico."""
    if not usuario:
        return RedirectResponse(url="/login", status_code=303)

    projeto = await get_projeto_context(projeto_id, usuario.id, db, load_artefatos=True)

    if not projeto:
        return RedirectResponse(url="/projetos", status_code=303)

    # Normalizar status 'salvo' → 'rascunho' para exibição
    for dfd in projeto.dfds:
        if dfd.status and dfd.status.lower() == 'salvo':
            dfd.status = 'rascunho'

    # ── Motor de Fluxo (único ponto de cálculo) ──
    from app.services.fluxo_engine import calcular_fluxo, obter_cor_branch, TIPO_PARA_RELATION
    fluxo = calcular_fluxo(projeto)

    return templates.TemplateResponse(
        "pages/projeto_dashboard.html",
        {
            "request": request,
            "usuario": usuario,
            "page": "projetos",
            "page_title": f"Dashboard - {projeto.titulo}",
            "projeto": projeto,
            "artefatos_config": ARTEFATO_CONFIG,
            # Dados do motor de fluxo
            "fluxo": fluxo,
            "etapas": fluxo["etapas"],
            "active_branch": fluxo["active_branch"],
            "decision_resolved": fluxo["decision_resolved"],
            "flow_state": fluxo["flow_state"],
            "artefatos_status": fluxo["artefatos_status"],
            "projeto_sem_pac": fluxo["projeto_sem_pac"],
            "branch_info": obter_cor_branch(fluxo["active_branch"]),
            "tipo_para_relation": TIPO_PARA_RELATION,
        }
    )


# ========== PESQUISA DE ATAS (PLACEHOLDER) ==========

@router.get("/projetos/{projeto_id}/pesquisa-atas", response_class=HTMLResponse)
async def pesquisa_atas(
    request: Request,
    projeto_id: int,
    db: AsyncSession = Depends(get_db),
    usuario: User = Depends(optional_current_active_user)
):
    """Página placeholder para pesquisa profunda de atas.
    
    Futura funcionalidade:
    - Integração com PNCP
    - Busca inteligente de atas compatíveis
    - Comparação de preços e condições
    - Validação de requisitos legais
    - Geração de documentos de adesão
    """
    if not usuario:
        return RedirectResponse(url="/login", status_code=303)

    projeto = await get_projeto_context(projeto_id, usuario.id, db, load_artefatos=False)
    
    if not projeto:
        return RedirectResponse(url="/projetos", status_code=303)

    return templates.TemplateResponse(
        "pages/pesquisa_atas.html",
        {
            "request": request,
            "usuario": usuario,
            "page": "projetos",
            "page_title": f"Pesquisa de Atas - {projeto.titulo}",
            "projeto": projeto
        }
    )


# ========== DFD ==========

@router.get("/projetos/{projeto_id}/dfd/chat", response_class=HTMLResponse)
async def projeto_dfd_chat(
    request: Request,
    projeto_id: int,
    edit: int = None,  # ID do DFD para edição (opcional)
    db: AsyncSession = Depends(get_db),
    usuario: User = Depends(optional_current_active_user)
):
    """
    Página de DFD com chat conversacional com IA.
    
    Fluxo de 3 fases:
    - Fase 1 (Preparação): Novo DFD - coleta de informações via chat
    - Fase 2 (Geração): IA gera os campos do DFD
    - Fase 3 (Edição): DFD existente - edição e refinamento
    
    Args:
        edit: ID do DFD para editar (se informado, inicia na fase 3)
    """
    if not usuario:
        return RedirectResponse(url="/login", status_code=303)

    logger.info(f"Iniciando DFD Chat para projeto {projeto_id}, edit={edit}")
    try:
        projeto = await get_projeto_context(projeto_id, usuario.id, db, load_artefatos=True)
        if not projeto:
            logger.warning(f"Projeto {projeto_id} não encontrado para usuário {usuario.id}")
            return RedirectResponse(url="/projetos", status_code=303)
        logger.info("Projeto encontrado, buscando itens PAC...")

        # Buscar itens PAC
        itens_pac = await buscar_itens_pac(projeto, db)
        logger.info(f"Encontrados {len(itens_pac)} itens PAC.")
        
        # Processar quantidades e totais
        total_itens = 0
        valor_estimado_total = 0.0
        itens_pac_dto = []
        
        projeto_qtd_map = {}
        if projeto.itens_pac:
            projeto_itens_list = []
            if isinstance(projeto.itens_pac, str):
                try:
                    projeto_itens_list = json.loads(projeto.itens_pac)
                except json.JSONDecodeError:
                    logger.error("Erro ao decodificar JSON de itens_pac do projeto.")
                    pass
            elif isinstance(projeto.itens_pac, list):
                projeto_itens_list = projeto.itens_pac
                
            for pi in projeto_itens_list:
                if isinstance(pi, dict) and 'id' in pi and 'quantidade' in pi:
                    try:
                        projeto_qtd_map[int(pi['id'])] = float(pi['quantidade'])
                    except (ValueError, TypeError):
                        logger.warning(f"Item inválido no mapa de quantidade do projeto: {pi}")

        logger.info("Processando valores dos itens...")
        for i, item in enumerate(itens_pac):
            try:
                qtd = projeto_qtd_map.get(item.id, item.quantidade or 1)
                valor_unitario = item.valor_por_item or 0.0
                
                valor_item_projeto = (qtd or 0) * valor_unitario
                total_itens += (qtd or 0)
                valor_estimado_total += valor_item_projeto
                
                dto = serialize_item_pac(item)
                dto['qtd_projeto'] = qtd
                dto['valor_projeto'] = valor_item_projeto
                itens_pac_dto.append(dto)
            except Exception as e:
                logger.error(f"Erro ao processar item PAC #{i} (ID: {item.id}): {e}", exc_info=True)
                # Pular item com erro
                continue

        logger.info("Cálculo de valores concluído. Buscando versões de DFD.")
        # Calcular próxima versão
        result = await db.execute(select(DFD).filter(DFD.projeto_id == projeto_id))
        existing_dfds = result.scalars().all()
        proxima_versao = len(existing_dfds) + 1
        
        # Buscar DFDs anteriores para contexto
        dfds_anteriores = sorted(existing_dfds, key=lambda x: x.versao if x.versao else 0, reverse=True)
        logger.info(f"Próxima versão: {proxima_versao}, DFDs anteriores: {len(dfds_anteriores)}")

        # Modo de edição: buscar DFD existente para pré-popular
        dfd_para_editar = None
        fase_inicial = 'preparation'  # preparação por padrão (novo DFD)
        
        if edit:
            # Buscar DFD existente para edição
            result_edit = await db.execute(
                select(DFD).filter(DFD.id == edit, DFD.projeto_id == projeto_id)
            )
            dfd_para_editar = result_edit.scalars().first()
            if dfd_para_editar:
                fase_inicial = 'editing'  # DFD existente vai direto para fase 3 (edição)
                logger.info(f"Modo edição: DFD {edit} carregado, versão {dfd_para_editar.versao}")
            else:
                logger.warning(f"DFD {edit} não encontrado para edição")

        return templates.TemplateResponse(
            "pages/projeto_dfd_chat.html",
            {
                "request": request,
                "usuario": usuario,
                "page": "projetos",
                "page_title": f"DFD {'Editar' if dfd_para_editar else 'Chat'} - {projeto.titulo}",
                "projeto": projeto,
                "itens_pac": itens_pac_dto,
                "total_itens": total_itens,
                "valor_estimado_total": valor_estimado_total,
                "proxima_versao": proxima_versao,
                "dfds_anteriores": dfds_anteriores,
                # Novos campos para modo edição
                "dfd_editar": dfd_para_editar,
                "fase_inicial": fase_inicial,
            }
        )
    except Exception as e:
        logger.error(f"Erro fatal ao renderizar DFD Chat para projeto {projeto_id}: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Ocorreu um erro interno ao carregar a página de chat do DFD.")



@router.get("/projetos/{projeto_id}/dfd", response_class=HTMLResponse)
async def projeto_dfd_page(
    request: Request,
    projeto_id: int,
    usuario: User = Depends(optional_current_active_user)
):
    """Redireciona para a nova página de chat do DFD."""
    if not usuario:
        return RedirectResponse(url="/login", status_code=303)
    
    # Redireciona para a nova interface conversacional
    return RedirectResponse(url=f"/projetos/{projeto_id}/dfd/chat", status_code=303)


# ========== JE (JUSTIFICATIVA DE EXCEPCIONALIDADE) ==========

@router.get("/projetos/{projeto_id}/justificativa_excepcionalidade/chat", response_class=HTMLResponse)
async def projeto_je_chat(
    request: Request,
    projeto_id: int,
    db: AsyncSession = Depends(get_db),
    usuario: User = Depends(optional_current_active_user)
):
    """Página de JE com chat conversacional com IA."""
    if not usuario:
        return RedirectResponse(url="/login", status_code=303)
    
    result = await db.execute(
        select(Projeto).where(
            Projeto.id == projeto_id,
            Projeto.usuario_id == usuario.id
        )
    )
    projeto = result.scalars().first()
    
    if not projeto:
        raise HTTPException(status_code=404, detail="Projeto não encontrado")
    
    return templates.TemplateResponse(
        "pages/projeto_je_chat.html",
        {
            "request": request,
            "projeto": projeto,
            "usuario": usuario,
            "page": "projeto_je",
            "proxima_versao": 1
        }
    )


@router.get("/projetos/{projeto_id}/justificativa_excepcionalidade", response_class=HTMLResponse)
async def projeto_je_page(
    request: Request,
    projeto_id: int,
    usuario: User = Depends(optional_current_active_user)
):
    """Redireciona para chat da JE."""
    if not usuario:
        return RedirectResponse(url="/login", status_code=303)
    
    return RedirectResponse(url=f"/projetos/{projeto_id}/justificativa_excepcionalidade/chat", status_code=303)


# ========== CHK (CHECKLIST DE INSTRUÇÃO) ==========

@router.get("/projetos/{projeto_id}/checklist_conformidade/chat", response_class=HTMLResponse)
async def projeto_chk_chat(
    request: Request,
    projeto_id: int,
    db: AsyncSession = Depends(get_db),
    usuario: User = Depends(optional_current_active_user)
):
    """Página de CHK com chat conversacional com IA."""
    if not usuario:
        return RedirectResponse(url="/login", status_code=303)

    result = await db.execute(
        select(Projeto).where(
            Projeto.id == projeto_id,
            Projeto.usuario_id == usuario.id
        )
    )
    projeto = result.scalars().first()

    if not projeto:
        raise HTTPException(status_code=404, detail="Projeto não encontrado")

    # Verificar artefatos existentes para exibir no painel de contexto
    dfd_result = await db.execute(
        select(DFD).filter(DFD.projeto_id == projeto_id, DFD.status.in_(["aprovado", "publicado"])).limit(1)
    )
    etp_result = await db.execute(
        select(ETP).filter(ETP.projeto_id == projeto_id, ETP.status.in_(["aprovado", "publicado"])).limit(1)
    )
    tr_result = await db.execute(
        select(TR).filter(TR.projeto_id == projeto_id, TR.status.in_(["aprovado", "publicado"])).limit(1)
    )
    pgr_result = await db.execute(
        select(Riscos).filter(Riscos.projeto_id == projeto_id, Riscos.status.in_(["aprovado", "publicado"])).limit(1)
    )
    pp_result = await db.execute(
        select(PesquisaPrecos).filter(PesquisaPrecos.projeto_id == projeto_id, PesquisaPrecos.status.in_(["aprovado", "publicado"])).limit(1)
    )

    # Contar versões existentes
    chk_count_result = await db.execute(
        select(ChecklistConformidade).filter(ChecklistConformidade.projeto_id == projeto_id)
    )
    existing_chks = chk_count_result.scalars().all()
    proxima_versao = len(existing_chks) + 1

    return templates.TemplateResponse(
        "pages/projeto_chk_chat.html",
        {
            "request": request,
            "projeto": projeto,
            "usuario": usuario,
            "page": "projeto_chk",
            "proxima_versao": proxima_versao,
            "dfd_existe": dfd_result.scalars().first() is not None,
            "etp_existe": etp_result.scalars().first() is not None,
            "tr_existe": tr_result.scalars().first() is not None,
            "pgr_existe": pgr_result.scalars().first() is not None,
            "pp_existe": pp_result.scalars().first() is not None,
        }
    )


@router.get("/projetos/{projeto_id}/checklist_conformidade", response_class=HTMLResponse)
async def projeto_chk_page(
    request: Request,
    projeto_id: int,
    usuario: User = Depends(optional_current_active_user)
):
    """Redireciona para chat do CHK."""
    if not usuario:
        return RedirectResponse(url="/login", status_code=303)

    return RedirectResponse(url=f"/projetos/{projeto_id}/checklist_conformidade/chat", status_code=303)


# ========== PGR CHAT ==========

@router.get("/projetos/{projeto_id}/pgr/chat", response_class=HTMLResponse)
async def projeto_pgr_chat(
    request: Request,
    projeto_id: int,
    edit: int = None,  # ID do PGR para edicao (opcional)
    db: AsyncSession = Depends(get_db),
    usuario: User = Depends(optional_current_active_user)
):
    """
    Pagina de PGR com chat conversacional com IA.

    Fluxo de 3 fases:
    - Fase 1 (Preparacao): Novo PGR - coleta de informacoes via chat
    - Fase 2 (Geracao): IA gera a analise de riscos
    - Fase 3 (Edicao): PGR existente - edicao e refinamento

    Contexto: Usa DFD e Cotacoes APROVADOS como base para analise.

    Args:
        edit: ID do PGR para editar (se informado, inicia na fase 3)
    """
    if not usuario:
        return RedirectResponse(url="/login", status_code=303)

    logger.info(f"Iniciando PGR Chat para projeto {projeto_id}, edit={edit}")
    try:
        projeto = await get_projeto_context(projeto_id, usuario.id, db, load_artefatos=True)
        if not projeto:
            logger.warning(f"Projeto {projeto_id} nao encontrado para usuario {usuario.id}")
            return RedirectResponse(url="/projetos", status_code=303)
        logger.info("Projeto encontrado, buscando contextos...")

        # Buscar helpers do PGR
        from app.routers.views.projeto_pgr_helper import (
            buscar_dfds_aprovados,
            buscar_cotacoes_projeto,
            serializar_dfd_para_contexto,
            serializar_cotacao_para_contexto
        )

        # Buscar DFDs APROVADOS (apenas status aprovado)
        dfds_aprovados = await buscar_dfds_aprovados(projeto_id, db)
        logger.info(f"DFDs aprovados encontrados: {len(dfds_aprovados)}")

        # Buscar Cotacoes APROVADAS (apenas status aprovado)
        result_cotacoes = await db.execute(
            select(PesquisaPrecos)
            .filter(PesquisaPrecos.projeto_id == projeto_id, PesquisaPrecos.status.in_(["aprovado", "publicado"]))
            .order_by(PesquisaPrecos.data_criacao.desc())
        )
        cotacoes_aprovadas = result_cotacoes.scalars().all()
        logger.info(f"Cotacoes aprovadas encontradas: {len(cotacoes_aprovadas)}")

        # Serializar para o template
        dfd_context = serializar_dfd_para_contexto(dfds_aprovados[0]) if dfds_aprovados else None
        cotacoes_context = [serializar_cotacao_para_contexto(cot) for cot in cotacoes_aprovadas]

        # Buscar itens PAC
        itens_pac = await buscar_itens_pac(projeto, db)

        # Processar quantidades e totais
        total_itens = 0
        valor_estimado_total = 0.0
        itens_pac_dto = []

        projeto_qtd_map = {}
        if projeto.itens_pac:
            projeto_itens_list = []
            if isinstance(projeto.itens_pac, str):
                try:
                    projeto_itens_list = json.loads(projeto.itens_pac)
                except json.JSONDecodeError:
                    pass
            elif isinstance(projeto.itens_pac, list):
                projeto_itens_list = projeto.itens_pac

            for pi in projeto_itens_list:
                if isinstance(pi, dict) and 'id' in pi and 'quantidade' in pi:
                    try:
                        projeto_qtd_map[int(pi['id'])] = float(pi['quantidade'])
                    except (ValueError, TypeError):
                        pass

        for item in itens_pac:
            try:
                qtd = projeto_qtd_map.get(item.id, item.quantidade or 1)
                valor_unitario = item.valor_por_item or 0.0
                valor_item_projeto = (qtd or 0) * valor_unitario
                total_itens += (qtd or 0)
                valor_estimado_total += valor_item_projeto

                dto = serialize_item_pac(item)
                dto['qtd_projeto'] = qtd
                dto['valor_projeto'] = valor_item_projeto
                itens_pac_dto.append(dto)
            except Exception as e:
                logger.error(f"Erro ao processar item PAC (ID: {item.id}): {e}")
                continue

        # Calcular proxima versao
        result = await db.execute(select(Riscos).filter(Riscos.projeto_id == projeto_id))
        existing_pgrs = result.scalars().all()
        proxima_versao = len(existing_pgrs) + 1

        # Buscar PGRs anteriores para contexto
        pgrs_anteriores = sorted(existing_pgrs, key=lambda x: x.versao if x.versao else 0, reverse=True)
        logger.info(f"Proxima versao: {proxima_versao}, PGRs anteriores: {len(pgrs_anteriores)}")

        # Modo de edicao: buscar PGR existente para pre-popular
        pgr_para_editar = None
        pgr_itens_risco_json = []  # Serialized risk items for JS
        fase_inicial = 'preparation'  # preparacao por padrao (novo PGR)

        if edit:
            # Usar selectinload para carregar itens_risco junto
            result_edit = await db.execute(
                select(Riscos)
                .options(selectinload(Riscos.itens_risco))
                .filter(Riscos.id == edit, Riscos.projeto_id == projeto_id)
            )
            pgr_para_editar = result_edit.scalars().first()
            if pgr_para_editar:
                fase_inicial = 'editing'
                logger.info(f"Modo edicao: PGR {edit} carregado, versao {pgr_para_editar.versao}")
                # Serializar itens_risco para JSON (incluindo IDs)
                if pgr_para_editar.itens_risco:
                    for item in pgr_para_editar.itens_risco:
                        pgr_itens_risco_json.append({
                            "id": item.id,
                            "pgr_id": item.pgr_id,
                            "origem": item.origem,
                            "fase_licitacao": item.fase_licitacao,
                            "categoria": item.categoria,
                            "evento": item.evento,
                            "causa": item.causa,
                            "consequencia": item.consequencia,
                            "probabilidade": item.probabilidade,
                            "impacto": item.impacto,
                            "tipo_tratamento": item.tipo_tratamento,
                            "resposta_planejada": item.resposta_planejada,
                            "acoes_preventivas": item.acoes_preventivas,
                            "acoes_contingencia": item.acoes_contingencia,
                            "alocacao_responsavel": item.alocacao_responsavel,
                            "gatilho_identificacao": item.gatilho_identificacao,
                            "indicador_monitoramento": item.indicador_monitoramento,
                            "frequencia_monitoramento": item.frequencia_monitoramento,
                            "status_atual": item.status_atual,
                        })
                    logger.info(f"Serializados {len(pgr_itens_risco_json)} itens de risco para JS")
            else:
                logger.warning(f"PGR {edit} nao encontrado para edicao")

        return templates.TemplateResponse(
            "pages/projeto_pgr_chat.html",
            {
                "request": request,
                "usuario": usuario,
                "page": "projetos",
                "page_title": f"PGR {'Editar' if pgr_para_editar else 'Chat'} - {projeto.titulo}",
                "projeto": projeto,
                "itens_pac": itens_pac_dto,
                "total_itens": total_itens,
                "valor_estimado_total": valor_estimado_total,
                "proxima_versao": proxima_versao,
                "pgrs_anteriores": pgrs_anteriores,
                # Contextos de artefatos aprovados
                "dfd_context": dfd_context,
                "dfd_context_json": json.dumps(dfd_context, ensure_ascii=False) if dfd_context else "null",
                "cotacoes_context": cotacoes_context,
                "cotacoes_context_json": json.dumps(cotacoes_context, ensure_ascii=False),
                # Modo edicao
                "pgr_editar": pgr_para_editar,
                "pgr_itens_risco_json": json.dumps(pgr_itens_risco_json, ensure_ascii=False),
                "fase_inicial": fase_inicial,
            }
        )
    except Exception as e:
        logger.error(f"Erro fatal ao renderizar PGR Chat para projeto {projeto_id}: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Ocorreu um erro interno ao carregar a pagina de chat do PGR.")


# ========== ETP CHAT ==========

@router.get("/projetos/{projeto_id}/etp/chat", response_class=HTMLResponse)
async def projeto_etp_chat(
    request: Request,
    projeto_id: int,
    edit: int = None,  # ID do ETP para edicao (opcional)
    db: AsyncSession = Depends(get_db),
    usuario: User = Depends(optional_current_active_user)
):
    """
    Pagina de ETP com chat conversacional com IA.

    Fluxo de 3 fases:
    - Fase 1 (Preparacao): Novo ETP - coleta de informacoes via chat
    - Fase 2 (Geracao): IA gera os campos do ETP (15 campos obrigatorios)
    - Fase 3 (Edicao): ETP existente - edicao e refinamento

    Contexto: Usa DFD, Cotacoes e PGR APROVADOS como base.

    Args:
        edit: ID do ETP para editar (se informado, inicia na fase 3)
    """
    if not usuario:
        return RedirectResponse(url="/login", status_code=303)

    logger.info(f"Iniciando ETP Chat para projeto {projeto_id}, edit={edit}")
    try:
        projeto = await get_projeto_context(projeto_id, usuario.id, db, load_artefatos=True)
        if not projeto:
            logger.warning(f"Projeto {projeto_id} nao encontrado para usuario {usuario.id}")
            return RedirectResponse(url="/projetos", status_code=303)
        logger.info("Projeto encontrado, buscando contextos...")

        # Buscar DFD APROVADO (obrigatorio para ETP)
        dfd_result = await db.execute(
            select(DFD)
            .filter(DFD.projeto_id == projeto_id, DFD.status.in_(["aprovado", "publicado"]))
            .order_by(DFD.data_criacao.desc())
            .limit(1)
        )
        dfd_aprovado = dfd_result.scalars().first()
        logger.info(f"DFD aprovado encontrado: {dfd_aprovado is not None}")

        # Contexto do DFD para o template
        dfd_context = None
        if dfd_aprovado:
            dfd_context = {
                "id": dfd_aprovado.id,
                "descricao_objeto": dfd_aprovado.descricao_objeto,
                "justificativa": dfd_aprovado.justificativa,
                "alinhamento_estrategico": dfd_aprovado.alinhamento_estrategico,
                "grau_prioridade": dfd_aprovado.grau_prioridade,
                "versao": dfd_aprovado.versao,
            }

        # Buscar Cotacao APROVADA
        pp_result = await db.execute(
            select(PesquisaPrecos)
            .filter(PesquisaPrecos.projeto_id == projeto_id, PesquisaPrecos.status.in_(["aprovado", "publicado"]))
            .order_by(PesquisaPrecos.data_criacao.desc())
            .limit(1)
        )
        cotacao_aprovada = pp_result.scalars().first()
        logger.info(f"Cotacao aprovada encontrada: {cotacao_aprovada is not None}")

        # Contexto da cotacao para o template
        cotacao_context = None
        if cotacao_aprovada:
            cotacao_context = {
                "id": cotacao_aprovada.id,
                "valor_total_cotacao": cotacao_aprovada.valor_total_cotacao or 0,
                "quantidade_fornecedores": len(cotacao_aprovada.itens_cotados or []),
                "versao": cotacao_aprovada.versao,
            }

        # Buscar PGR APROVADO
        pgr_result = await db.execute(
            select(Riscos)
            .filter(Riscos.projeto_id == projeto_id, Riscos.status.in_(["aprovado", "publicado"]))
            .order_by(Riscos.data_criacao.desc())
            .limit(1)
        )
        pgr_aprovado = pgr_result.scalars().first()
        logger.info(f"PGR aprovado encontrado: {pgr_aprovado is not None}")

        # Contexto do PGR para o template
        pgr_context = None
        if pgr_aprovado:
            pgr_context = {
                "id": pgr_aprovado.id,
                "identificacao_objeto": pgr_aprovado.identificacao_objeto,
                "resumo_analise_planejamento": pgr_aprovado.resumo_analise_planejamento,
                "resumo_analise_selecao": pgr_aprovado.resumo_analise_selecao,
                "resumo_analise_gestao": pgr_aprovado.resumo_analise_gestao,
                "versao": pgr_aprovado.versao,
            }

        # Buscar itens PAC
        itens_pac = await buscar_itens_pac(projeto, db)

        # Processar quantidades e totais
        total_itens = 0
        valor_estimado_total = 0.0
        itens_pac_dto = []

        projeto_qtd_map = {}
        if projeto.itens_pac:
            projeto_itens_list = []
            if isinstance(projeto.itens_pac, str):
                try:
                    projeto_itens_list = json.loads(projeto.itens_pac)
                except json.JSONDecodeError:
                    pass
            elif isinstance(projeto.itens_pac, list):
                projeto_itens_list = projeto.itens_pac

            for pi in projeto_itens_list:
                if isinstance(pi, dict) and 'id' in pi and 'quantidade' in pi:
                    try:
                        projeto_qtd_map[int(pi['id'])] = float(pi['quantidade'])
                    except (ValueError, TypeError):
                        pass

        for item in itens_pac:
            try:
                qtd = projeto_qtd_map.get(item.id, item.quantidade or 1)
                valor_unitario = item.valor_por_item or 0.0
                valor_item_projeto = (qtd or 0) * valor_unitario
                total_itens += (qtd or 0)
                valor_estimado_total += valor_item_projeto

                dto = serialize_item_pac(item)
                dto['qtd_projeto'] = qtd
                dto['valor_projeto'] = valor_item_projeto
                itens_pac_dto.append(dto)
            except Exception as e:
                logger.error(f"Erro ao processar item PAC (ID: {item.id}): {e}")
                continue

        # Calcular proxima versao
        result = await db.execute(select(ETP).filter(ETP.projeto_id == projeto_id))
        existing_etps = result.scalars().all()
        proxima_versao = len(existing_etps) + 1

        # Buscar ETPs anteriores para contexto
        etps_anteriores = sorted(existing_etps, key=lambda x: x.versao if x.versao else 0, reverse=True)
        logger.info(f"Proxima versao: {proxima_versao}, ETPs anteriores: {len(etps_anteriores)}")

        # Modo de edicao: buscar ETP existente para pre-popular
        etp_para_editar = None
        fase_inicial = 'preparation'  # preparacao por padrao (novo ETP)

        if edit:
            result_edit = await db.execute(
                select(ETP).filter(ETP.id == edit, ETP.projeto_id == projeto_id)
            )
            etp_para_editar = result_edit.scalars().first()
            if etp_para_editar:
                fase_inicial = 'editing'
                logger.info(f"Modo edicao: ETP {edit} carregado, versao {etp_para_editar.versao}")
            else:
                logger.warning(f"ETP {edit} nao encontrado para edicao")

        return templates.TemplateResponse(
            "pages/projeto_etp_chat.html",
            {
                "request": request,
                "usuario": usuario,
                "page": "projetos",
                "page_title": f"ETP {'Editar' if etp_para_editar else 'Chat'} - {projeto.titulo}",
                "projeto": projeto,
                "itens_pac": itens_pac_dto,
                "total_itens": total_itens,
                "valor_estimado_total": valor_estimado_total,
                "proxima_versao": proxima_versao,
                "etps_anteriores": etps_anteriores,
                # Contextos de artefatos aprovados
                "dfd_context": dfd_context,
                "dfd_context_json": json.dumps(dfd_context, ensure_ascii=False) if dfd_context else "null",
                "cotacao_context": cotacao_context,
                "cotacao_context_json": json.dumps(cotacao_context, ensure_ascii=False) if cotacao_context else "null",
                "pgr_context": pgr_context,
                "pgr_context_json": json.dumps(pgr_context, ensure_ascii=False) if pgr_context else "null",
                # Modo edicao
                "etp_editar": etp_para_editar,
                "fase_inicial": fase_inicial,
            }
        )
    except Exception as e:
        logger.error(f"Erro fatal ao renderizar ETP Chat para projeto {projeto_id}: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Ocorreu um erro interno ao carregar a pagina de chat do ETP.")


# ========== TR CHAT ==========

@router.get("/projetos/{projeto_id}/tr/chat", response_class=HTMLResponse)
async def projeto_tr_chat(
    request: Request,
    projeto_id: int,
    edit: int = None,  # ID do TR para edicao (opcional)
    db: AsyncSession = Depends(get_db),
    usuario: User = Depends(optional_current_active_user)
):
    """
    Pagina de TR com chat conversacional com IA.

    Fluxo de 3 fases:
    - Fase 1 (Preparacao): Novo TR - coleta de informacoes via chat
    - Fase 2 (Geracao): IA gera os campos do TR (5 campos obrigatorios)
    - Fase 3 (Edicao): Edicao - ajustes e aprovacao

    Contextos aprovados necessarios: ETP (obrigatorio), DFD, Cotacao, PGR
    """
    if not usuario:
        return RedirectResponse(url="/login", status_code=303)

    try:
        projeto = await get_projeto_context(projeto_id, usuario.id, db, load_artefatos=True)
        if not projeto:
            return RedirectResponse(url="/projetos", status_code=303)

        # Buscar contextos de artefatos aprovados
        from app.routers.views.projeto_pgr_helper import (
            buscar_dfds_aprovados,
            buscar_cotacoes_projeto,
            buscar_pgr_aprovado,
            buscar_etp_aprovado,
            serializar_dfd_para_contexto,
            serializar_cotacao_para_contexto,
            serializar_pgr_para_contexto,
            serializar_etp_para_contexto
        )

        dfds_aprovados = await buscar_dfds_aprovados(projeto_id, db)
        cotacoes = await buscar_cotacoes_projeto(projeto_id, db)
        pgr_aprovado = await buscar_pgr_aprovado(projeto_id, db)
        etp_aprovado = await buscar_etp_aprovado(projeto_id, db)

        # Serializar contextos
        dfd_context = serializar_dfd_para_contexto(dfds_aprovados[0]) if dfds_aprovados else None
        cotacao_context = serializar_cotacao_para_contexto(cotacoes[0]) if cotacoes else None
        pgr_context = serializar_pgr_para_contexto(pgr_aprovado)
        etp_context = serializar_etp_para_contexto(etp_aprovado)

        # Buscar itens PAC e calcular totais
        itens_pac = await buscar_itens_pac(projeto, db)
        total_itens = 0
        valor_estimado_total = 0.0
        itens_pac_dto = []

        # Mapa de quantidades do projeto
        projeto_qtd_map = {}
        if projeto.itens_pac:
            projeto_itens_list = []
            if isinstance(projeto.itens_pac, str):
                try:
                    projeto_itens_list = json.loads(projeto.itens_pac)
                except:
                    pass
            elif isinstance(projeto.itens_pac, list):
                projeto_itens_list = projeto.itens_pac

            for pi in projeto_itens_list:
                if isinstance(pi, dict) and 'id' in pi and 'quantidade' in pi:
                    projeto_qtd_map[int(pi['id'])] = float(pi['quantidade'])

        for item in itens_pac:
            try:
                qtd = projeto_qtd_map.get(item.id, item.quantidade or 1)
                valor_unitario = item.valor_por_item or 0.0
                valor_item_projeto = (qtd or 0) * valor_unitario
                total_itens += (qtd or 0)
                valor_estimado_total += valor_item_projeto

                dto = serialize_item_pac(item)
                dto['qtd_projeto'] = qtd
                dto['valor_projeto'] = valor_item_projeto
                itens_pac_dto.append(dto)
            except Exception as e:
                logger.error(f"Erro ao processar item PAC (ID: {item.id}): {e}")
                continue

        # Calcular proxima versao
        result = await db.execute(select(TR).filter(TR.projeto_id == projeto_id))
        existing_trs = result.scalars().all()
        proxima_versao = len(existing_trs) + 1

        # Buscar TRs anteriores para contexto
        trs_anteriores = sorted(existing_trs, key=lambda x: x.versao if x.versao else 0, reverse=True)
        logger.info(f"Proxima versao TR: {proxima_versao}, TRs anteriores: {len(trs_anteriores)}")

        # Modo de edicao: buscar TR existente para pre-popular
        tr_para_editar = None
        fase_inicial = 'preparation'  # preparacao por padrao (novo TR)

        if edit:
            result_edit = await db.execute(
                select(TR).filter(TR.id == edit, TR.projeto_id == projeto_id)
            )
            tr_para_editar = result_edit.scalars().first()
            if tr_para_editar:
                fase_inicial = 'editing'
                logger.info(f"Modo edicao: TR {edit} carregado, versao {tr_para_editar.versao}")
            else:
                logger.warning(f"TR {edit} nao encontrado para edicao")

        return templates.TemplateResponse(
            "pages/projeto_tr_chat.html",
            {
                "request": request,
                "usuario": usuario,
                "page": "projetos",
                "page_title": f"TR {'Editar' if tr_para_editar else 'Chat'} - {projeto.titulo}",
                "projeto": projeto,
                "itens_pac": itens_pac_dto,
                "total_itens": total_itens,
                "valor_estimado_total": valor_estimado_total,
                "proxima_versao": proxima_versao,
                "trs_anteriores": trs_anteriores,
                # Contextos de artefatos aprovados
                "etp_context": etp_context,
                "etp_context_json": json.dumps(etp_context, ensure_ascii=False) if etp_context else "null",
                "dfd_context": dfd_context,
                "dfd_context_json": json.dumps(dfd_context, ensure_ascii=False) if dfd_context else "null",
                "cotacao_context": cotacao_context,
                "cotacao_context_json": json.dumps(cotacao_context, ensure_ascii=False) if cotacao_context else "null",
                "pgr_context": pgr_context,
                "pgr_context_json": json.dumps(pgr_context, ensure_ascii=False) if pgr_context else "null",
                # Modo edicao
                "tr_editar": tr_para_editar,
                "fase_inicial": fase_inicial,
            }
        )
    except Exception as e:
        logger.error(f"Erro fatal ao renderizar TR Chat para projeto {projeto_id}: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Ocorreu um erro interno ao carregar a pagina de chat do TR.")


@router.get("/projetos/{projeto_id}/dfd/novo/editar", response_class=HTMLResponse)
async def projeto_dfd_novo_editar(
    request: Request,
    projeto_id: int,
    usuario: User = Depends(optional_current_active_user)
):
    """Redireciona para a interface de chat do DFD."""
    if not usuario:
        return RedirectResponse(url="/login", status_code=303)
    return RedirectResponse(url=f"/projetos/{projeto_id}/dfd/chat", status_code=303)


@router.get("/projetos/{projeto_id}/pgr/novo/editar", response_class=HTMLResponse)
async def projeto_pgr_novo_editar(
    request: Request,
    projeto_id: int,
    usuario: User = Depends(optional_current_active_user)
):
    """Redireciona para a interface de chat do PGR."""
    if not usuario:
        return RedirectResponse(url="/login", status_code=303)
    return RedirectResponse(url=f"/projetos/{projeto_id}/pgr/chat", status_code=303)


@router.get("/projetos/{projeto_id}/pgr/novo/gerar", response_class=HTMLResponse)
async def projeto_pgr_novo_gerar(
    request: Request,
    projeto_id: int,
    usuario: User = Depends(optional_current_active_user)
):
    """Redireciona para a interface de chat do PGR."""
    if not usuario:
        return RedirectResponse(url="/login", status_code=303)
    return RedirectResponse(url=f"/projetos/{projeto_id}/pgr/chat", status_code=303)


@router.get("/projetos/{projeto_id}/etp/novo/editar", response_class=HTMLResponse)
async def projeto_etp_novo_editar(
    request: Request,
    projeto_id: int,
    usuario: User = Depends(optional_current_active_user)
):
    """Redireciona para a interface de chat da ETP."""
    if not usuario:
        return RedirectResponse(url="/login", status_code=303)
    return RedirectResponse(url=f"/projetos/{projeto_id}/etp/chat", status_code=303)


@router.get("/projetos/{projeto_id}/tr/novo/editar", response_class=HTMLResponse)
async def projeto_tr_novo_editar(
    request: Request,
    projeto_id: int,
    usuario: User = Depends(optional_current_active_user)
):
    """Redireciona para a interface de chat do TR."""
    if not usuario:
        return RedirectResponse(url="/login", status_code=303)
    return RedirectResponse(url=f"/projetos/{projeto_id}/tr/chat", status_code=303)


@router.get("/projetos/{projeto_id}/edital/novo/editar", response_class=HTMLResponse)
async def projeto_edital_novo_editar(
    request: Request,
    projeto_id: int,
    usuario: User = Depends(optional_current_active_user)
):
    """Redireciona para a interface de chat do Edital."""
    if not usuario:
        return RedirectResponse(url="/login", status_code=303)
    return RedirectResponse(url=f"/projetos/{projeto_id}/ed/chat", status_code=303)


@router.get("/projetos/{projeto_id}/ed/chat", response_class=HTMLResponse)
async def projeto_ed_chat(
    request: Request,
    projeto_id: int,
    edit: int = None,  # ID do Edital para edição (opcional)
    db: AsyncSession = Depends(get_db),
    usuario: User = Depends(optional_current_active_user)
):
    """
    Página de Edital com chat conversacional com IA.

    Fluxo de 3 fases:
    - Fase 1 (Preparação): Novo Edital - coleta de configurações via chat
    - Fase 2 (Geração): IA gera os campos do Edital
    - Fase 3 (Edição): Edital existente - edição e refinamento

    Contexto: Usa DFD, Cotações, PGR, ETP e TR APROVADOS como base.
    """
    if not usuario:
        return RedirectResponse(url="/login", status_code=303)

    logger.info(f"Iniciando Edital Chat para projeto {projeto_id}, edit={edit}")
    try:
        projeto = await get_projeto_context(projeto_id, usuario.id, db, load_artefatos=True)
        if not projeto:
            logger.warning(f"Projeto {projeto_id} não encontrado para usuário {usuario.id}")
            return RedirectResponse(url="/projetos", status_code=303)

        # Buscar itens PAC
        itens_pac = await buscar_itens_pac(projeto, db)

        # Processar quantidades e totais
        total_itens = 0
        valor_estimado_total = 0.0
        itens_pac_dto = []

        projeto_qtd_map = {}
        if projeto.itens_pac:
            projeto_itens_list = []
            if isinstance(projeto.itens_pac, str):
                try:
                    projeto_itens_list = json.loads(projeto.itens_pac)
                except json.JSONDecodeError:
                    pass
            elif isinstance(projeto.itens_pac, list):
                projeto_itens_list = projeto.itens_pac

            for pi in projeto_itens_list:
                if isinstance(pi, dict) and 'id' in pi and 'quantidade' in pi:
                    try:
                        projeto_qtd_map[int(pi['id'])] = float(pi['quantidade'])
                    except (ValueError, TypeError):
                        pass

        for item in itens_pac:
            try:
                qtd = projeto_qtd_map.get(item.id, item.quantidade or 1)
                valor_unitario = item.valor_por_item or 0.0
                valor_item_projeto = (qtd or 0) * valor_unitario
                total_itens += (qtd or 0)
                valor_estimado_total += valor_item_projeto

                dto = serialize_item_pac(item)
                dto['qtd_projeto'] = qtd
                dto['valor_projeto'] = valor_item_projeto
                itens_pac_dto.append(dto)
            except Exception as e:
                logger.error(f"Erro ao processar item PAC (ID: {item.id}): {e}")
                continue

        # Calcular próxima versão
        result = await db.execute(select(Edital).filter(Edital.projeto_id == projeto_id))
        existing_editais = result.scalars().all()
        proxima_versao = len(existing_editais) + 1

        # Buscar editais anteriores para contexto
        editais_anteriores = sorted(existing_editais, key=lambda x: x.versao if x.versao else 0, reverse=True)

        # Buscar documentos aprovados como contexto
        documentos_aprovados = []

        # DFD aprovado
        dfd_result = await db.execute(
            select(DFD).filter(DFD.projeto_id == projeto_id, DFD.status.in_(["aprovado", "publicado"]))
            .order_by(DFD.data_criacao.desc()).limit(1)
        )
        dfd_aprovado = dfd_result.scalars().first()
        if dfd_aprovado:
            documentos_aprovados.append("DFD")

        # Cotação aprovada
        cotacao_result = await db.execute(
            select(PesquisaPrecos).filter(PesquisaPrecos.projeto_id == projeto_id, PesquisaPrecos.status.in_(["aprovado", "publicado"]))
            .order_by(PesquisaPrecos.data_criacao.desc()).limit(1)
        )
        cotacao_aprovada = cotacao_result.scalars().first()
        if cotacao_aprovada:
            documentos_aprovados.append("Cotação")

        # PGR aprovado
        pgr_result = await db.execute(
            select(Riscos).filter(Riscos.projeto_id == projeto_id, Riscos.status.in_(["aprovado", "publicado"]))
            .order_by(Riscos.data_criacao.desc()).limit(1)
        )
        pgr_aprovado = pgr_result.scalars().first()
        if pgr_aprovado:
            documentos_aprovados.append("PGR")

        # ETP aprovado
        etp_result = await db.execute(
            select(ETP).filter(ETP.projeto_id == projeto_id, ETP.status.in_(["aprovado", "publicado"]))
            .order_by(ETP.data_criacao.desc()).limit(1)
        )
        etp_aprovado = etp_result.scalars().first()
        if etp_aprovado:
            documentos_aprovados.append("ETP")

        # TR aprovado
        tr_result = await db.execute(
            select(TR).filter(TR.projeto_id == projeto_id, TR.status.in_(["aprovado", "publicado"]))
            .order_by(TR.data_criacao.desc()).limit(1)
        )
        tr_aprovado = tr_result.scalars().first()
        if tr_aprovado:
            documentos_aprovados.append("TR")

        # Modo de edição: buscar Edital existente para pré-popular
        edital_para_editar = None
        fase_inicial = 'preparation'

        if edit:
            result_edit = await db.execute(
                select(Edital).filter(Edital.id == edit, Edital.projeto_id == projeto_id)
            )
            edital_para_editar = result_edit.scalars().first()
            if edital_para_editar:
                fase_inicial = 'editing'
                logger.info(f"Modo edição: Edital {edit} carregado, versão {edital_para_editar.versao}")

        return templates.TemplateResponse(
            "pages/projeto_ed_chat.html",
            {
                "request": request,
                "usuario": usuario,
                "page": "projetos",
                "page_title": f"Edital {'Editar' if edital_para_editar else 'Chat'} - {projeto.titulo}",
                "projeto": projeto,
                "itens_pac": itens_pac_dto,
                "total_itens": total_itens,
                "valor_estimado_total": valor_estimado_total,
                "proxima_versao": proxima_versao,
                "editais_anteriores": editais_anteriores,
                # Documentos aprovados
                "documentos_aprovados": documentos_aprovados,
                "dfd_aprovado": dfd_aprovado,
                "cotacao_aprovada": cotacao_aprovada,
                "pgr_aprovado": pgr_aprovado,
                "etp_aprovado": etp_aprovado,
                "tr_aprovado": tr_aprovado,
                # Modo edição
                "edital_editar": edital_para_editar,
                "fase_inicial": fase_inicial,
            }
        )
    except Exception as e:
        logger.error(f"Erro fatal ao renderizar Edital Chat para projeto {projeto_id}: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Ocorreu um erro interno ao carregar a página de chat do Edital.")


@router.get("/projetos/{projeto_id}/dfd/{dfd_id}/editar", response_class=HTMLResponse)
async def projeto_dfd_editar(
    request: Request,
    projeto_id: int,
    dfd_id: int,
    usuario: User = Depends(optional_current_active_user)
):
    """Redireciona para a interface de chat do DFD em modo edicao."""
    if not usuario:
        return RedirectResponse(url="/login", status_code=303)
    return RedirectResponse(
        url=f"/projetos/{projeto_id}/dfd/chat?edit={dfd_id}",
        status_code=303
    )


# ========== PGR (RISCOS) ==========

@router.get("/projetos/{projeto_id}/pgr", response_class=HTMLResponse)
async def projeto_pgr_page(
    request: Request,
    projeto_id: int,
    usuario: User = Depends(optional_current_active_user)
):
    """Redireciona para a interface de chat do PGR."""
    if not usuario:
        return RedirectResponse(url="/login", status_code=303)
    return RedirectResponse(url=f"/projetos/{projeto_id}/pgr/chat", status_code=303)


@router.get("/projetos/{projeto_id}/pgr/preparar", response_class=HTMLResponse)
async def projeto_pgr_preparar_page(
    request: Request,
    projeto_id: int,
    usuario: User = Depends(optional_current_active_user)
):
    """Redireciona para a interface de chat do PGR."""
    if not usuario:
        return RedirectResponse(url="/login", status_code=303)
    return RedirectResponse(url=f"/projetos/{projeto_id}/pgr/chat", status_code=303)


# ========== ETP ==========

@router.get("/projetos/{projeto_id}/etp", response_class=HTMLResponse)
async def projeto_etp_page(
    request: Request,
    projeto_id: int,
    usuario: User = Depends(optional_current_active_user)
):
    """Redireciona para a interface de chat da ETP."""
    if not usuario:
        return RedirectResponse(url="/login", status_code=303)
    return RedirectResponse(url=f"/projetos/{projeto_id}/etp/chat", status_code=303)


@router.get("/projetos/{projeto_id}/etp/preparar", response_class=HTMLResponse)
async def projeto_etp_preparar_page(
    request: Request,
    projeto_id: int,
    usuario: User = Depends(optional_current_active_user)
):
    """Redireciona para a interface de chat da ETP."""
    if not usuario:
        return RedirectResponse(url="/login", status_code=303)
    return RedirectResponse(url=f"/projetos/{projeto_id}/etp/chat", status_code=303)


# ========== TR - PREPARAR ==========

@router.get("/projetos/{projeto_id}/tr", response_class=HTMLResponse)
async def projeto_tr_page(
    request: Request,
    projeto_id: int,
    db: AsyncSession = Depends(get_db),
    usuario: User = Depends(optional_current_active_user)
):
    """Página de preparação do TR."""
    if not usuario:
        return RedirectResponse(url="/login", status_code=303)

    projeto = await get_projeto_context(projeto_id, usuario.id, db)
    if not projeto:
        return RedirectResponse(url="/projetos", status_code=303)

    # Helper consolidado
    itens_pac = await buscar_itens_pac(projeto, db)
    
    # Processar quantidades específicas do projeto e totais
    total_itens = 0
    valor_estimado_total = 0.0
    
    # Mapa de quantidades do projeto: {pac_id: quantidade}
    projeto_qtd_map = {}
    if projeto.itens_pac:
        projeto_itens_list = []
        if isinstance(projeto.itens_pac, str):
            try:
                projeto_itens_list = json.loads(projeto.itens_pac)
            except:
                pass
        elif isinstance(projeto.itens_pac, list):
            projeto_itens_list = projeto.itens_pac
            
        for pi in projeto_itens_list:
            if isinstance(pi, dict) and 'id' in pi and 'quantidade' in pi:
                projeto_qtd_map[int(pi['id'])] = float(pi['quantidade'])

    itens_pac_dto = []
    for item in itens_pac:
        # Determinar quantidade: Projeto > PAC > 1
        qtd = projeto_qtd_map.get(item.id, item.quantidade or 1)
        
        # Atribuir temporariamente ao objeto (para uso no template)
        item.qtd_projeto = qtd
        
        # Calcular valor total do item para este projeto
        valor_item_projeto = qtd * item.valor_por_item
        
        total_itens += qtd
        valor_estimado_total += valor_item_projeto
        
        # Serializar
        dto = serialize_item_pac(item)
        dto['qtd_projeto'] = qtd
        dto['valor_projeto'] = valor_item_projeto
        itens_pac_dto.append(dto)

    itens_pac_json = json.dumps(itens_pac_dto, ensure_ascii=False)

    # Calcular proxima versao - procura por um modelo TR se existir
    result = await db.execute(select(TR).filter(TR.projeto_id == projeto_id))
    existing_trs = result.scalars().all()
    proxima_versao = len(existing_trs) + 1

    return templates.TemplateResponse(
        "pages/projeto_tr_chat.html",
        {
            "request": request,
            "usuario": usuario,
            "page": "projetos",
            "page_title": f"TR Chat - {projeto.titulo}",
            "projeto": projeto,
            "itens_pac": itens_pac,
            "itens_pac_json": itens_pac_json,
            "total_itens": total_itens,
            "valor_estimado_total": valor_estimado_total,
            "tipo_artefato": "tr",
            "proxima_versao": proxima_versao
        }
    )


# ========== EDITAL ==========

@router.get("/projetos/{projeto_id}/edital", response_class=HTMLResponse)
async def projeto_edital_page(
    request: Request,
    projeto_id: int,
    usuario: User = Depends(optional_current_active_user)
):
    """Redireciona para a interface de chat do Edital."""
    if not usuario:
        return RedirectResponse(url="/login", status_code=303)
    return RedirectResponse(url=f"/projetos/{projeto_id}/ed/chat", status_code=303)


@router.get("/projetos/{projeto_id}/edital/preparar", response_class=HTMLResponse)
async def projeto_edital_preparar_legacy(
    request: Request,
    projeto_id: int,
    usuario: User = Depends(optional_current_active_user)
):
    """Redireciona para a interface de chat do Edital."""
    if not usuario:
        return RedirectResponse(url="/login", status_code=303)
    return RedirectResponse(url=f"/projetos/{projeto_id}/ed/chat", status_code=303)


# ========== EDIÇÃO DE ARTEFATOS ==========

@router.get("/projetos/{projeto_id}/pgr/{artefato_id}/editar", response_class=HTMLResponse)
async def projeto_pgr_editar(
    request: Request,
    projeto_id: int,
    artefato_id: int,
    usuario: User = Depends(optional_current_active_user)
):
    """Redireciona para a interface de chat do PGR em modo edicao."""
    if not usuario:
        return RedirectResponse(url="/login", status_code=303)
    return RedirectResponse(
        url=f"/projetos/{projeto_id}/pgr/chat?edit={artefato_id}",
        status_code=303
    )


@router.get("/projetos/{projeto_id}/etp/{artefato_id}/editar", response_class=HTMLResponse)
async def projeto_etp_editar(
    request: Request,
    projeto_id: int,
    artefato_id: int,
    usuario: User = Depends(optional_current_active_user)
):
    """Redireciona para a interface de chat da ETP em modo edicao."""
    if not usuario:
        return RedirectResponse(url="/login", status_code=303)
    return RedirectResponse(
        url=f"/projetos/{projeto_id}/etp/chat?edit={artefato_id}",
        status_code=303
    )


@router.get("/projetos/{projeto_id}/tr/{artefato_id}/editar", response_class=HTMLResponse)
async def projeto_tr_editar(
    request: Request,
    projeto_id: int,
    artefato_id: int,
    usuario: User = Depends(optional_current_active_user)
):
    """Redireciona para a interface de chat do TR em modo edicao."""
    if not usuario:
        return RedirectResponse(url="/login", status_code=303)
    return RedirectResponse(
        url=f"/projetos/{projeto_id}/tr/chat?edit={artefato_id}",
        status_code=303
    )


@router.get("/projetos/{projeto_id}/edital/{artefato_id}/editar", response_class=HTMLResponse)
async def projeto_edital_editar(
    request: Request,
    projeto_id: int,
    artefato_id: int,
    usuario: User = Depends(optional_current_active_user)
):
    """Redireciona para a interface de chat do Edital em modo edicao."""
    if not usuario:
        return RedirectResponse(url="/login", status_code=303)
    return RedirectResponse(
        url=f"/projetos/{projeto_id}/ed/chat?edit={artefato_id}",
        status_code=303
    )


# ========== RISCOS (PGR) ==========

# ROTAS GENÉRICAS: Gerenciamento de riscos
@router.get("/projetos/{projeto_id}/riscos", response_class=HTMLResponse)
async def projeto_riscos_redirect(
    request: Request,
    projeto_id: int,
    db: AsyncSession = Depends(get_db),
    usuario: User = Depends(optional_current_active_user)
):
    """Redireciona para a nova rota de preparação de PGR."""
    if not usuario:
        return RedirectResponse(url="/login", status_code=303)
    
    projeto = await get_projeto_context(projeto_id, usuario.id, db)
    if not projeto:
        return RedirectResponse(url="/projetos", status_code=303)
    
    return RedirectResponse(url=f"/projetos/{projeto_id}/pgr", status_code=303)


@router.get("/projetos/{projeto_id}/riscos/{artefato_id}/editar", response_class=HTMLResponse)
async def projeto_riscos_editar(
    request: Request,
    projeto_id: int,
    artefato_id: int,
    db: AsyncSession = Depends(get_db),
    usuario: User = Depends(optional_current_active_user)
):
    """Redireciona para a nova rota de edição de PGR."""
    if not usuario:
        return RedirectResponse(url="/login", status_code=303)
    
    projeto = await get_projeto_context(projeto_id, usuario.id, db)
    if not projeto:
        return RedirectResponse(url="/projetos", status_code=303)
    
    return RedirectResponse(url=f"/projetos/{projeto_id}/pgr/{artefato_id}/editar", status_code=303)


@router.get("/projetos/{projeto_id}/pesquisa_precos", response_class=HTMLResponse)
async def projeto_pesquisa_precos_page(
    request: Request,
    projeto_id: int,
    db: AsyncSession = Depends(get_db),
    usuario: User = Depends(optional_current_active_user)
):
    """Página de pesquisa de preços do projeto."""
    if not usuario:
        return RedirectResponse(url="/login", status_code=303)

    projeto = await get_projeto_context(projeto_id, usuario.id, db)
    if not projeto:
        return RedirectResponse(url="/projetos", status_code=303)

    # Buscar Pesquisas Existentes
    result = await db.execute(select(PesquisaPrecos).filter(
        PesquisaPrecos.projeto_id == projeto_id
    ).order_by(PesquisaPrecos.data_criacao.desc()))
    pesquisas = result.scalars().all()

    # Contexto para IA (Levantamento de Soluções)
    # 1. DFDs
    res_dfds = await db.execute(select(DFD).filter(DFD.projeto_id == projeto_id).order_by(DFD.versao.desc()))
    dfds = res_dfds.scalars().all()
    
    # 2. Itens do PAC
    itens_pac = await buscar_itens_pac(projeto, db)
    # Serializar simples para contexto visual no modal
    itens_pac_simple = [{"id": i.id, "descricao": i.descricao, "quantidade": i.quantidade} for i in itens_pac]

    return templates.TemplateResponse(
        "pages/compras.html",
        {
            "request": request,
            "usuario": usuario,
            "page": "projetos",
            "page_title": f"Pesquisa de Preços - {projeto.titulo}",
            "projeto": projeto,
            "pesquisas": pesquisas,
            "proxima_versao": len(pesquisas) + 1,
            # Contexto IA
            "dfds": dfds,
            "itens_pac": itens_pac_simple,
            "itens_pac_json": json.dumps(itens_pac_simple, ensure_ascii=False)
        }
    )


@router.get("/projetos/{projeto_id}/pesquisa_precos/{pesquisa_id}/editar", response_class=HTMLResponse)
async def projeto_pesquisa_precos_editar(
    request: Request,
    projeto_id: int,
    pesquisa_id: int,
    db: AsyncSession = Depends(get_db),
    usuario: User = Depends(optional_current_active_user)
):
    """Página de edição da pesquisa de preços."""
    if not usuario:
        return RedirectResponse(url="/login", status_code=303)

    projeto = await get_projeto_context(projeto_id, usuario.id, db)
    if not projeto:
        return RedirectResponse(url="/projetos", status_code=303)

    result = await db.execute(select(PesquisaPrecos).filter(
        PesquisaPrecos.id == pesquisa_id,
        PesquisaPrecos.projeto_id == projeto_id
    ))
    pesquisa = result.scalars().first()

    if not pesquisa:
        return RedirectResponse(url=f"/projetos/{projeto_id}", status_code=303)

    dados_cotacao = pesquisa.dados_cotacao or {}
    item_info = dados_cotacao.get('item', {})
    estatisticas = dados_cotacao.get('estatisticas', {})
    doc_header = dados_cotacao.get('document_header', pesquisa.document_header or {})
    itens_cotados = pesquisa.itens_cotados or dados_cotacao.get('itens', [])

    return templates.TemplateResponse(
        "pages/projeto_pesquisa_precos_editar.html",
        {
            "request": request,
            "usuario": usuario,
            "page": "projetos",
            "page_title": f"Editar PP v{pesquisa.versao} - {projeto.titulo}",
            "projeto": projeto,
            "pesquisa": pesquisa,
            "item_info": item_info,
            "estatisticas": estatisticas,
            "doc_header": doc_header,
            "itens_cotados": itens_cotados
        }
    )


# ========== MÓDULO DE COTAÇÃO ==========

@router.get("/compras-app", response_class=HTMLResponse)
async def compras_app_page(
    request: Request,
    usuario: User = Depends(optional_current_active_user)
):
    """Serve a página da aplicação de cotação (antiga api_compras)."""
    return templates.TemplateResponse(
        "pages/compras.html",
        {"request": request, "usuario": usuario}
    )


@router.post("/projetos/{projeto_id}/cotacao/preview", response_class=HTMLResponse)
async def projeto_cotacao_preview(
    request: Request,
    projeto_id: int,
    db: AsyncSession = Depends(get_db),
    usuario: User = Depends(optional_current_active_user),
    dfd_base_id: Optional[int] = Form(None),
    palavras_chave: Optional[str] = Form(None),
    itens: Optional[str] = Form(None),
    codigo_catmat: Optional[int] = Form(None),
    tipo_catalogo: Optional[str] = Form(None),
    pesquisar_familia_pdm: bool = Form(False),
    estado: Optional[str] = Form(None),
    incluir_detalhes_pncp: bool = Form(False)
):
    """
    Gera a pesquisa de preços com a IA e exibe uma tela de preview/curadoria.
    """
    if not usuario:
        return RedirectResponse(url="/login", status_code=303)

    projeto = await get_projeto_context(projeto_id, usuario.id, db)
    if not projeto:
        return RedirectResponse(url="/projetos", status_code=303)

    itens_list = []
    if itens:
        try:
            itens_list = json.loads(itens)
        except json.JSONDecodeError:
            itens_list = [i.strip() for i in itens.split(',') if i.strip()]

    try:
        cotacao_data = await gerar_cotacao_local(
            projeto=projeto,
            db=db,
            itens=itens_list,
            dfd_base_id=dfd_base_id,
            palavras_chave=palavras_chave,
            codigo_catmat=codigo_catmat,
            tipo_catalogo=tipo_catalogo,
            pesquisar_familia_pdm=pesquisar_familia_pdm,
            estado=estado,
            incluir_detalhes_pncp=incluir_detalhes_pncp
        )
    except HTTPException as e:
        error_message = f"Erro ao gerar pesquisa de preços: {e.detail}"
        return RedirectResponse(url=f"/projetos/{projeto_id}/pesquisa_precos?error={error_message}", status_code=303)

    return templates.TemplateResponse(
        "pages/projeto_cotacao_preview.html",
        {
            "request": request,
            "usuario": usuario,
            "projeto": projeto,
            "page": "projetos",
            "page_title": f"Curadoria da Pesquisa de Preços - {projeto.titulo}",
            "cotacao_data": cotacao_data,
            "cotacao_data_json": json.dumps(cotacao_data, ensure_ascii=False)
        }
    )


# ========== ROTAS GENÉRICAS PARA ARTEFATOS ==========

@router.get("/projetos/{projeto_id}/{tipo_artefato}", response_class=HTMLResponse)
async def projeto_artefato_gerar(
    request: Request,
    projeto_id: int,
    tipo_artefato: str,
    db: AsyncSession = Depends(get_db),
    usuario: User = Depends(optional_current_active_user)
):
    """Página de geração de artefatos."""
    if not usuario:
        return RedirectResponse(url="/login", status_code=303)

    projeto = await get_projeto_context(projeto_id, usuario.id, db)
    if not projeto:
        return RedirectResponse(url="/projetos", status_code=303)

    # ROTA ESPECIFICA PARA RISCOS (PGR)
    if tipo_artefato == "riscos":
        # Carregar DFDs disponiveis para selecao de contexto
        result = await db.execute(select(DFD).filter(DFD.projeto_id == projeto_id).order_by(DFD.versao.desc()))
        dfds_disponiveis = result.scalars().all()
        
        # Carregar ETP para contexto (mais recente)
        result_etp = await db.execute(select(ETP).filter(ETP.projeto_id == projeto_id).order_by(ETP.versao.desc()))
        etp = result_etp.scalars().first()

        # Calcular proxima versao de Riscos
        result_versoes = await db.execute(select(Riscos).filter(Riscos.projeto_id == projeto_id))
        existing = result_versoes.scalars().all()
        proxima_versao = len(existing) + 1

        return templates.TemplateResponse(
            "pages/projeto_riscos_gerar.html",
            {
                "request": request,
                "usuario": usuario,
                "projeto": projeto,
                "page": "projetos",
                "page_title": f"Gerar Mapa de Riscos - {projeto.titulo}",
                "tipo_artefato": "riscos",
                "config": ARTEFATO_CONFIG["riscos"],
                "dfds_disponiveis": dfds_disponiveis,
                "etp": etp,
                "proxima_versao": proxima_versao
            }
        )

    if tipo_artefato == "cotacao" or tipo_artefato == "pesquisa_precos":
        return templates.TemplateResponse(
            "pages/compras.html",
            {
                "request": request,
                "usuario": usuario,
                "projeto": projeto,
                "page": "projetos",
                "page_title": f"Pesquisa de Preços - {projeto.titulo}"
            }
        )

    if tipo_artefato not in ARTEFATO_CONFIG:
        return RedirectResponse(url=f"/projetos/{projeto_id}", status_code=303)

    itens_pac = await buscar_itens_pac(projeto, db)

    dfds_disponiveis = []
    if tipo_artefato == "riscos":
        res = await db.execute(select(DFD).filter(DFD.projeto_id == projeto_id).order_by(DFD.versao.desc()))
        dfds = res.scalars().all()
        for dfd in dfds:
            dfds_disponiveis.append({
                "id": dfd.id,
                "versao": dfd.versao,
                "status": dfd.status or "rascunho",
                "data_criacao": dfd.data_criacao.strftime("%d/%m/%Y %H:%M") if dfd.data_criacao else "",
                "descricao": dfd.descricao_objeto[:100] + "..." if dfd.descricao_objeto and len(dfd.descricao_objeto) > 100 else (dfd.descricao_objeto or "")
            })

    # Usar helper para serializacao
    itens_pac_dto = [{"id": i.id, "descricao": i.descricao} for i in itens_pac]
    itens_pac_json = json.dumps(itens_pac_dto, ensure_ascii=False)

    return templates.TemplateResponse(
        "pages/projeto_artefato_gerar.html",
        {
            "request": request,
            "usuario": usuario,
            "page": "projetos",
            "page_title": f"{ARTEFATO_CONFIG[tipo_artefato]['titulo']} - {projeto.titulo}",
            "projeto": projeto,
            "tipo_artefato": tipo_artefato,
            "config": ARTEFATO_CONFIG[tipo_artefato],
            "itens_pac": itens_pac,
            "itens_pac_json": itens_pac_json,
            "dfds_disponiveis": dfds_disponiveis
        }
    )


@router.get("/projetos/{projeto_id}/{tipo_artefato}/{artefato_id}/editar", response_class=HTMLResponse)
async def projeto_artefato_id_editar(
    request: Request,
    projeto_id: int,
    tipo_artefato: str,
    artefato_id: int,
    db: AsyncSession = Depends(get_db),
    usuario: User = Depends(optional_current_active_user)
):
    """Página de edição de artefato específico por ID."""
    if tipo_artefato not in ARTEFATO_CONFIG:
        return RedirectResponse(url=f"/projetos/{projeto_id}", status_code=303)

    if not usuario:
        return RedirectResponse(url="/login", status_code=303)

    projeto = await get_projeto_context(projeto_id, usuario.id, db)
    if not projeto:
        return RedirectResponse(url="/projetos", status_code=303)

    Model = ARTEFATO_CONFIG[tipo_artefato]['model']
    result = await db.execute(select(Model).filter(Model.id == artefato_id, Model.projeto_id == projeto_id))
    artefato = result.scalars().first()
    if not artefato:
        return RedirectResponse(url=f"/projetos/{projeto_id}", status_code=303)

    # Proteção: Se publicado no SEI, redirecionar para visualização/publicação
    if artefato.protocolo_sei:
        return RedirectResponse(url=f"/projetos/{projeto_id}/{tipo_artefato}/{artefato_id}/publicar-sei", status_code=303)

    result = await db.execute(select(Model).filter(Model.projeto_id == projeto_id).order_by(Model.versao.desc()))
    todas_versoes = result.scalars().all()
    versoes = [
        {"id": v.id, "versao": v.versao, "data": v.data_criacao.strftime("%d/%m/%Y %H:%M") if v.data_criacao else "N/A"}
        for v in todas_versoes
    ]

    # Verificar se existe outra versão aprovada (para controle de UI)
    has_other_approved = any(
        v.status in ["aprovado", "publicado"] and v.id != artefato_id 
        for v in todas_versoes
    )
    has_any_approved = any(v.status in ["aprovado", "publicado"] for v in todas_versoes)
    
    # ROTA ESPECIFICA PARA RISCOS (PGR) - EDICAO
    if tipo_artefato == "riscos":
        # Carregar DFDs disponiveis
        result = await db.execute(select(DFD).filter(DFD.projeto_id == projeto_id).order_by(DFD.versao.desc()))
        dfds_disponiveis = result.scalars().all()
        
        # Carregar ETP para contexto
        result_etp = await db.execute(select(ETP).filter(ETP.projeto_id == projeto_id).order_by(ETP.versao.desc()))
        etp = result_etp.scalars().first()

        return templates.TemplateResponse(
            "pages/projeto_riscos_gerar.html",
            {
                "request": request,
                "usuario": usuario,
                "projeto": projeto,
                "artefato": artefato,  # Passar artefato para pre-enchimento
                "page": "projetos",
                "page_title": f"Editar Mapa de Riscos v{artefato.versao} - {projeto.titulo}",
                "tipo_artefato": "riscos",
                "config": ARTEFATO_CONFIG["riscos"],
                "dfds_disponiveis": dfds_disponiveis,
                "etp": etp,
                "proxima_versao": len(todas_versoes) + 1,
                "versoes": versoes
            }
        )

    return templates.TemplateResponse(
        "pages/projeto_artefato_editar.html",
        {
            "request": request,
            "usuario": usuario,
            "page": "projetos",
            "page_title": f"Editar {ARTEFATO_CONFIG[tipo_artefato]['sigla']} v{artefato.versao} - {projeto.titulo}",
            "projeto": projeto,
            "artefato": artefato,
            "tipo_artefato": tipo_artefato,
            "config": ARTEFATO_CONFIG[tipo_artefato],
            "campos_config": ARTEFATO_CONFIG[tipo_artefato]['config'],
            "campos_config_json": json.dumps(ARTEFATO_CONFIG[tipo_artefato]['config'], ensure_ascii=False),
            "versoes": versoes,
            "has_other_approved": has_other_approved,
            "has_any_approved": has_any_approved
        }
    )


# ========== PUBLICAR ARTEFATO NO SEI ==========

@router.get("/projetos/{projeto_id}/{tipo_artefato}/{artefato_id}/publicar-sei", response_class=HTMLResponse)
async def publicar_artefato_sei_page(
    request: Request,
    projeto_id: int,
    tipo_artefato: str,
    artefato_id: int,
    db: AsyncSession = Depends(get_db),
    usuario: User = Depends(optional_current_active_user)
):
    """Página de verificação e publicação de artefato no SEI."""
    if not usuario:
        return RedirectResponse(url="/login", status_code=303)

    if tipo_artefato not in ARTEFATO_MAP:
        return RedirectResponse(url=f"/projetos/{projeto_id}", status_code=303)

    projeto = await get_projeto_context(projeto_id, usuario.id, db)
    if not projeto:
        return RedirectResponse(url="/projetos", status_code=303)

    # Buscar artefato
    Model = ARTEFATO_MAP[tipo_artefato]['model']
    result = await db.execute(select(Model).filter(Model.id == artefato_id, Model.projeto_id == projeto_id))
    artefato = result.scalars().first()

    if not artefato:
        return RedirectResponse(url=f"/projetos/{projeto_id}", status_code=303)

    # Se já publicado, setar flag para template
    success_message = None
    if artefato.protocolo_sei:
         success_message = f"Artefato publicado com sucesso sob protocolo {artefato.protocolo_sei.get('numero')}"
    
    # REGRA: Apenas artefatos APROVADOS ou JÁ PUBLICADOS podem acessar essa página
    if artefato.status not in ['aprovado', 'publicado', 'concluido']:
         # Redirecionar com erro (idealmente passaria msg na query ou flash)
         # Por enquanto, fallback para o dashboard (ou pagina de erro se tivesse)
         return RedirectResponse(url=f"/projetos/{projeto_id}?error=apenas_aprovados", status_code=303)

    return templates.TemplateResponse(
        "pages/projeto_artefato_publicar_sei.html",
        {
            "request": request,
            "usuario": usuario,
            "page": "projetos",
            "page_title": f"Publicar {ARTEFATO_MAP[tipo_artefato]['sigla']} no SEI",
            "projeto": projeto,
            "artefato": artefato,
            "tipo_artefato": tipo_artefato,
            "config": ARTEFATO_MAP[tipo_artefato],
            "campos_config": ARTEFATO_MAP[tipo_artefato]['config'],
            "success_message": success_message,
            "sei_data": artefato.protocolo_sei
        }
    )

@router.post("/projetos/{projeto_id}/{tipo_artefato}/{artefato_id}/publicar-sei", response_class=HTMLResponse)
async def publicar_artefato_sei_post(
    request: Request,
    projeto_id: int,
    tipo_artefato: str,
    artefato_id: int,
    assunto: str = Form(...),
    db: AsyncSession = Depends(get_db),
    usuario: User = Depends(optional_current_active_user)
):
    """Processa a publicação no SEI."""
    if not usuario:
        return RedirectResponse(url="/login", status_code=303)

    projeto = await get_projeto_context(projeto_id, usuario.id, db)
    if not projeto:
        return RedirectResponse(url="/projetos", status_code=303)

    Model = ARTEFATO_MAP[tipo_artefato]['model']
    result = await db.execute(select(Model).filter(Model.id == artefato_id, Model.projeto_id == projeto_id))
    artefato = result.scalars().first()

    if not artefato:
        return RedirectResponse(url=f"/projetos/{projeto_id}", status_code=303)
    
    # REGRA: Apenas artefatos APROVADOS ou CONCLUIDOS podem ser publicados
    if artefato.status not in ['aprovado', 'concluido'] and not artefato.protocolo_sei:
        return RedirectResponse(url=f"/projetos/{projeto_id}?error=apenas_aprovados", status_code=303)

    if artefato.protocolo_sei:
         return RedirectResponse(url=f"/projetos/{projeto_id}/{tipo_artefato}/{artefato_id}/publicar-sei", status_code=303)

    # Publicar no SEI usando método do base (gerar mock protocolo)
    import random
    protocolo_number = f"000{random.randint(1000, 9999)}-{random.randint(10, 99)}.2026.6.09.0000"
    link_sei = f"https://sei.tre-go.gov.br/sei/modulos/pesquisa/md_pesq_documento_consulta_externa.php?{protocolo_number}"
    artefato.publicar_sei(
        numero_protocolo=protocolo_number,
        assunto=assunto,
        link=link_sei
    )
    await db.commit()

    return templates.TemplateResponse(
        "pages/projeto_artefato_publicar_sei.html",
        {
            "request": request,
            "usuario": usuario,
            "page": "projetos",
            "page_title": f"Publicado - {ARTEFATO_MAP[tipo_artefato]['sigla']}",
            "projeto": projeto,
            "artefato": artefato,
            "tipo_artefato": tipo_artefato,
            "config": ARTEFATO_MAP[tipo_artefato],
            "campos_config": ARTEFATO_MAP[tipo_artefato]['config'],
            "success_message": f"Artefato publicado com sucesso!",
            "sei_data": artefato.protocolo_sei
        }
    )


# ========== MOCK SEI ==========

@router.get("/projetos/{projeto_id}/sei/criar", response_class=HTMLResponse)
async def projeto_sei_criar_page(
    request: Request,
    projeto_id: int,
    db: AsyncSession = Depends(get_db),
    usuario: User = Depends(optional_current_active_user)
):
    """Página para criação de processo SEI (Mock)."""
    if not usuario:
        return RedirectResponse(url="/login", status_code=303)

    projeto = await get_projeto_context(projeto_id, usuario.id, db)
    if not projeto:
        return RedirectResponse(url="/projetos", status_code=303)

    return templates.TemplateResponse(
        "pages/projeto_sei_criar.html",
        {
            "request": request,
            "usuario": usuario,
            "page": "projetos",
            "page_title": f"Criar Processo SEI - {projeto.titulo}",
            "projeto": projeto
        }
    )


@router.post("/projetos/{projeto_id}/sei/criar", response_class=HTMLResponse)
async def projeto_sei_criar_post(
    request: Request,
    projeto_id: int,
    assunto: str = Form(...),
    tema: str = Form(...),
    data_autuacao: str = Form(...),
    db: AsyncSession = Depends(get_db),
    usuario: User = Depends(optional_current_active_user)
):
    """Processa a criação do processo SEI (Mock)."""
    if not usuario:
        return RedirectResponse(url="/login", status_code=303)

    projeto = await get_projeto_context(projeto_id, usuario.id, db)
    if not projeto:
        return RedirectResponse(url="/projetos", status_code=303)

    # Mock do protocolo SEI
    import random
    protocolo_sei = f"000{random.randint(1000, 9999)}-{random.randint(10, 99)}.2026.6.09.0000"
    
    # Atualiza o projeto
    sei_data = {
        "numero": protocolo_sei,
        "assunto": assunto,
        "tema": tema,
        "data_autuacao": data_autuacao,
        "status": "autuado",
        "link": f"https://sei.tre-go.jus.br/sei/controlador.php?acao=procedimento_trabalhar&id_procedimento={random.randint(1000000, 9999999)}"
    }
    
    projeto.protocolo_sei = sei_data
    await db.commit()

    return templates.TemplateResponse(
        "pages/projeto_sei_criar.html",
        {
            "request": request,
            "usuario": usuario,
            "page": "projetos",
            "page_title": f"Processo Criado - {projeto.titulo}",
            "projeto": projeto,
            "success_message": f"Processo SEI {protocolo_sei} criado com sucesso!",
            "sei_data": sei_data
        }
    )

