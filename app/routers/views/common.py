"""
Sistema LIA - Views Common (Helpers e Configuracoes Compartilhadas)
====================================================================
Centraliza templates, CSRF, configuracoes de artefatos e funcoes utilitarias.

Autor: Equipe TRE-GO
Data: Janeiro 2026
"""

from fastapi import Request
from fastapi.templating import Jinja2Templates
from fastapi.responses import RedirectResponse
from slowapi import Limiter
from slowapi.util import get_remote_address
from typing import Optional
from collections import OrderedDict
import os
import secrets
import logging

from app.models.user import User
from app.models.artefatos import (
    DFD, DFD_CAMPOS_CONFIG,
    ARTEFATO_MAP
)

logger = logging.getLogger(__name__)


# ========== CONFIGURACAO DE TEMPLATES ==========

base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
templates_dir = os.path.join(base_dir, "templates")

if not os.path.exists(templates_dir):
    potential_frontend = os.path.join(os.path.dirname(base_dir), "frontend")
    if os.path.exists(potential_frontend):
        templates_dir = potential_frontend

templates = Jinja2Templates(directory=templates_dir)


# ========== RATE LIMITER ==========

limiter = Limiter(key_func=get_remote_address)


# ========== REDIS CONNECTION ==========

import redis
from app.config import settings

# Conexão Redis para CSRF tokens (síncrono para simplicidade)
try:
    redis_client = redis.from_url(settings.REDIS_URL, decode_responses=True)
    redis_client.ping()  # Verificar conexão
    REDIS_AVAILABLE = True
except Exception as e:
    logger.warning(f"Redis não disponível, usando fallback em memória: {e}")
    redis_client = None
    REDIS_AVAILABLE = False

# Fallback em memória se Redis não estiver disponível
csrf_tokens_memory = {}

# Tempo de expiração do CSRF token (30 minutos)
CSRF_TOKEN_EXPIRE = 1800


def get_session_id(request: Request) -> str:
    """Retorna ID da sessao do cookie ou gera um novo."""
    return request.cookies.get("session_id") or str(secrets.token_urlsafe(32))


def get_csrf_token_for_template(request: Request) -> str:
    """Gera token CSRF para template, armazenando em Redis."""
    session_id = get_session_id(request)
    token = secrets.token_urlsafe(32)
    
    if REDIS_AVAILABLE and redis_client:
        try:
            redis_client.setex(f"csrf:{session_id}", CSRF_TOKEN_EXPIRE, token)
        except Exception as e:
            logger.warning(f"Erro ao salvar CSRF no Redis: {e}")
            csrf_tokens_memory[session_id] = token
    else:
        csrf_tokens_memory[session_id] = token
    
    return token


def validate_csrf_token(session_id: str, token: str) -> bool:
    """Valida token CSRF consultando Redis."""
    # Se não há token fornecido, falha imediatamente
    if not token:
        return False
    
    if REDIS_AVAILABLE and redis_client:
        try:
            stored_token = redis_client.get(f"csrf:{session_id}")
            # CORREÇÃO: Retornar False se não houver token armazenado
            return stored_token == token if stored_token else False
        except Exception as e:
            logger.warning(f"Erro ao validar CSRF no Redis: {e}")
    
    # Fallback para memória
    stored_token = csrf_tokens_memory.get(session_id)
    # CORREÇÃO: Retornar False se não houver token armazenado
    return stored_token == token if stored_token else False


async def get_template_context(
    request: Request,
    usuario: Optional[User] = None,
    **kwargs
) -> dict:
    """
    Retorna o contexto base para templates, incluindo CSRF token.
    """
    csrf_token = get_csrf_token_for_template(request) if usuario else ""

    return {
        "request": request,
        "usuario": usuario,
        "csrf_token": csrf_token,
        **kwargs
    }


# ========== HELPER DE AUTENTICACAO ==========

def require_login(usuario: Optional[User]) -> Optional[RedirectResponse]:
    """
    Verifica se usuario esta logado. Retorna redirect se nao estiver.

    Uso:
        if redirect := require_login(usuario):
            return redirect
    """
    if not usuario:
        return RedirectResponse(url="/login", status_code=303)
    return None


# ========== CONFIGURACAO DE ARTEFATOS ==========

# Usar o mapa centralizado de artefatos (sem DFD para fluxo de workflow)
ARTEFATO_CONFIG = OrderedDict(
    sorted(
        [(k, v) for k, v in ARTEFATO_MAP.items() if k != "dfd"],
        key=lambda x: x[1].get("ordem", 99)
    )
)

# DFD tem configuração especial pois é o ponto de partida
DFD_CONFIG_DICT = ARTEFATO_MAP["dfd"]


def verificar_dependencias(projeto, tipo_artefato: str) -> dict:
    """
    Verifica se as dependencias de um artefato estao satisfeitas.
    
    Wrapper para o motor de fluxo centralizado.

    Args:
        projeto: Objeto Projeto com relacionamentos carregados
        tipo_artefato: Tipo do artefato (riscos, etp, tr, etc)

    Returns:
        dict com 'liberado' (bool) e 'faltando' (list)
    """
    from app.services.fluxo_engine import verificar_dependencias as _engine_verificar_deps
    return _engine_verificar_deps(projeto, tipo_artefato)


# ========== HELPERS DE DADOS (DB & SERIALIZATION) ==========

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload
from app.models.projeto import Projeto
from app.models.pac import PAC
import json

async def get_projeto_context(
    projeto_id: int,
    usuario_id: int,
    db: AsyncSession,
    load_artefatos: bool = False
) -> Optional[Projeto]:
    """
    Busca projeto garantindo que pertence ao usuario.
    Opcionalmente carrega todos os relacionamentos de artefatos.
    """
    query = select(Projeto).filter(
        Projeto.id == projeto_id,
        Projeto.usuario_id == usuario_id
    )
    
    if load_artefatos:
        query = query.options(
            selectinload(Projeto.justificativas_excepcionalidade),
            selectinload(Projeto.dfds),
            selectinload(Projeto.riscos),
            selectinload(Projeto.pesquisas_precos),
            selectinload(Projeto.etps),
            selectinload(Projeto.trs),
            selectinload(Projeto.editais),
            selectinload(Projeto.portarias_designacao),
            # Adesão a Ata
            selectinload(Projeto.relatorios_vantagem_economica),
            selectinload(Projeto.justificativas_vantagem_adesao),
            selectinload(Projeto.termos_aceite_fornecedor),
            # Dispensa por Valor Baixo
            selectinload(Projeto.trs_simplificados),
            selectinload(Projeto.avisos_dispensa_eletronica),
            selectinload(Projeto.justificativas_preco_escolha),
            selectinload(Projeto.certidoes_enquadramento),
            # Licitação Normal
            selectinload(Projeto.checklists_conformidade),
            selectinload(Projeto.minutas_contrato),
            # Contratação Direta
            selectinload(Projeto.avisos_publicidade_direta),
            selectinload(Projeto.justificativas_fornecedor_escolhido),
        )
        
    result = await db.execute(query)
    return result.scalars().first()

async def buscar_itens_pac(projeto: Projeto, db: AsyncSession) -> list:
    """Busca os itens do PAC vinculados ao projeto."""
    itens_pac = []
    pac_ids = []

    if projeto.itens_pac:
        if isinstance(projeto.itens_pac, str):
            try:
                pac_ids = json.loads(projeto.itens_pac)
            except:
                pac_ids = []
        elif isinstance(projeto.itens_pac, list):
            pac_ids = projeto.itens_pac

    # Otimizacao: Buscar todos de uma vez com IN
    if pac_ids:
        # Converter para int e filtrar invalidos
        ids_validos = []
        for pid in pac_ids:
            try:
                # Se for dict (novo formato: [{"id": 1, "quantidade": 10}, ...])
                if isinstance(pid, dict):
                    val = pid.get("id")
                    if val is not None:
                        ids_validos.append(int(val))
                # Se for valor direto (antigo formato: [1, 2, ...])
                else:
                    ids_validos.append(int(pid))
            except (ValueError, TypeError):
                continue
        
        if ids_validos:
            result = await db.execute(select(PAC).filter(PAC.id.in_(ids_validos)))
            itens_pac = result.scalars().all()

    return itens_pac

def serialize_item_pac(item: PAC) -> dict:
    """Converte um item PAC para DTO (dict)."""
    return {
        "id": item.id,
        "ano": item.ano,
        "tipo_pac": item.tipo_pac,
        "iniciativa": item.iniciativa,
        "objetivo": item.objetivo,
        "unidade_tecnica": item.unidade_tecnica,
        "unidade_administrativa": item.unidade_administrativa,
        "detalhamento": item.detalhamento,
        "descricao": item.descricao,
        "quantidade": item.quantidade,
        "unidade": item.unidade,
        "frequencia": item.frequencia,
        "valor_previsto": item.valor_previsto,
        "justificativa": item.justificativa,
        "prioridade": item.prioridade,
        "catmat_catser": item.catmat_catser,
        "tipo_contratacao": item.tipo_contratacao,
        "fase": item.fase,
        "numero_contrato": item.numero_contrato,
        "vencimento_contrato": item.vencimento_contrato,
        "contratacao_continuada": item.contratacao_continuada,
    }

