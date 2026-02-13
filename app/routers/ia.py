"""
Sistema LIA - Router de Compatibilidade (LEGADO - n8n removido)
================================================================
⚠️ ⚠️ ⚠️ ATENÇÃO: ARQUIVO LEGADO - PROGRAMAÇÃO PARA REMOÇÃO ⚠️ ⚠️ ⚠️

Este arquivo é um WRAPPER de compatibilidade que redireciona para ia_native.py.
Todos os endpoints aqui são DEPRECATED e mantidos APENAS para compatibilidade
com o frontend existente.

CRONOGRAMA DE REMOÇÃO:
- Fase 1 (fevereiro 2026): Adicionar deprecation warnings a todos os endpoints
- Fase 2 (março 2026): Remover endpoints um por um conforme frontend migra
- Fase 3 (abril 2026): Deletar este arquivo completamente

**AÇÕES NECESSÁRIAS:**
1. ⚠️ Migrar frontend para usar /api/ia-native/* diretamente
2. ⚠️ Remover COMPLETAMENTE este arquivo após migração
3. ⚠️ Atualizar main.py para remover inclusão deste router
4. ⚠️ NÃO ADICIONE NOVOS ENDPOINTS AQUI! Use ia_native.py

Autor: Equipe TRE-GO
Data: Fevereiro 2026
Versão: Legado (Deprecação Iniciada)
"""

import warnings
import logging
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
import json

from app.database import get_db
from app.models.projeto import Projeto
from app.models.user import User
from app.auth import current_active_user as auth_get_current_user
from app.models.artefatos import (
    DFD,
    ETP,
    TR,
    Riscos,
    Edital,
    ARTEFATO_MAP,
    PesquisaPrecos
)
from app.schemas.ia_schemas import (
    GerarArtefatoPayload,
    SalvarArtefatoIARequest,
    RegenerarCampoRequest
)
from app.services.artefatos_service import mapear_campos_artefato
from app.utils.deprecation import log_deprecation
from app.utils.datetime_utils import parse_date

# Import from ia_native for delegation
from app.routers import ia_native

logger = logging.getLogger(__name__)

router = APIRouter()

# Alias for compatibility
_mapear_campos_artefato = mapear_campos_artefato


# ========== COMPATIBILITY ENDPOINTS ==========

@router.post("/{tipo_artefato}/gerar")
async def gerar_artefato(
    tipo_artefato: str,
    payload: GerarArtefatoPayload,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(auth_get_current_user),
    use_test: bool = False
):
    """
    [DEPRECATED] Wrapper for ia_native.gerar_artefato_json
    
    This endpoint is mantido para compatibilidade com frontend.
    Internamente, usa agentes Python nativos (ia_native.py).
    """
    log_deprecation(f"/api/ia/{tipo_artefato}/gerar", "/api/ia-native/{tipo_artefato}/gerar")
    
    # Redirect to ia_native
    projeto_id = payload.projeto.get('projeto_id')
    prompt_adicional = payload.prompt_adicional
    
    return await ia_native.gerar_artefato_json(
        tipo_artefato=tipo_artefato,
        projeto_id=projeto_id,
        prompt_adicional=prompt_adicional,
        db=db,
        current_user=current_user
    )


@router.post("/{tipo_artefato}/gerar-stream")
async def gerar_artefato_stream(
    tipo_artefato: str,
    payload: GerarArtefatoPayload,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(auth_get_current_user),
    use_test: bool = False
):
    """
    [DEPRECATED] Wrapper for ia_native.gerar_artefato_stream
    
    This endpoint is mantido para compatibilidade com frontend.
    Internamente, usa agentes Python nativos (ia_native.py).
    """
    log_deprecation(f"/api/ia/{tipo_artefato}/gerar-stream", "/api/ia-native/{tipo_artefato}/gerar-stream")
    
    # Redirect to ia_native
    projeto_id = payload.projeto.get('projeto_id')
    prompt_adicional = payload.prompt_adicional
    
    return await ia_native.gerar_artefato_stream(
        tipo_artefato=tipo_artefato,
        projeto_id=projeto_id,
        prompt_adicional=prompt_adicional,
        db=db,
        current_user=current_user
    )


@router.post("/artefato/salvar")
async def salvar_artefato(
    request: SalvarArtefatoIARequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(auth_get_current_user)
):
    """
    Salva artefato gerado no banco de dados.
    
    NOTA: Este endpoint mantém a lógica original pois lida com
    dados já gerados pelo frontend. Não precisa de wrapper.
    """
    log_deprecation("/api/ia/artefato/salvar")
    
    # parse_date movido para utils.datetime_utils
    
    projeto_id = request.projeto_id
    tipo = request.tipo_artefato or "dfd"
    
    logger.info(f"[Salvar Artefato] Salvando {tipo} para projeto {projeto_id}")
    
    # Usar campo especifico com base no tipo
    if tipo == "pgr" or tipo == "riscos":
        artefato_data = request.pgr_data or {}
    elif tipo == "etp":
        artefato_data = request.etp_data or {}
    elif tipo == "tr":
        artefato_data = request.tr_data or {}
    elif tipo == "edital":
        artefato_data = request.edital_data or {}
    elif tipo == "pesquisa_precos":
        artefato_data = request.pesquisa_precos_data or {}
    else:
        artefato_data = request.artefato_data or {}

    if tipo not in ARTEFATO_MAP:
        raise HTTPException(
            status_code=400,
            detail=f"Tipo de artefato invalido: {tipo}"
        )

    ModelClass = ARTEFATO_MAP[tipo]["model"]

    # Buscar projeto
    result = await db.execute(
        select(Projeto).filter(Projeto.id == projeto_id)
    )
    projeto = result.scalars().first()

    if not projeto:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Projeto nao encontrado"
        )

    # Extrair conteudo e metadados
    content = artefato_data.get('content_blocks', artefato_data)
    audit = artefato_data.get('audit_metadata', {})
    artefatos_base = artefato_data.get('artefatos_base', None)

    # Extrair campos do sistema e do usuario
    campos_sistema = request.campos_sistema or {}
    campos_usuario = request.campos_usuario or {}

    if tipo == "dfd":
        result = await db.execute(
            select(func.count()).filter(DFD.projeto_id == projeto_id)
        )
        dfds_existentes = result.scalar() or 0

        model_data = {
            "descricao_objeto": content.get('descricao_objeto_padronizada', ''),
            "justificativa": content.get('justificativa_tecnica', ''),
            "setor_requisitante": campos_sistema.get('setor_requisitante', ''),
            "responsavel_requisitante": campos_sistema.get('responsavel_requisitante', ''),
            "alinhamento_pca": campos_sistema.get('alinhamento_pca', ''),
            "valor_estimado": campos_sistema.get('valor_estimado'),
            "grau_prioridade": campos_sistema.get('grau_prioridade', ''),
            "alinhamento_estrategico": campos_sistema.get('alinhamento_estrategico', ''),
            "data_pretendida": parse_date(campos_usuario.get('data_pretendida')),
            "responsavel_gestor": campos_usuario.get('responsavel_gestor', ''),
            "responsavel_fiscal": campos_usuario.get('responsavel_fiscal', ''),
            "prompt_ia": request.prompt_adicional,
            "metadata_ia": {"id_item_pca": content.get('id_item_pca'), **audit},
            "gerado_por_ia": True,
        }

        artefato = DFD(
            projeto_id=projeto_id,
            versao=dfds_existentes + 1,
            status=request.status or "rascunho",
            **model_data
        )
        db.add(artefato)

    elif tipo == "riscos" or tipo == "pgr":
        from app.models.artefatos import ItemRisco

        result = await db.execute(
            select(func.count()).filter(ModelClass.projeto_id == projeto_id)
        )
        artefatos_existentes = result.scalar() or 0

        itens_risco_data = content.pop('itens_risco', [])

        is_new_format = any(k in content for k in ['identificacao_objeto', 'resumo_analise_planejamento'])

        if is_new_format:
            model_data = {
                "projeto_id": projeto_id,
                "versao": artefatos_existentes + 1,
                "status": request.status or "rascunho",
                "gerado_por_ia": True,
                "prompt_ia": request.prompt_adicional,
                "metadata_ia": audit,
                "identificacao_objeto": content.get('identificacao_objeto', ''),
                "valor_estimado_total": content.get('valor_estimado_total'),
                "metodologia_adotada": content.get('metodologia_adotada', 'Matriz 5x5'),
                "resumo_analise_planejamento": content.get('resumo_analise_planejamento', ''),
                "resumo_analise_selecao": content.get('resumo_analise_selecao', ''),
                "resumo_analise_gestao": content.get('resumo_analise_gestao', ''),
            }
        else:
            model_data = _mapear_campos_artefato(tipo, content)
            model_data.update({
                "projeto_id": projeto_id,
                "versao": artefatos_existentes + 1,
                "status": request.status or "rascunho",
                "gerado_por_ia": True,
                "prompt_ia": request.prompt_adicional,
                "metadata_ia": audit,
            })

        if artefatos_base:
            model_data["artefatos_base"] = artefatos_base

        artefato = ModelClass(**model_data)
        db.add(artefato)
        await db.flush()

        # Save itens_risco
        if itens_risco_data and isinstance(itens_risco_data, list):
            for item_data in itens_risco_data:
                if not isinstance(item_data, dict):
                    continue

                item_risco = ItemRisco(
                    pgr_id=artefato.id,
                    origem=item_data.get('origem'),
                    fase_licitacao=item_data.get('fase_licitacao'),
                    categoria=item_data.get('categoria'),
                    evento=item_data.get('evento'),
                    causa=item_data.get('causa'),
                    consequencia=item_data.get('consequencia'),
                    probabilidade=item_data.get('probabilidade'),
                    impacto=item_data.get('impacto'),
                    tipo_tratamento=item_data.get('tipo_tratamento'),
                    acoes_preventivas=item_data.get('acoes_preventivas'),
                    acoes_contingencia=item_data.get('acoes_contingencia'),
                    alocacao_responsavel=item_data.get('alocacao_responsavel'),
                    gatilho_monitoramento=item_data.get('gatilho_monitoramento'),
                    responsavel_monitoramento=item_data.get('responsavel_monitoramento'),
                    frequencia_monitoramento=item_data.get('frequencia_monitoramento'),
                    status_risco=item_data.get('status_risco', 'Identificado'),
                )
                db.add(item_risco)

    else:
        # Outros tipos de artefato
        result = await db.execute(
            select(func.count()).filter(ModelClass.projeto_id == projeto_id)
        )
        artefatos_existentes = result.scalar() or 0

        model_data = _mapear_campos_artefato(tipo, content)
        model_data.update({
            "projeto_id": projeto_id,
            "versao": artefatos_existentes + 1,
            "status": request.status or "rascunho",
            "gerado_por_ia": True,
            "prompt_ia": request.prompt_adicional,
            "metadata_ia": audit,
        })

        if artefatos_base:
            model_data["artefatos_base"] = artefatos_base

        artefato = ModelClass(**model_data)
        db.add(artefato)

    await db.commit()
    await db.refresh(artefato)

    logger.info(f"[Salvar Artefato] {tipo.upper()} v{artefato.versao} salvo com sucesso (ID: {artefato.id})")

    return {
        "success": True,
        "artefato_id": artefato.id,
        "versao": artefato.versao,
        "tipo": tipo
    }




