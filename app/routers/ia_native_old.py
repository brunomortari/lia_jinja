"""
Sistema LIA - Router de IA Nativa (Python + OpenRouter)
========================================================
Endpoints para geração de artefatos usando agentes Python nativos.

REFATORADO (v2): Usa factory pattern para endpoints de chat.
Cada artefato tem sua config em app/routers/ia_chat/{tipo}.py

Artefatos suportados (via factory):
- DFD: Documento de Formalização da Demanda
- ETP: Estudo Técnico Preliminar
- PGR: Plano de Gerenciamento de Riscos
- TR: Termo de Referência
- Edital: Edital de Licitação
- JE: Justificativa de Excepcionalidade
- PesquisaPrecos: Pesquisa de Preços

Endpoints genéricos (aplicáveis a qualquer artefato):
- POST /{tipo}/gerar/stream — Direct generation (sem chat)
- POST /{tipo}/gerar-json — Generate JSON
- POST /{tipo}/regenerar-campo/stream — Regen single field
- GET /agentes — List all agents
- GET /agentes/{tipo} — Get agent fields

Autor: Equipe TRE-GO
Data: Fevereiro 2026
"""

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from datetime import datetime
import json
import logging
import asyncio

from app.database import get_db
from app.config import settings
from app.models.projeto import Projeto
from app.models.user import User
from app.auth import current_active_user as auth_get_current_user
from app.models.artefatos import DFD, ETP, TR, Riscos, Edital, PesquisaPrecos
from app.models.skill import Skill
from sqlalchemy.orm import selectinload
from app.services.agents import (
    DFDAgent, ETPAgent, PGRAgent, TRAgent, EditalAgent,
    AdeAgent, RdveAgent, JpefAgent, JvaAgent, TrsAgent
)
from app.services.deep_research import deep_research_service
from pydantic import BaseModel
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/ia", tags=["🧠 IA Nativa"])

# ========== IMPORT CHAT ROUTERS FROM FACTORY ==========
from app.routers.ia_chat import combined_router as chat_routers
router.include_router(chat_routers, prefix="")  # Already prefixed in factory


# ========== ROUTER ==========

router = APIRouter(prefix="/ia-native", tags=["IA Nativa"])


# Mapeamento de tipo para agente
AGENT_MAP = {
    "dfd": DFDAgent,
    "etp": ETPAgent,
    "pgr": PGRAgent,
    "riscos": PGRAgent,  # Alias
    "tr": TRAgent,
    "edital": EditalAgent,
}

class DeepResearchRequest(BaseModel):
    topic: str
    context: str = ""


# ========== HELPERS ==========

async def get_projeto_contexto(
    projeto_id: int,
    db: AsyncSession,
    include_artefatos: bool = True
) -> dict:
    """
    Monta o contexto completo de um projeto para os agentes.
    
    Args:
        projeto_id: ID do projeto
        db: Sessão do banco
        include_artefatos: Se deve incluir artefatos aprovados
        
    Returns:
        Dicionário com contexto do projeto
    """
    # Buscar projeto
    result = await db.execute(
        select(Projeto).filter(Projeto.id == projeto_id)
    )
    projeto = result.scalars().first()
    
    if not projeto:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Projeto {projeto_id} não encontrado"
        )
    
    # Buscar itens PAC
    itens_pac = await pac_service.get_itens_by_projeto(projeto, db)
    
    # Montar contexto base
    contexto = {
        "projeto_id": projeto.id,
        "projeto_titulo": projeto.titulo,
        "setor_usuario": "Unidade Requisitante",  # TODO: obter do usuário logado
        "itens_pac": itens_pac or [],
    }
    
    if not include_artefatos:
        return contexto
    
    # Buscar artefatos aprovados para contexto
    # DFD
    dfd_result = await db.execute(
        select(DFD)
        .filter(DFD.projeto_id == projeto_id, DFD.status.in_(["aprovado", "publicado"]))
        .order_by(DFD.data_criacao.desc())
        .limit(1)
    )
    dfd = dfd_result.scalars().first()
    if dfd:
        contexto["dfd"] = {
            "descricao_objeto": dfd.descricao_objeto,
            "justificativa": dfd.justificativa,
        }
    
    # Pesquisa de Preços
    pp_result = await db.execute(
        select(PesquisaPrecos)
        .filter(PesquisaPrecos.projeto_id == projeto_id, PesquisaPrecos.status.in_(["aprovado", "publicado"]))
        .order_by(PesquisaPrecos.data_criacao.desc())
        .limit(1)
    )
    pp = pp_result.scalars().first()
    if pp:
        contexto["pesquisa_precos"] = {"valor_total_cotacao": pp.valor_total_cotacao}
    
    # ETP
    etp_result = await db.execute(
        select(ETP)
        .filter(ETP.projeto_id == projeto_id, ETP.status.in_(["aprovado", "publicado"]))
        .order_by(ETP.data_criacao.desc())
        .limit(1)
    )
    etp = etp_result.scalars().first()
    if etp:
        contexto["etp"] = {"descricao_necessidade": etp.descricao_necessidade}
    
    # PGR
    pgr_result = await db.execute(
        select(Riscos)
        .filter(Riscos.projeto_id == projeto_id, Riscos.status.in_(["aprovado", "publicado"]))
        .order_by(Riscos.data_criacao.desc())
        .limit(1)
    )
    pgr = pgr_result.scalars().first()
    if pgr:
        contexto["pgr"] = {"identificacao_objeto": pgr.identificacao_objeto}
    
    # TR
    tr_result = await db.execute(
        select(TR)
        .filter(TR.projeto_id == projeto_id, TR.status.in_(["aprovado", "publicado"]))
        .order_by(TR.data_criacao.desc())
        .limit(1)
    )
    tr = tr_result.scalars().first()
    if tr:
        contexto["tr"] = {"definicao_objeto": tr.definicao_objeto}
    
    return contexto


async def stream_agent_response(agent, contexto: dict, prompt_adicional: str = None):
    """
    Generator que formata a resposta do agente como SSE.
    
    Args:
        agent: Instância do agente
        contexto: Contexto do projeto
        prompt_adicional: Instruções extras
        
    Yields:
        Eventos SSE formatados
    """
    reasoning_buffer = ""
    content_buffer = ""
    try:
        async for chunk_data in agent.gerar(contexto, prompt_adicional):
            if chunk_data["type"] == "content":
                chunk = chunk_data["content"]
                content_buffer += chunk
                # Enviar conteúdo acumulado (Items Paradigm)
                yield f"data: {json.dumps({'content': content_buffer})}\n\n"
            elif chunk_data["type"] == "reasoning":
                reasoning_chunk = chunk_data["content"]
                reasoning_buffer += reasoning_chunk
                # Enviar reasoning acumulado se necessário
                yield f"data: {json.dumps({'type': 'reasoning', 'content': reasoning_buffer})}\n\n"
        
        # Tentar parsear JSON final
        try:
            # Limpar markdown se presente
            cleaned = content_buffer.strip()
            if cleaned.startswith("```json"):
                cleaned = cleaned[7:]
            if cleaned.startswith("```"):
                cleaned = cleaned[3:]
            if cleaned.endswith("```"):
                cleaned = cleaned[:-3]
            
            parsed = json.loads(cleaned.strip())
            # Enviar evento de conclusão com JSON parseado
            yield f"event: complete\ndata: {json.dumps({'success': True, 'data': parsed})}\n\n"
        except json.JSONDecodeError:
            # Se não for JSON válido, enviar resposta bruta
            yield f"event: complete\ndata: {json.dumps({'success': True, 'raw': content_buffer})}\n\n"
            
    except Exception as e:
        logger.error(f"Erro no streaming: {e}")
        yield f"event: error\ndata: {json.dumps({'error': str(e)})}\n\n"


# ========== ENDPOINTS DE GERAÇÃO ==========

@router.post("/{tipo_artefato}/gerar/stream")
async def gerar_artefato_stream(
    tipo_artefato: str,
    projeto_id: int,
    prompt_adicional: str = None,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(auth_get_current_user),
):
    """
    Gera artefato usando agente Python nativo com streaming SSE.
    
    Args:
        tipo_artefato: Tipo do artefato (dfd, etp, pgr, tr, edital)
        projeto_id: ID do projeto
        prompt_adicional: Instruções extras do usuário
        
    Returns:
        StreamingResponse com eventos SSE
    """
    # Validar tipo de artefato
    if tipo_artefato not in AGENT_MAP:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Tipo de artefato inválido: {tipo_artefato}. "
                   f"Valores válidos: {list(AGENT_MAP.keys())}"
        )
    
    # Obter contexto do projeto
    contexto = await get_projeto_contexto(projeto_id, db)
    
    # Instanciar agente
    AgentClass = AGENT_MAP[tipo_artefato]
    agent = AgentClass()
    
    logger.info(f"Iniciando geração de {tipo_artefato} para projeto {projeto_id}")
    
    return StreamingResponse(
        stream_agent_response(agent, contexto, prompt_adicional),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        }
    )


@router.post("/{tipo_artefato}/gerar")
async def gerar_artefato_json(
    tipo_artefato: str,
    projeto_id: int,
    prompt_adicional: str = None,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(auth_get_current_user),
):
    """
    Gera artefato usando agente Python nativo (resposta JSON completa).
    
    Útil para testes ou quando não precisa de streaming.
    
    Args:
        tipo_artefato: Tipo do artefato (dfd, etp, pgr, tr, edital)
        projeto_id: ID do projeto
        prompt_adicional: Instruções extras do usuário
        
    Returns:
        JSON com o artefato gerado
    """
    # Validar tipo de artefato
    if tipo_artefato not in AGENT_MAP:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Tipo de artefato inválido: {tipo_artefato}"
        )
    
    # Obter contexto do projeto
    contexto = await get_projeto_contexto(projeto_id, db)
    
    # Instanciar agente e gerar
    AgentClass = AGENT_MAP[tipo_artefato]
    agent = AgentClass()
    
    logger.info(f"Gerando {tipo_artefato} para projeto {projeto_id} (modo JSON)")
    
    try:
        resultado = await agent.gerar_json(contexto, prompt_adicional)
        return {
            "success": True,
            "tipo_artefato": tipo_artefato,
            "projeto_id": projeto_id,
            "data": resultado,
            "generated_at": now_brasilia().isoformat(),
        }
    except Exception as e:
        logger.error(f"Erro ao gerar {tipo_artefato}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erro ao gerar artefato: {str(e)}"
        )


# ========== ENDPOINT DE REGENERAÇÃO DE CAMPO ==========

@router.post("/{tipo_artefato}/regenerar-campo/stream")
async def regenerar_campo_stream(
    tipo_artefato: str,
    projeto_id: int,
    campo: str,
    valor_atual: str = None,
    instrucoes: str = None,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(auth_get_current_user),
):
    """
    Regenera um campo específico do artefato com streaming.
    
    Args:
        tipo_artefato: Tipo do artefato
        projeto_id: ID do projeto
        campo: Nome do campo a regenerar
        valor_atual: Valor atual do campo (opcional)
        instrucoes: Instruções específicas para regeneração
        
    Returns:
        StreamingResponse com o novo valor do campo
    """
    if tipo_artefato not in AGENT_MAP:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Tipo de artefato inválido: {tipo_artefato}"
        )
    
    # Obter contexto (sem artefatos para regeneração)
    contexto = await get_projeto_contexto(projeto_id, db, include_artefatos=False)
    
    # Instanciar agente
    AgentClass = AGENT_MAP[tipo_artefato]
    agent = AgentClass()
    
    # Validar se o campo existe no agente
    if campo not in agent.campos:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Campo '{campo}' não existe no artefato {tipo_artefato}. "
                   f"Campos válidos: {agent.campos}"
        )
    
    logger.info(f"Regenerando campo '{campo}' do {tipo_artefato} para projeto {projeto_id}")
    
    async def stream_regenerate():
        content_buffer = ""
        try:
            async for chunk in agent.regenerar_campo(campo, contexto, valor_atual, instrucoes):
                content_buffer += chunk
                yield f"data: {json.dumps({'content': content_buffer})}\n\n"
            
            yield f"event: complete\ndata: {json.dumps({'success': True, 'campo': campo, 'valor': content_buffer})}\n\n"
        except Exception as e:
            logger.error(f"Erro ao regenerar campo: {e}")
            yield f"event: error\ndata: {json.dumps({'error': str(e)})}\n\n"
    
    return StreamingResponse(
        stream_regenerate(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
        }
    )


# ========== ENDPOINT DE INFORMAÇÕES DOS AGENTES ==========

@router.get("/agentes")
async def listar_agentes():
    """
    Lista todos os agentes disponíveis e seus campos.
    
    Returns:
        Informações sobre os agentes e campos gerados
    """
    agentes_info = {}
    
    for tipo, AgentClass in AGENT_MAP.items():
        if tipo == "riscos":  # Skip alias
            continue
        agent = AgentClass()
        agentes_info[tipo] = {
            "nome": AgentClass.__name__,
            "campos": agent.campos,
            "temperature": agent.temperature,
            "model": agent.model,
        }
    
    return {
        "agentes": agentes_info,
        "total": len(agentes_info),
    }


@router.get("/agentes/{tipo_artefato}/campos")
async def listar_campos_agente(tipo_artefato: str):
    """
    Lista os campos gerados por um agente específico.
    
    Args:
        tipo_artefato: Tipo do artefato
        
    Returns:
        Lista de campos do agente
    """
    if tipo_artefato not in AGENT_MAP:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Tipo de artefato inválido: {tipo_artefato}"
        )
    
    AgentClass = AGENT_MAP[tipo_artefato]
    agent = AgentClass()
    
    return {
        "tipo_artefato": tipo_artefato,
        "campos": agent.campos,
    }


# ========== SCHEMAS PARA CHAT ==========

class ChatMessageInput(BaseModel):
    """Mensagem enviada pelo usuário no chat."""
    content: str
    history: List[dict] = []  # Lista de {"role": "user"|"assistant", "content": "..."}
    gestor: Optional[str] = None
    fiscal: Optional[str] = None
    data_limite: Optional[str] = None
    model: Optional[str] = None  # Modelo de IA selecionado pelo usuário
    attachments: Optional[List[Dict[str, Any]]] = None # Anexos {type, url, content, ...}


class ChatGenerateInput(BaseModel):
    """Dados para geração do DFD a partir do chat."""
    history: List[dict] = []
    gestor: Optional[str] = None
    fiscal: Optional[str] = None
    data_limite: Optional[str] = None
    model: Optional[str] = None  # Modelo de IA selecionado pelo usuário
    attachments: Optional[List[Dict[str, Any]]] = None  # Anexos com extracted_text
    temperatura: Optional[float] = 0.6  # Temperatura para geração


class ChatInitResponse(BaseModel):
    """Resposta inicial do chat."""
    mensagem_inicial: str
    projeto_id: int
    projeto_titulo: str
    itens_pac_count: int


# ========== ENDPOINTS DE CHAT (DFD) ==========

@router.get("/dfd/chat/init/{projeto_id}")
async def iniciar_chat_dfd(
    projeto_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(auth_get_current_user),
) -> ChatInitResponse:
    """
    Inicializa o chat para geração de DFD.
    
    Retorna a mensagem inicial da IA e dados do projeto.
    """
    # Buscar contexto do projeto
    context = await _build_chat_context(projeto_id, db, "dfd")
    
    # Criar agente e obter mensagem inicial
    agent = DFDChatAgent()
    mensagem_inicial = agent.get_mensagem_inicial(context)
    
    return ChatInitResponse(
        mensagem_inicial=mensagem_inicial,
        projeto_id=context.projeto_id,
        projeto_titulo=context.projeto_titulo,
        itens_pac_count=len(context.itens_pac),
    )


@router.post("/dfd/chat/{projeto_id}")
async def chat_dfd(
    projeto_id: int,
    message: ChatMessageInput,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(auth_get_current_user),
):
    """
    Processa uma mensagem do chat e retorna resposta em streaming.

    Quando a IA detectar que está pronta para gerar, retorna:
    {"action": "generate", "message": "..."}
    """
    # Buscar contexto do projeto
    context = await _build_chat_context(projeto_id, db, "dfd")

    # Se gestor/fiscal/data vieram do formulário, adicionar ao contexto
    # para que a IA saiba que já temos esses dados
    logger.info(f"[DFD Chat] Dados recebidos do formulário: gestor='{message.gestor}', fiscal='{message.fiscal}', data='{message.data_limite}'")
    
    if message.gestor:
        context.dados_coletados['responsavel_gestor'] = message.gestor
        logger.info(f"[DFD Chat] Gestor adicionado ao contexto: {message.gestor}")
    if message.fiscal:
        context.dados_coletados['responsavel_fiscal'] = message.fiscal
        logger.info(f"[DFD Chat] Fiscal adicionado ao contexto: {message.fiscal}")
    if message.data_limite:
        context.dados_coletados['data_pretendida'] = message.data_limite
        logger.info(f"[DFD Chat] Data limite adicionada ao contexto: {message.data_limite}")
    
    logger.info(f"[DFD Chat] dados_coletados final: {context.dados_coletados}")

    # Converter histórico para objetos Message
    history = [
        Message(role=msg["role"], content=msg["content"])
        for msg in message.history
    ]

    # Usar modelo selecionado pelo usuário ou padrão
    modelo_ia = message.model or settings.OPENROUTER_DEFAULT_MODEL
    logger.info(f"[DFD Chat] Modelo de IA selecionado: {modelo_ia}")
    agent = DFDChatAgent(model_override=modelo_ia)
    
    async def stream_chat():
        reasoning_buffer = ""
        content_buffer = ""
        try:
            async for chunk_data in agent.chat(message.content, history, context, message.attachments):
                # chunk_data agora eh um dict {"type": "...", "content": "..."}
                
                if chunk_data["type"] == "reasoning":
                    reasoning_buffer += chunk_data["content"]
                    yield f"data: {json.dumps({'type': 'reasoning', 'content': reasoning_buffer})}\n\n"
                
                elif chunk_data["type"] == "content":
                    chunk = chunk_data["content"]
                    content_buffer += chunk
                    yield f"data: {json.dumps({'type': 'chunk', 'content': content_buffer})}\n\n"
                    # Forcar flush do evento
                    await asyncio.sleep(0)

            # Verificar se a resposta contém marcador de geração
            # Aceita [GERAR_DFD] ou variações como "gerar agora", "pode gerar", confirmação do usuário
            should_generate = '[GERAR_DFD]' in content_buffer
            
            # Fallback: detectar se o usuário autorizou a geração na mensagem atual
            if not should_generate:
                user_msg = message.content.lower().strip()
                authorization_phrases = [
                    'gere', 'gerar', 'pode gerar', 'inicie', 'inicie a geração',
                    'sim', 'ok', 'confirmo', 'autorizo', 'prossiga', 'vai', 'manda',
                    'pode iniciar', 'inicia', 'gera', 'faça', 'faz', 'execute',
                    'confirma', 'positivo', 'afirmativo', 'isso', 'isso mesmo'
                ]
                if any(phrase in user_msg for phrase in authorization_phrases):
                    # Verificar se já temos dados suficientes para gerar
                    has_content = len(history) >= 2  # Pelo menos uma troca de mensagens
                    has_gestor = context.dados_coletados.get('responsavel_gestor')
                    has_fiscal = context.dados_coletados.get('responsavel_fiscal')
                    if has_content and has_gestor and has_fiscal:
                        should_generate = True
                        logger.info(f"[DFD Chat] Autorização detectada na mensagem do usuário: '{user_msg}'")
            
            if should_generate:
                # Remover o marcador da mensagem exibida
                buffer_limpo = content_buffer.replace('[GERAR_DFD]', '').strip()
                yield f"data: {json.dumps({'type': 'action', 'action': 'generate', 'message': 'Iniciando geração do DFD...'})}\n\n"

            yield f"data: {json.dumps({'type': 'done', 'full_response': content_buffer})}\n\n"

        except Exception as e:
            logger.error(f"Erro no chat DFD: {e}")
            yield f"data: {json.dumps({'type': 'error', 'error': str(e)})}\n\n"
    
    return StreamingResponse(
        stream_chat(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        }
    )


@router.post("/dfd/chat/{projeto_id}/gerar")
async def gerar_dfd_from_chat(
    projeto_id: int,
    body: ChatGenerateInput,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(auth_get_current_user),
):
    """
    Gera o DFD baseado no histórico da conversa.

    Chamado quando a IA sinaliza que está pronta para gerar.
    """
    logger.info(f"[DFD Gen] === INICIANDO GERAÇÃO para projeto {projeto_id} ===")
    logger.info(f"[DFD Gen] Histórico recebido: {len(body.history)} mensagens")
    logger.info(f"[DFD Gen] Dados do formulário: gestor={body.gestor}, fiscal={body.fiscal}, data={body.data_limite}")
    
    # Buscar contexto do projeto
    context = await _build_chat_context(projeto_id, db, "dfd")
    logger.info(f"[DFD Gen] Contexto construído: projeto={context.projeto_titulo}, itens_pac={len(context.itens_pac)}")

    # Se gestor/fiscal/data vieram do formulário, adicionar ao contexto
    if body.gestor:
        context.dados_coletados['responsavel_gestor'] = body.gestor
    if body.fiscal:
        context.dados_coletados['responsavel_fiscal'] = body.fiscal
    if body.data_limite:
        context.dados_coletados['data_pretendida'] = body.data_limite

    # Converter histórico para objetos Message
    messages = [
        Message(role=msg["role"], content=msg["content"])
        for msg in body.history
    ]
    logger.info(f"[DFD Gen] Mensagens convertidas: {len(messages)}")

    # Incluir texto extraído dos anexos (base de conhecimento) no contexto
    if body.attachments:
        textos_anexos = []
        for att in body.attachments:
            if att.get("extracted_text"):
                textos_anexos.append(f"[{att.get('filename', 'arquivo')}]: {att['extracted_text']}")
        if textos_anexos:
            context.dados_coletados['base_conhecimento'] = "\n\n".join(textos_anexos)
            logger.info(f"[DFD Gen] Base de conhecimento incluída: {len(textos_anexos)} arquivo(s)")

    # Criar agente com modelo selecionado
    modelo_ia = body.model or settings.OPENROUTER_DEFAULT_MODEL
    logger.info(f"[DFD Gen] Modelo de IA selecionado: {modelo_ia}")
    agent = DFDChatAgent(model_override=modelo_ia)
    logger.info(f"[DFD Gen] Agente criado, iniciando geração...")
    
    async def stream_generate():
        reasoning_buffer = ""
        content_buffer = ""
        chunk_count = 0
        try:
            async for chunk_data in agent.gerar(context, messages):
                if chunk_data["type"] == "reasoning":
                    reasoning_buffer += chunk_data["content"]
                    yield f"data: {json.dumps({'type': 'reasoning', 'content': reasoning_buffer})}\n\n"
                
                elif chunk_data["type"] == "content":
                    chunk = chunk_data["content"]
                    chunk_count += 1
                    content_buffer += chunk
                    if chunk_count <= 5 or chunk_count % 20 == 0:
                        logger.debug(f"[DFD Gen] Chunk #{chunk_count}: {chunk[:50]}...")
                    yield f"data: {json.dumps({'type': 'chunk', 'content': content_buffer})}\n\n"
            
            logger.info(f"[DFD Gen] Geração completa. Total chunks: {chunk_count}, buffer length: {len(content_buffer)}")
            logger.info(f"[DFD Gen] Buffer preview: {content_buffer[:500]}...")
            
            # Tentar parsear JSON final
            try:
                cleaned = content_buffer.strip()
                if cleaned.startswith("```json"):
                    cleaned = cleaned[7:]
                if cleaned.startswith("```"):
                    cleaned = cleaned[3:]
                if cleaned.endswith("```"):
                    cleaned = cleaned[:-3]
                
                parsed = json.loads(cleaned.strip())
                logger.info(f"[DFD Gen] JSON parseado com sucesso. Campos: {list(parsed.keys())}")
                yield f"data: {json.dumps({'type': 'complete', 'success': True, 'data': parsed})}\n\n"
            except json.JSONDecodeError as je:
                logger.warning(f"[DFD Gen] Falha ao parsear JSON: {je}")
                logger.warning(f"[DFD Gen] Raw buffer: {content_buffer[:300]}...")
                yield f"data: {json.dumps({'type': 'complete', 'success': True, 'raw': content_buffer})}\n\n"
                
        except Exception as e:
            logger.error(f"[DFD Gen] === ERRO NA GERAÇÃO ===: {e}", exc_info=True)
            yield f"data: {json.dumps({'type': 'error', 'error': str(e)})}\n\n"
    
    return StreamingResponse(
        stream_generate(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        }
    )


class RegenerarCampoInput(BaseModel):
    """Input para regenerar um campo específico do DFD."""
    campo: str
    history: List[Dict[str, Any]] = []
    prompt_adicional: Optional[str] = None
    valor_atual: Optional[str] = None
    model: Optional[str] = None  # Modelo de IA selecionado
    temperatura: Optional[float] = 0.6  # Temperatura para geração


@router.post("/dfd/chat/{projeto_id}/regenerar-campo")
async def regenerar_campo_dfd(
    projeto_id: int,
    body: RegenerarCampoInput,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(auth_get_current_user),
):
    """
    Regenera um campo específico do DFD usando IA.
    
    Args:
        projeto_id: ID do projeto
        body: Campo a regenerar, histórico e instruções adicionais
        
    Returns:
        JSON com o novo valor do campo
    """
    logger.info(f"[DFD Regen] Regenerando campo '{body.campo}' para projeto {projeto_id}")
    logger.info(f"[DFD Regen] Prompt adicional: {body.prompt_adicional}")
    logger.info(f"[DFD Regen] Valor atual: {body.valor_atual[:100] if body.valor_atual else 'Nenhum'}...")
    
    # Labels dos campos para mensagens amigáveis
    campos_labels = {
        'numero_dfd': 'Número do DFD',
        'setor_requisitante': 'Setor Requisitante',
        'responsavel_requisitante': 'Responsável pela Demanda',
        'valor_estimado': 'Estimativa Preliminar',
        'descricao_objeto_padronizada': 'Descrição do Objeto',
        'justificativa_tecnica': 'Justificativa da Necessidade',
        'analise_alinhamento': 'Alinhamento Estratégico',
        'prioridade_sugerida': 'Grau de Prioridade',
        'data_pretendida': 'Data Pretendida',
        'responsavel_gestor': 'Gestor do Contrato',
        'responsavel_fiscal': 'Fiscal do Contrato',
    }
    
    campo_label = campos_labels.get(body.campo, body.campo)
    
    # Buscar contexto do projeto
    context = await _build_chat_context(projeto_id, db, "dfd")
    
    # Construir prompt para regeneração do campo específico
    conversa_resumo = ""
    if body.history:
        partes = []
        for msg in body.history[-5:]:  # Últimas 5 mensagens
            prefixo = "Usuário:" if msg.get("role") == "user" else "IA:"
            partes.append(f"{prefixo} {msg.get('content', '')[:200]}")
        conversa_resumo = "\n".join(partes)
    
    system_prompt = f"""Você é um especialista em contratações públicas do TRE-GO.
    
Sua tarefa é regenerar APENAS o campo "{campo_label}" de um DFD (Documento de Formalização da Demanda).

REGRAS:
1. Retorne APENAS o novo texto do campo, sem JSON, sem aspas extras, sem markdown
2. Use linguagem formal e objetiva
3. Foque na fundamentação legal (Lei 14.133/2021)
4. Se o usuário deu instruções específicas, siga-as
5. O texto deve ser conciso mas completo"""

    user_prompt = f"""PROJETO: {context.projeto_titulo}

CAMPO A REGENERAR: {campo_label}

VALOR ATUAL DO CAMPO:
{body.valor_atual or 'Não preenchido'}

CONTEXTO DA CONVERSA:
{conversa_resumo or 'Não disponível'}

INSTRUÇÕES DO USUÁRIO:
{body.prompt_adicional or 'Nenhuma instrução específica - melhore o texto mantendo a essência.'}

Gere o novo texto para o campo "{campo_label}". Retorne APENAS o texto, sem formatação extra."""

    try:
        from openai import AsyncOpenAI
        client = AsyncOpenAI(
            api_key=settings.OPENROUTER_API_KEY,
            base_url=settings.OPENROUTER_BASE_URL,
            timeout=settings.OPENROUTER_TIMEOUT,
        )
        
        response = await client.chat.completions.create(
            model=settings.OPENROUTER_DEFAULT_MODEL,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            temperature=0.6,
            max_tokens=2048,
        )
        
        novo_valor = response.choices[0].message.content.strip()
        
        # Limpar possíveis aspas extras
        if novo_valor.startswith('"') and novo_valor.endswith('"'):
            novo_valor = novo_valor[1:-1]
        
        logger.info(f"[DFD Regen] Campo '{body.campo}' regenerado com sucesso. Novo valor: {novo_valor[:100]}...")
        
        return {
            "success": True,
            "campo": body.campo,
            "value": novo_valor,
            "label": campo_label
        }
        
    except Exception as e:
        logger.error(f"[DFD Regen] Erro ao regenerar campo: {e}", exc_info=True)
        return {
            "success": False,
            "error": str(e),
            "campo": body.campo
        }


async def _build_chat_context(projeto_id: int, db: AsyncSession, tipo_artefato: str = None) -> ChatContext:
    """Constrói o ChatContext para o agente conversacional."""

    # Buscar projeto
    result = await db.execute(
        select(Projeto).filter(Projeto.id == projeto_id)
    )
    projeto = result.scalars().first()

    if not projeto:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Projeto {projeto_id} não encontrado"
        )

    # Buscar itens PAC
    itens_pac = await pac_service.get_itens_by_projeto(projeto, db)

    # Buscar skills ativas
    skills_ativas = await _load_skills_ativas(projeto_id, db, tipo_artefato, projeto.usuario_id)

    # Contexto base
    context = ChatContext(
        projeto_id=projeto.id,
        projeto_titulo=projeto.titulo,
        setor_usuario="Unidade Requisitante",
        itens_pac=itens_pac or [],
        skills=skills_ativas,
    )
    if skills_ativas:
        logger.info(f"[Context] {len(skills_ativas)} skill(s) ativa(s) para projeto {projeto_id}")
    
    # Buscar artefatos existentes para contexto
    # DFD
    dfd_result = await db.execute(
        select(DFD)
        .filter(DFD.projeto_id == projeto_id, DFD.status.in_(["aprovado", "publicado"]))
        .order_by(DFD.data_criacao.desc())
        .limit(1)
    )
    dfd = dfd_result.scalars().first()
    if dfd:
        context.dfd = {
            "descricao_objeto": dfd.descricao_objeto,
            "justificativa": dfd.justificativa,
        }
    
    # Pesquisa de Preços
    pp_result = await db.execute(
        select(PesquisaPrecos)
        .filter(PesquisaPrecos.projeto_id == projeto_id, PesquisaPrecos.status.in_(["aprovado", "publicado"]))
        .order_by(PesquisaPrecos.data_criacao.desc())
        .limit(1)
    )
    pp = pp_result.scalars().first()
    if pp:
        context.pesquisa_precos = {
            "valor_total_cotacao": pp.valor_total_cotacao,
        }

    return context


async def _load_skills_ativas(projeto_id: int, db: AsyncSession, tipo_artefato: str = None, user_id: int = None) -> list:
    """Carrega skills ativas (sistema + usuario), filtradas por tipo de artefato."""
    conditions = [Skill.escopo == "system"]
    
    # Se tiver user_id, inclui skills do usuario
    if user_id:
        conditions.append(Skill.usuario_id == user_id)
    
    # Se nao tiver user_id, tenta buscar usuario atraves do projeto (menos ideal, mas fallback)
    # Mas como removemos a relacao projeto-usuario direta no load_skills, melhor depender do user_id
    
    query = select(Skill).filter(or_(*conditions))
    
    # Filtragem por tipo de artefato foi removida na simplificação
    # Se futuramente quisermos filtrar por capabilities/tools, implementar aqui
    # Por enquanto, carrega todas as skills ativas do escopo
    
    query = query.order_by(Skill.escopo.desc(), Skill.nome)
    result = await db.execute(query)
    
    skills = []
    for skill in result.scalars().all():
        skills.append(skill.to_dict())
    return skills


# ========== ENDPOINTS DE CHAT (PGR) ==========

class PGRChatMessageInput(BaseModel):
    """Mensagem enviada pelo usuario no chat PGR."""
    content: str
    history: List[dict] = []
    areas_preocupacao: Optional[str] = None
    prazo_desejado: Optional[str] = None
    historico_problemas: Optional[str] = None
    equipe_responsavel: Optional[str] = None
    model: Optional[str] = None
    active_skills: Optional[List[int]] = []


class PGRChatGenerateInput(BaseModel):
    """Dados para geracao do PGR a partir do chat."""
    history: List[dict] = []
    areas_preocupacao: Optional[str] = None
    prazo_desejado: Optional[str] = None
    historico_problemas: Optional[str] = None
    equipe_responsavel: Optional[str] = None
    gestor: Optional[str] = None
    fiscal: Optional[str] = None
    data_limite: Optional[str] = None
    attachments: Optional[List[Dict[str, Any]]] = None
    model: Optional[str] = None
    active_skills: Optional[List[int]] = []


class PGRChatInitResponse(BaseModel):
    """Resposta inicial do chat PGR."""
    mensagem_inicial: str
    projeto_id: int
    projeto_titulo: str
    dfd_aprovado: bool
    cotacao_aprovada: bool
    valor_estimado: float


@router.get("/pgr/chat/init/{projeto_id}")
async def iniciar_chat_pgr(
    projeto_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(auth_get_current_user),
) -> PGRChatInitResponse:
    """
    Inicializa o chat para geracao de PGR.

    Retorna a mensagem inicial da IA e dados do projeto/artefatos aprovados.
    """
    # Buscar contexto do projeto com artefatos aprovados
    context = await _build_pgr_chat_context(projeto_id, db)

    # Criar agente e obter mensagem inicial
    agent = PGRChatAgent()
    mensagem_inicial = agent.get_mensagem_inicial(context)

    # Calcular valor estimado
    valor_estimado = 0.0
    if context.pesquisa_precos:
        valor_estimado = context.pesquisa_precos.get('valor_total_cotacao', 0)

    return PGRChatInitResponse(
        mensagem_inicial=mensagem_inicial,
        projeto_id=context.projeto_id,
        projeto_titulo=context.projeto_titulo,
        dfd_aprovado=context.dfd is not None,
        cotacao_aprovada=context.pesquisa_precos is not None,
        valor_estimado=valor_estimado,
    )


@router.post("/pgr/chat/{projeto_id}")
async def chat_pgr(
    projeto_id: int,
    message: PGRChatMessageInput,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(auth_get_current_user),
):
    """
    Processa uma mensagem do chat PGR e retorna resposta em streaming.

    Quando a IA detectar que esta pronta para gerar, retorna:
    {"action": "generate", "message": "..."}
    """
    # Buscar contexto do projeto com artefatos aprovados
    context = await _build_pgr_chat_context(projeto_id, db)

    # Se dados vieram do formulario, adicionar ao contexto
    logger.info(f"[PGR Chat] Dados recebidos: areas={message.areas_preocupacao}, prazo={message.prazo_desejado}")

    if message.areas_preocupacao:
        context.dados_coletados['areas_preocupacao'] = message.areas_preocupacao
    if message.prazo_desejado:
        context.dados_coletados['prazo_desejado'] = message.prazo_desejado
    if message.historico_problemas:
        context.dados_coletados['historico_problemas'] = message.historico_problemas
    if message.equipe_responsavel:
        context.dados_coletados['equipe_responsavel'] = message.equipe_responsavel

    # Converter historico para objetos Message
    history = [
        Message(role=msg["role"], content=msg["content"])
        for msg in message.history
    ]

    # Modelo a ser usado
    selected_model = message.model or settings.OPENROUTER_DEFAULT_MODEL

    # Instanciar agente
    agent = PGRChatAgent(model_override=selected_model)

    async def stream_chat():
        reasoning_buffer = ""
        content_buffer = ""
        try:
            async for chunk_data in agent.chat(message.content, history, context):
                # chunk_data agora eh um dict {"type": "...", "content": "..."}
                
                if chunk_data["type"] == "reasoning":
                    reasoning_buffer += chunk_data["content"]
                    yield f"data: {json.dumps({'type': 'reasoning', 'content': reasoning_buffer})}\n\n"
                
                elif chunk_data["type"] == "content":
                    chunk = chunk_data["content"]
                    content_buffer += chunk
                    yield f"data: {json.dumps({'type': 'chunk', 'content': content_buffer})}\n\n"
                    # Forcar flush do evento
                    await asyncio.sleep(0)

            # Verificar se a resposta contem marcador de geracao
            should_generate = '[GERAR_PGR]' in content_buffer

            # Fallback: detectar se o usuario autorizou a geracao na mensagem atual
            if not should_generate:
                user_msg = message.content.lower().strip()
                authorization_phrases = [
                    'gere', 'gerar', 'pode gerar', 'inicie', 'inicie a geracao',
                    'sim', 'ok', 'confirmo', 'autorizo', 'prossiga', 'vai', 'manda',
                    'pode iniciar', 'inicia', 'gera', 'faca', 'faz', 'execute',
                    'confirma', 'positivo', 'afirmativo', 'isso', 'isso mesmo'
                ]
                if any(phrase in user_msg for phrase in authorization_phrases):
                    # Verificar se ja temos dados suficientes para gerar
                    has_content = len(history) >= 2  # Pelo menos uma troca de mensagens
                    has_dfd = context.dfd is not None
                    if has_content and has_dfd:
                        should_generate = True
                        logger.info(f"[PGR Chat] Autorizacao detectada na mensagem do usuario: '{user_msg}'")

            if should_generate:
                # Remover o marcador da mensagem exibida
                buffer_limpo = content_buffer.replace('[GERAR_PGR]', '').strip()
                yield f"data: {json.dumps({'type': 'action', 'action': 'generate', 'message': 'Iniciando analise de riscos...'})}\n\n"

            yield f"data: {json.dumps({'type': 'done', 'full_response': content_buffer})}\n\n"

        except Exception as e:
            logger.error(f"Erro no chat PGR: {e}")
            yield f"data: {json.dumps({'type': 'error', 'error': str(e)})}\n\n"

    return StreamingResponse(
        stream_chat(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        }
    )


@router.post("/pgr/chat/{projeto_id}/gerar")
async def gerar_pgr_stream(
    projeto_id: int,
    body: PGRChatGenerateInput,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(auth_get_current_user),
):
    """
    Gera o PGR baseado no historico da conversa.

    Chamado quando a IA sinaliza que esta pronta para gerar.
    """
    logger.info(f"[PGR Gen] === INICIANDO GERACAO para projeto {projeto_id} ===")
    logger.info(f"[PGR Gen] Historico recebido: {len(body.history)} mensagens")

    # Buscar contexto do projeto com artefatos aprovados
    context = await _build_pgr_chat_context(projeto_id, db)
    logger.info(f"[PGR Gen] Contexto construido: projeto={context.projeto_titulo}, dfd={context.dfd is not None}, cotacao={context.pesquisa_precos is not None}")

    # Se dados vieram do formulario, adicionar ao contexto
    if body.areas_preocupacao:
        context.dados_coletados['areas_preocupacao'] = body.areas_preocupacao
    if body.prazo_desejado:
        context.dados_coletados['prazo_desejado'] = body.prazo_desejado
    if body.historico_problemas:
        context.dados_coletados['historico_problemas'] = body.historico_problemas
    if body.equipe_responsavel:
        context.dados_coletados['equipe_responsavel'] = body.equipe_responsavel
    if body.gestor:
        context.dados_coletados['responsavel_gestor'] = body.gestor
    if body.fiscal:
        context.dados_coletados['responsavel_fiscal'] = body.fiscal
    if body.data_limite:
        context.dados_coletados['data_pretendida'] = body.data_limite

    # Incluir base de conhecimento dos anexos
    if body.attachments:
        textos_anexos = [f"[{att.get('filename', 'arquivo')}]: {att['extracted_text']}" for att in body.attachments if att.get("extracted_text")]
        if textos_anexos:
            context.dados_coletados['base_conhecimento'] = "\n\n".join(textos_anexos)

    # Converter historico para objetos Message
    messages = [
        Message(role=msg["role"], content=msg["content"])
        for msg in body.history
    ]
    logger.info(f"[PGR Gen] Mensagens convertidas: {len(messages)}")

    # Modelo a ser usado
    selected_model = body.model or settings.OPENROUTER_DEFAULT_MODEL

    # Criar agente e gerar
    agent = PGRChatAgent(model_override=selected_model)
    logger.info(f"[PGR Gen] Agente criado, iniciando geracao...")

    async def stream_generate():
        reasoning_buffer = ""
        content_buffer = ""
        chunk_count = 0
        try:
            async for chunk_data in agent.gerar(context, messages):
                if chunk_data["type"] == "reasoning":
                    reasoning_buffer += chunk_data["content"]
                    yield f"data: {json.dumps({'type': 'reasoning', 'content': reasoning_buffer})}\n\n"
                
                elif chunk_data["type"] == "content":
                    chunk = chunk_data["content"]
                    chunk_count += 1
                    content_buffer += chunk
                    if chunk_count <= 5 or chunk_count % 20 == 0:
                        logger.debug(f"[PGR Gen] Chunk #{chunk_count}: {chunk[:50]}...")
                    yield f"data: {json.dumps({'type': 'chunk', 'content': content_buffer})}\n\n"

            logger.info(f"[PGR Gen] Geracao completa. Total chunks: {chunk_count}, buffer length: {len(content_buffer)}")

            # Tentar parsear JSON final
            try:
                cleaned = content_buffer.strip()
                if cleaned.startswith("```json"):
                    cleaned = cleaned[7:]
                if cleaned.startswith("```"):
                    cleaned = cleaned[3:]
                if cleaned.endswith("```"):
                    cleaned = cleaned[:-3]

                parsed = json.loads(cleaned.strip())
                logger.info(f"[PGR Gen] JSON parseado com sucesso. Campos: {list(parsed.keys())}")
                yield f"data: {json.dumps({'type': 'complete', 'success': True, 'data': parsed})}\n\n"
            except json.JSONDecodeError as je:
                logger.warning(f"[PGR Gen] Falha ao parsear JSON: {je}")
                logger.warning(f"[PGR Gen] Raw buffer: {content_buffer[:300]}...")
                yield f"data: {json.dumps({'type': 'complete', 'success': True, 'raw': content_buffer})}\n\n"

        except Exception as e:
            logger.error(f"[PGR Gen] === ERRO NA GERACAO ===: {e}", exc_info=True)
            yield f"data: {json.dumps({'type': 'error', 'error': str(e)})}\n\n"

    return StreamingResponse(
        stream_generate(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        }
    )


class PGRRegenerarCampoInput(BaseModel):
    """Input para regenerar um campo especifico do PGR ou um risco por categoria."""
    campo: str  # Campo do PGR ou categoria de risco (Planejamento, Selecao_Fornecedor, Gestao_Contratual)
    history: List[Dict[str, Any]] = []
    prompt_adicional: Optional[str] = None
    valor_atual: Optional[str] = None
    tipo: str = "campo"  # "campo" ou "categoria"
    model: Optional[str] = None
    active_skills: Optional[List[int]] = []
    attachments: Optional[List[Dict[str, Any]]] = None


@router.post("/pgr/chat/{projeto_id}/regenerar-campo")
async def regenerar_campo_pgr(
    projeto_id: int,
    body: PGRRegenerarCampoInput,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(auth_get_current_user),
):
    """
    Regenera um campo especifico do PGR ou riscos de uma categoria.

    Args:
        projeto_id: ID do projeto
        body: Campo/categoria a regenerar, historico e instrucoes adicionais

    Returns:
        JSON com o novo valor do campo ou riscos regenerados
    """
    logger.info(f"[PGR Regen] Regenerando {body.tipo} '{body.campo}' para projeto {projeto_id}")
    logger.info(f"[PGR Regen] Prompt adicional: {body.prompt_adicional}")

    # Labels dos campos para mensagens amigaveis
    campos_labels = {
        'identificacao_objeto': 'Identificacao do Objeto',
        'metodologia_adotada': 'Metodologia Adotada',
        'resumo_analise_planejamento': 'Resumo - Fase Planejamento',
        'resumo_analise_selecao': 'Resumo - Fase Selecao',
        'resumo_analise_gestao': 'Resumo - Fase Gestao',
        'Planejamento': 'Riscos de Planejamento',
        'Selecao_Fornecedor': 'Riscos de Selecao de Fornecedor',
        'Gestao_Contratual': 'Riscos de Gestao Contratual',
    }

    campo_label = campos_labels.get(body.campo, body.campo)

    # Buscar contexto do projeto
    context = await _build_pgr_chat_context(projeto_id, db)

    # Adicionar anexos especificos da regeneração (se houver) ao contexto
    if body.attachments:
        textos_anexos = [f"[{att.get('filename', 'arquivo')}]: {att['extracted_text']}" for att in body.attachments if att.get("extracted_text")]
        if textos_anexos:
            base_conhecimento_field = "\n\nANEXOS ADICIONAIS PARA ESTE CAMPO:\n" + "\n\n".join(textos_anexos)
            if 'base_conhecimento' in context.dados_coletados:
                context.dados_coletados['base_conhecimento'] += "\n" + base_conhecimento_field
            else:
                context.dados_coletados['base_conhecimento'] = base_conhecimento_field

    # Construir prompt para regeneracao
    conversa_resumo = ""
    if body.history:
        partes = []
        for msg in body.history[-5:]:
            prefixo = "Usuario:" if msg.get("role") == "user" else "IA:"
            partes.append(f"{prefixo} {msg.get('content', '')[:200]}")
        conversa_resumo = "\n".join(partes)

    # Prompt diferente para campo vs categoria de risco
    if body.tipo == "categoria":
        system_prompt = f"""Voce e um especialista em gerenciamento de riscos do TRE-GO.

Sua tarefa e regenerar os RISCOS da categoria "{campo_label}" de um PGR.

REGRAS:
1. Retorne um array JSON com 2-4 riscos para esta fase
2. Use o mesmo schema de ItemRisco
3. Se o usuario deu instrucoes especificas, siga-as
4. Considere o contexto do DFD e cotacoes aprovadas"""

        user_prompt = f"""PROJETO: {context.projeto_titulo}

FASE/CATEGORIA A REGENERAR: {campo_label}

RISCOS ATUAIS:
{body.valor_atual or 'Nenhum'}

CONTEXTO DA CONVERSA:
{conversa_resumo or 'Nao disponivel'}

INSTRUCOES DO USUARIO:
{body.prompt_adicional or 'Nenhuma instrucao especifica - gere riscos relevantes para esta fase.'}

Gere os novos riscos para a fase "{body.campo}". Retorne APENAS o array JSON."""
    else:
        system_prompt = f"""Voce e um especialista em gerenciamento de riscos do TRE-GO.

Sua tarefa e regenerar APENAS o campo "{campo_label}" de um PGR.

REGRAS:
1. Retorne APENAS o novo texto do campo, sem JSON, sem aspas extras, sem markdown
2. Use linguagem formal e objetiva
3. Foque na fundamentacao legal (Lei 14.133/2021)
4. Se o usuario deu instrucoes especificas, siga-as"""

        user_prompt = f"""PROJETO: {context.projeto_titulo}

CAMPO A REGENERAR: {campo_label}

VALOR ATUAL DO CAMPO:
{body.valor_atual or 'Nao preenchido'}

CONTEXTO DA CONVERSA:
{conversa_resumo or 'Nao disponivel'}

INSTRUCOES DO USUARIO:
{body.prompt_adicional or 'Nenhuma instrucao especifica - melhore o texto mantendo a essencia.'}

Gere o novo texto para o campo "{campo_label}". Retorne APENAS o texto, sem formatacao extra."""

    try:
        from openai import AsyncOpenAI
        client = AsyncOpenAI(
            api_key=settings.OPENROUTER_API_KEY,
            base_url=settings.OPENROUTER_BASE_URL,
            timeout=settings.OPENROUTER_TIMEOUT,
        )

        # Modelo a ser usado
        selected_model = body.model or settings.OPENROUTER_DEFAULT_MODEL

        # Carregar skills ativas
        skills_context = ""
        if body.active_skills:
            skills_objs = await _load_skills_ativas_by_ids(body.active_skills, current_user.id, db)
            if skills_objs:
                skills_context = "\nDIRETRIZES DE HABILIDADES ATIVAS:\n"
                for skill in skills_objs:
                    skills_context += f"- {skill.nome}: {skill.instrucao}\n"

        # Injetar skills no system prompt
        if skills_context:
            system_prompt += f"\n\n{skills_context}"

        response = await client.chat.completions.create(
            model=selected_model,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            temperature=0.5,
            max_tokens=4096,
        )

        novo_valor = response.choices[0].message.content.strip()

        # Limpar possiveis aspas extras
        if novo_valor.startswith('"') and novo_valor.endswith('"'):
            novo_valor = novo_valor[1:-1]

        logger.info(f"[PGR Regen] {body.tipo} '{body.campo}' regenerado com sucesso.")

        return {
            "success": True,
            "campo": body.campo,
            "tipo": body.tipo,
            "value": novo_valor,
            "label": campo_label
        }

    except Exception as e:
        logger.error(f"[PGR Regen] Erro ao regenerar: {e}", exc_info=True)
        return {
            "success": False,
            "error": str(e),
            "campo": body.campo
        }


async def _build_pgr_chat_context(projeto_id: int, db: AsyncSession) -> ChatContext:
    """Constroi o ChatContext para o agente conversacional do PGR.

    Inclui DFD e Cotacoes APROVADOS como contexto.
    """

    # Buscar projeto
    result = await db.execute(
        select(Projeto).filter(Projeto.id == projeto_id)
    )
    projeto = result.scalars().first()

    if not projeto:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Projeto {projeto_id} nao encontrado"
        )

    # Buscar itens PAC
    itens_pac = await pac_service.get_itens_by_projeto(projeto, db)

    # Criar contexto
    skills = await _load_skills_ativas(projeto_id, db, "riscos", projeto.usuario_id)
    context = ChatContext(
        projeto_id=projeto.id,
        projeto_titulo=projeto.titulo,
        setor_usuario="Unidade Requisitante",
        itens_pac=itens_pac or [],
        skills=skills,
    )

    # Buscar DFD APROVADO
    dfd_result = await db.execute(
        select(DFD)
        .filter(DFD.projeto_id == projeto_id, DFD.status.in_(["aprovado", "publicado"]))
        .order_by(DFD.data_criacao.desc())
        .limit(1)
    )
    dfd = dfd_result.scalars().first()
    if dfd:
        context.dfd = {
            "id": dfd.id,
            "descricao_objeto": dfd.descricao_objeto,
            "descricao_objeto_padronizada": dfd.descricao_objeto,
            "justificativa": dfd.justificativa,
            "justificativa_tecnica": dfd.justificativa,
            "grau_prioridade": dfd.grau_prioridade,
            "versao": dfd.versao,
        }

    # Buscar Cotacoes APROVADAS
    pp_result = await db.execute(
        select(PesquisaPrecos)
        .filter(PesquisaPrecos.projeto_id == projeto_id, PesquisaPrecos.status.in_(["aprovado", "publicado"]))
        .order_by(PesquisaPrecos.data_criacao.desc())
        .limit(1)
    )
    pp = pp_result.scalars().first()
    if pp:
        # Calcular CV se disponivel
        cv = 0.0
        qtd_fornecedores = 0
        if pp.dados_cotacao:
            estatisticas = pp.dados_cotacao.get('estatisticas', {})
            cv = estatisticas.get('coeficiente_variacao', 0)
            qtd_fornecedores = estatisticas.get('quantidade_fornecedores', len(pp.itens_cotados or []))

        context.pesquisa_precos = {
            "id": pp.id,
            "valor_total_cotacao": pp.valor_total_cotacao or 0,
            "valor_total": pp.valor_total_cotacao or 0,
            "quantidade_fornecedores": qtd_fornecedores,
            "coeficiente_variacao": cv,
            "versao": pp.versao,
        }

    return context


# ========== ENDPOINTS DE CHAT (ETP) ==========

class ETPChatMessageInput(BaseModel):
    """Mensagem enviada pelo usuario no chat ETP."""
    content: str
    history: List[dict] = []
    requisitos_adicionais: Optional[str] = None
    certificacoes: Optional[str] = None
    model: Optional[str] = None
    active_skills: Optional[List[int]] = []


class ETPChatGenerateInput(BaseModel):
    """Dados para geracao do ETP a partir do chat."""
    history: List[dict] = []
    requisitos_adicionais: Optional[str] = None
    certificacoes: Optional[str] = None
    gestor: Optional[str] = None
    fiscal: Optional[str] = None
    data_limite: Optional[str] = None
    attachments: Optional[List[Dict[str, Any]]] = None
    model: Optional[str] = None
    active_skills: Optional[List[int]] = []


class ETPChatInitResponse(BaseModel):
    """Resposta inicial do chat ETP."""
    mensagem_inicial: str
    projeto_id: int
    projeto_titulo: str
    dfd_aprovado: bool
    cotacao_aprovada: bool
    pgr_aprovado: bool
    valor_estimado: float


@router.get("/etp/chat/init/{projeto_id}")
async def iniciar_chat_etp(
    projeto_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(auth_get_current_user),
) -> ETPChatInitResponse:
    """
    Inicializa o chat para geracao de ETP.

    Retorna a mensagem inicial da IA e dados dos artefatos aprovados.
    """
    # Buscar contexto do projeto com artefatos aprovados
    context = await _build_etp_chat_context(projeto_id, db)

    # Criar agente e obter mensagem inicial
    agent = ETPChatAgent()
    mensagem_inicial = agent.get_mensagem_inicial(context)

    # Calcular valor estimado
    valor_estimado = 0.0
    if context.pesquisa_precos:
        valor_estimado = context.pesquisa_precos.get('valor_total_cotacao', 0)

    return ETPChatInitResponse(
        mensagem_inicial=mensagem_inicial,
        projeto_id=context.projeto_id,
        projeto_titulo=context.projeto_titulo,
        dfd_aprovado=context.dfd is not None,
        cotacao_aprovada=context.pesquisa_precos is not None,
        pgr_aprovado=context.pgr is not None,
        valor_estimado=valor_estimado,
    )


@router.post("/etp/chat/{projeto_id}")
async def chat_etp(
    projeto_id: int,
    message: ETPChatMessageInput,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(auth_get_current_user),
):
    """
    Processa uma mensagem do chat ETP e retorna resposta em streaming.

    Quando a IA detectar que esta pronta para gerar, retorna:
    {"action": "generate", "message": "..."}
    """
    # Buscar contexto do projeto com artefatos aprovados
    context = await _build_etp_chat_context(projeto_id, db)

    # Se dados vieram do formulario, adicionar ao contexto
    logger.info(f"[ETP Chat] Dados recebidos: requisitos={message.requisitos_adicionais}, certificacoes={message.certificacoes}")

    if message.requisitos_adicionais:
        context.dados_coletados['requisitos_adicionais'] = message.requisitos_adicionais
    if message.certificacoes:
        context.dados_coletados['certificacoes'] = message.certificacoes

    # Converter historico para objetos Message
    history = [
        Message(role=msg["role"], content=msg["content"])
        for msg in message.history
    ]

    # Modelo a ser usado
    selected_model = message.model or settings.OPENROUTER_DEFAULT_MODEL
    logger.info(f"[ETP Chat] Modelo de IA selecionado: {selected_model}")

    # Carregar skills ativas se solicitadas
    active_skills_instr = ""
    if message.active_skills:
        skills_objs = await _load_skills_ativas_by_ids(message.active_skills, current_user.id, db)
        if skills_objs:
            active_skills_instr = "\nDIRETRIZES DE HABILIDADES SELECIONADAS:\n"
            for skill in skills_objs:
                active_skills_instr += f"- {skill.nome}: {skill.instrucao}\n"
            logger.info(f"[ETP Chat] {len(skills_objs)} skill(s) ativada(s).")

    # Instanciar agente com o modelo selecionado e skills ativas
    agent = ETPChatAgent(model_override=selected_model, active_skills_instr=active_skills_instr)

    async def stream_chat():
        reasoning_buffer = ""
        content_buffer = ""
        try:
            async for chunk_data in agent.chat(message.content, history, context):
                # chunk_data agora eh um dict {"type": "...", "content": "..."}
                
                if chunk_data["type"] == "reasoning":
                    reasoning_buffer += chunk_data["content"]
                    yield f"data: {json.dumps({'type': 'reasoning', 'content': reasoning_buffer})}\n\n"
                
                elif chunk_data["type"] == "content":
                    chunk = chunk_data["content"]
                    content_buffer += chunk
                    yield f"data: {json.dumps({'type': 'chunk', 'content': content_buffer})}\n\n"
                    # Forcar flush do evento
                    await asyncio.sleep(0)

            # Verificar se a resposta contem marcador de geracao
            should_generate = '[GERAR_ETP]' in content_buffer

            # Fallback: detectar se o usuario autorizou a geracao na mensagem atual
            if not should_generate:
                user_msg = message.content.lower().strip()
                authorization_phrases = [
                    'gere', 'gerar', 'pode gerar', 'inicie', 'inicie a geracao',
                    'sim', 'ok', 'confirmo', 'autorizo', 'prossiga', 'vai', 'manda',
                    'pode iniciar', 'inicia', 'gera', 'faca', 'faz', 'execute',
                    'confirma', 'positivo', 'afirmativo', 'isso', 'isso mesmo'
                ]
                if any(phrase in user_msg for phrase in authorization_phrases):
                    # Verificar se ja temos dados suficientes para gerar
                    has_content = len(history) >= 1  # Pelo menos uma mensagem
                    has_dfd = context.dfd is not None
                    if has_content and has_dfd:
                        should_generate = True
                        logger.info(f"[ETP Chat] Autorizacao detectada na mensagem do usuario: '{user_msg}'")

            if should_generate:
                # Remover o marcador da mensagem exibida
                buffer_limpo = content_buffer.replace('[GERAR_ETP]', '').strip()
                yield f"data: {json.dumps({'type': 'action', 'action': 'generate', 'message': 'Iniciando geracao do ETP...'})}\n\n"

            yield f"data: {json.dumps({'type': 'done', 'full_response': content_buffer})}\n\n"

        except Exception as e:
            logger.error(f"Erro no chat ETP: {e}")
            yield f"data: {json.dumps({'type': 'error', 'error': str(e)})}\n\n"

    return StreamingResponse(
        stream_chat(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        }
    )


@router.post("/etp/chat/{projeto_id}/gerar")
async def gerar_etp_stream(
    projeto_id: int,
    body: ETPChatGenerateInput,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(auth_get_current_user),
):
    """
    Gera o ETP baseado no historico da conversa.

    Chamado quando a IA sinaliza que esta pronta para gerar.
    """
    logger.info(f"[ETP Gen] === INICIANDO GERACAO para projeto {projeto_id} ===")
    logger.info(f"[ETP Gen] Historico recebido: {len(body.history)} mensagens")

    # Buscar contexto do projeto com artefatos aprovados
    context = await _build_etp_chat_context(projeto_id, db)
    logger.info(f"[ETP Gen] Contexto construido: projeto={context.projeto_titulo}, dfd={context.dfd is not None}, cotacao={context.pesquisa_precos is not None}, pgr={context.pgr is not None}")

    # Se dados vieram do formulario, adicionar ao contexto
    if body.requisitos_adicionais:
        context.dados_coletados['requisitos_adicionais'] = body.requisitos_adicionais
    if body.certificacoes:
        context.dados_coletados['certificacoes'] = body.certificacoes
    if body.gestor:
        context.dados_coletados['responsavel_gestor'] = body.gestor
    if body.fiscal:
        context.dados_coletados['responsavel_fiscal'] = body.fiscal
    if body.data_limite:
        context.dados_coletados['data_pretendida'] = body.data_limite

    # Incluir base de conhecimento dos anexos
    if body.attachments:
        textos_anexos = [f"[{att.get('filename', 'arquivo')}]: {att['extracted_text']}" for att in body.attachments if att.get("extracted_text")]
        if textos_anexos:
            context.dados_coletados['base_conhecimento'] = "\n\n".join(textos_anexos)

    # Converter historico para objetos Message
    messages = [
        Message(role=msg["role"], content=msg["content"])
        for msg in body.history
    ]
    logger.info(f"[ETP Gen] Mensagens convertidas: {len(messages)}")

    # Modelo a ser usado
    selected_model = body.model or settings.OPENROUTER_DEFAULT_MODEL
    logger.info(f"[ETP Gen] Iniciando geracao streaming com modelo: {selected_model}")

    # Carregar skills ativas
    active_skills_instr = ""
    if body.active_skills:
        skills_objs = await _load_skills_ativas_by_ids(body.active_skills, current_user.id, db)
        if skills_objs:
            active_skills_instr = "\nDIRETRIZES DE HABILIDADES SELECIONADAS:\n"
            for skill in skills_objs:
                active_skills_instr += f"- {skill.nome}: {skill.instrucao}\n"
            logger.info(f"[ETP Gen] {len(skills_objs)} skill(s) ativada(s).")

    # Criar agente e gerar
    agent = ETPChatAgent(model_override=selected_model, active_skills_instr=active_skills_instr)
    logger.info(f"[ETP Gen] Agente criado, iniciando geracao...")

    async def stream_generate():
        reasoning_buffer = ""
        content_buffer = ""
        chunk_count = 0
        try:
            async for chunk_data in agent.gerar(context, messages):
                if chunk_data["type"] == "reasoning":
                    reasoning_buffer += chunk_data["content"]
                    yield f"data: {json.dumps({'type': 'reasoning', 'content': reasoning_buffer})}\n\n"
                
                elif chunk_data["type"] == "content":
                    chunk = chunk_data["content"]
                    chunk_count += 1
                    content_buffer += chunk
                    if chunk_count <= 5 or chunk_count % 10 == 0:
                        logger.debug(f"[ETP Gen] Chunk #{chunk_count}: {chunk[:100]}...")
                    yield f"data: {json.dumps({'type': 'chunk', 'content': content_buffer})}\n\n"

            logger.info(f"[ETP Gen] Geracao completa. Total chunks: {chunk_count}, buffer length: {len(content_buffer)}")

            # Tentar parsear JSON final
            try:
                cleaned = content_buffer.strip()
                if cleaned.startswith("```json"):
                    cleaned = cleaned[7:]
                if cleaned.startswith("```"):
                    cleaned = cleaned[3:]
                if cleaned.endswith("```"):
                    cleaned = cleaned[:-3]

                parsed = json.loads(cleaned.strip())
                logger.info(f"[ETP Gen] JSON parseado com sucesso. Campos: {list(parsed.keys())}")
                yield f"data: {json.dumps({'type': 'complete', 'success': True, 'data': parsed})}\n\n"
            except json.JSONDecodeError as je:
                logger.warning(f"[ETP Gen] Falha ao parsear JSON: {je}")
                logger.warning(f"[ETP Gen] Raw buffer: {content_buffer[:300]}...")
                yield f"data: {json.dumps({'type': 'complete', 'success': True, 'raw': content_buffer})}\n\n"

        except Exception as e:
            logger.error(f"[ETP Gen] === ERRO NA GERACAO ===: {e}", exc_info=True)
            yield f"data: {json.dumps({'type': 'error', 'error': str(e)})}\n\n"

    return StreamingResponse(
        stream_generate(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        }
    )


class ETPRegenerarCampoInput(BaseModel):
    """Input para regenerar um campo especifico do ETP."""
    campo: str
    history: List[Dict[str, Any]] = []
    prompt_adicional: Optional[str] = None
    valor_atual: Optional[str] = None
    model: Optional[str] = None
    active_skills: Optional[List[int]] = []
    attachments: Optional[List[Dict[str, Any]]] = None


@router.post("/etp/chat/{projeto_id}/regenerar-campo")
async def regenerar_campo_etp(
    projeto_id: int,
    body: ETPRegenerarCampoInput,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(auth_get_current_user),
):
    """
    Regenera um campo especifico do ETP usando IA.

    Args:
        projeto_id: ID do projeto
        body: Campo a regenerar, historico e instrucoes adicionais

    Returns:
        JSON com o novo valor do campo
    """
    logger.info(f"[ETP Regen] Regenerando campo '{body.campo}' para projeto {projeto_id}")
    
    # Modelo a ser usado
    selected_model = body.model or settings.OPENROUTER_DEFAULT_MODEL
    logger.info(f"[ETP Regen] Usando modelo: {selected_model}")

    # Labels dos campos para mensagens amigaveis
    campos_labels = {
        'descricao_necessidade': 'Descricao da Necessidade (ETP-01)',
        'area_requisitante': 'Area Requisitante (ETP-02)',
        'requisitos_contratacao': 'Requisitos da Contratacao (ETP-03)',
        'estimativa_quantidades': 'Estimativa de Quantidades (ETP-04)',
        'levantamento_mercado': 'Levantamento de Mercado (ETP-05)',
        'estimativa_valor': 'Estimativa do Valor (ETP-06)',
        'descricao_solucao': 'Descricao da Solucao (ETP-07)',
        'justificativa_parcelamento': 'Parcelamento do Objeto (ETP-08)',
        'contratacoes_correlatas': 'Contratacoes Correlatas (ETP-09)',
        'alinhamento_pca': 'Alinhamento ao PCA (ETP-10)',
        'resultados_pretendidos': 'Resultados Pretendidos (ETP-11)',
        'providencias_previas': 'Providencias Previas (ETP-12)',
        'impactos_ambientais': 'Impactos Ambientais (ETP-13)',
        'analise_riscos': 'Analise de Riscos (ETP-14)',
        'viabilidade_contratacao': 'Viabilidade da Contratacao (ETP-15)',
    }

    campo_label = campos_labels.get(body.campo, body.campo)

    # Buscar contexto do projeto
    context = await _build_etp_chat_context(projeto_id, db)

    # Adicionar anexos especificos da regeneração (se houver) ao contexto
    if body.attachments:
        textos_anexos = [f"[{att.get('filename', 'arquivo')}]: {att['extracted_text']}" for att in body.attachments if att.get("extracted_text")]
        if textos_anexos:
            base_conhecimento_field = "\n\nANEXOS ADICIONAIS PARA ESTE CAMPO:\n" + "\n\n".join(textos_anexos)
            if 'base_conhecimento' in context.dados_coletados:
                context.dados_coletados['base_conhecimento'] += "\n" + base_conhecimento_field
            else:
                context.dados_coletados['base_conhecimento'] = base_conhecimento_field

    # Carregar skills ativas se solicitadas
    skills_context = ""
    if body.active_skills:
        skills_objs = await _load_skills_ativas_by_ids(body.active_skills, current_user.id, db)
        if skills_objs:
            skills_context = "\nDIRETRIZES DE HABILIDADES ATIVAS:\n"
            for skill in skills_objs:
                skills_context += f"- {skill.nome}: {skill.instrucao}\n"

    # Construir prompt para regeneracao do campo especifico
    conversa_resumo = ""
    if body.history:
        partes = []
        for msg in body.history[-5:]:  # Ultimas 5 mensagens
            prefixo = "Usuario:" if msg.get("role") == "user" else "IA:"
            partes.append(f"{prefixo} {msg.get('content', '')[:200]}")
        conversa_resumo = "\n".join(partes)

    system_prompt = f"""Voce e um especialista em Estudos Tecnicos Preliminares do TRE-GO.

Sua tarefa e regenerar APENAS o campo "{campo_label}" de um ETP (Estudo Tecnico Preliminar).

{skills_context}

REGRAS:
1. Retorne APENAS o novo texto do campo, sem JSON, sem aspas extras, sem markdown
2. Use linguagem formal e objetiva
3. Foque na fundamentacao legal (Lei 14.133/2021, art. 18, 1)
4. Se o usuario deu instrucoes especificas, siga-as
5. O texto deve ser conciso mas completo"""

    # Incluir contexto do DFD se disponivel
    dfd_context = ""
    if context.dfd:
        dfd_context = f"""
CONTEXTO DO DFD APROVADO:
- Objeto: {context.dfd.get('descricao_objeto', 'N/A')}
- Justificativa: {context.dfd.get('justificativa', 'N/A')[:300]}
"""

    user_prompt = f"""PROJETO: {context.projeto_titulo}
{dfd_context}
CAMPO A REGENERAR: {campo_label}

VALOR ATUAL DO CAMPO:
{body.valor_atual or 'Nao preenchido'}

CONTEXTO DA CONVERSA:
{conversa_resumo or 'Nao disponivel'}

INSTRUCOES DO USUARIO:
{body.prompt_adicional or 'Nenhuma instrucao especifica - melhore o texto mantendo a essencia.'}

Gere o novo texto para o campo "{campo_label}". Retorne APENAS o texto, sem formatacao extra."""

    try:
        from openai import AsyncOpenAI
        client = AsyncOpenAI(
            api_key=settings.OPENROUTER_API_KEY,
            base_url=settings.OPENROUTER_BASE_URL,
            timeout=settings.OPENROUTER_TIMEOUT,
        )

        response = await client.chat.completions.create(
            model=selected_model,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            temperature=0.6,
            max_tokens=2048,
        )

        novo_valor = response.choices[0].message.content.strip()

        # Limpar possiveis aspas extras
        if novo_valor.startswith('"') and novo_valor.endswith('"'):
            novo_valor = novo_valor[1:-1]

        logger.info(f"[ETP Regen] Campo '{body.campo}' regenerado com sucesso. Novo valor: {novo_valor[:100]}...")

        return {
            "success": True,
            "campo": body.campo,
            "value": novo_valor,
            "label": campo_label
        }

    except Exception as e:
        logger.error(f"[ETP Regen] Erro ao regenerar campo: {e}", exc_info=True)
        return {
            "success": False,
            "error": str(e),
            "campo": body.campo
        }


async def _build_etp_chat_context(projeto_id: int, db: AsyncSession) -> ChatContext:
    """Constroi o ChatContext para o agente ETP conversacional.

    Inclui DFD, PGR e Cotacoes APROVADOS como contexto.
    """

    # Buscar projeto
    result = await db.execute(
        select(Projeto).filter(Projeto.id == projeto_id)
    )
    projeto = result.scalars().first()

    if not projeto:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Projeto {projeto_id} nao encontrado"
        )

    # Buscar itens PAC
    itens_pac = await pac_service.get_itens_by_projeto(projeto, db)

    # Criar contexto
    skills = await _load_skills_ativas(projeto_id, db, "etp", projeto.usuario_id)
    context = ChatContext(
        projeto_id=projeto.id,
        projeto_titulo=projeto.titulo,
        setor_usuario="Unidade Requisitante",
        itens_pac=itens_pac or [],
        skills=skills,
    )

    # Buscar DFD APROVADO ou PUBLICADO (obrigatorio para ETP)
    dfd_result = await db.execute(
        select(DFD)
        .filter(DFD.projeto_id == projeto_id, DFD.status.in_(["aprovado", "publicado"]))
        .order_by(DFD.data_criacao.desc())
        .limit(1)
    )
    dfd = dfd_result.scalars().first()
    if dfd:
        context.dfd = {
            "id": dfd.id,
            "descricao_objeto": dfd.descricao_objeto,
            "justificativa": dfd.justificativa,
            "alinhamento_estrategico": dfd.alinhamento_estrategico,
            "grau_prioridade": dfd.grau_prioridade,
            "versao": dfd.versao,
        }

    # Buscar Cotacoes APROVADAS
    pp_result = await db.execute(
        select(PesquisaPrecos)
        .filter(PesquisaPrecos.projeto_id == projeto_id, PesquisaPrecos.status.in_(["aprovado", "publicado"]))
        .order_by(PesquisaPrecos.data_criacao.desc())
        .limit(1)
    )
    pp = pp_result.scalars().first()
    if pp:
        context.pesquisa_precos = {
            "id": pp.id,
            "valor_total_cotacao": pp.valor_total_cotacao or 0,
            "quantidade_fornecedores": len(pp.itens_cotados or []),
            "versao": pp.versao,
        }

    # Buscar PGR APROVADO
    pgr_result = await db.execute(
        select(Riscos)
        .filter(Riscos.projeto_id == projeto_id, Riscos.status.in_(["aprovado", "publicado"]))
        .order_by(Riscos.data_criacao.desc())
        .limit(1)
    )
    pgr = pgr_result.scalars().first()
    if pgr:
        context.pgr = {
            "id": pgr.id,
            "identificacao_objeto": pgr.identificacao_objeto,
            "resumo_analise_planejamento": pgr.resumo_analise_planejamento,
            "resumo_analise_selecao": pgr.resumo_analise_selecao,
            "resumo_analise_gestao": pgr.resumo_analise_gestao,
            "versao": pgr.versao,
        }

    return context


# ========== ENDPOINTS DE CHAT (TR) ==========

class TRChatMessageInput(BaseModel):
    """Mensagem enviada pelo usuario no chat TR."""
    content: str
    history: List[dict] = []
    modelo_execucao: Optional[str] = None
    prazo_entrega: Optional[str] = None
    model: Optional[str] = None
    active_skills: Optional[List[int]] = []


class TRChatGenerateInput(BaseModel):
    """Dados para geracao do TR a partir do chat."""
    history: List[dict] = []
    modelo_execucao: Optional[str] = None
    prazo_entrega: Optional[str] = None
    gestor: Optional[str] = None
    fiscal: Optional[str] = None
    data_limite: Optional[str] = None
    attachments: Optional[List[Dict[str, Any]]] = None
    model: Optional[str] = None
    active_skills: Optional[List[int]] = []


class TRChatInitResponse(BaseModel):
    """Resposta inicial do chat TR."""
    mensagem_inicial: str
    projeto_id: int
    projeto_titulo: str
    etp_aprovado: bool
    dfd_aprovado: bool
    cotacao_aprovada: bool
    valor_estimado: float


@router.get("/tr/chat/init/{projeto_id}")
async def iniciar_chat_tr(
    projeto_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(auth_get_current_user),
) -> TRChatInitResponse:
    """
    Inicializa o chat para geracao de TR.

    Retorna a mensagem inicial da IA e dados do projeto/artefatos aprovados.
    """
    # Buscar contexto do projeto com artefatos aprovados
    context = await _build_tr_chat_context(projeto_id, db)

    # Criar agente e obter mensagem inicial
    agent = TRChatAgent()
    mensagem_inicial = agent.get_mensagem_inicial(context)

    # Calcular valor estimado
    valor_estimado = 0.0
    if context.pesquisa_precos:
        valor_estimado = context.pesquisa_precos.get('valor_total_cotacao', 0)

    return TRChatInitResponse(
        mensagem_inicial=mensagem_inicial,
        projeto_id=context.projeto_id,
        projeto_titulo=context.projeto_titulo,
        etp_aprovado=context.etp is not None,
        dfd_aprovado=context.dfd is not None,
        cotacao_aprovada=context.pesquisa_precos is not None,
        valor_estimado=valor_estimado,
    )


@router.post("/tr/chat/{projeto_id}")
async def chat_tr(
    projeto_id: int,
    message: TRChatMessageInput,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(auth_get_current_user),
):
    """
    Processa uma mensagem do chat TR e retorna resposta em streaming.

    Quando a IA detectar que esta pronta para gerar, retorna:
    {"action": "generate", "message": "..."}
    """
    # Buscar contexto do projeto com artefatos aprovados
    context = await _build_tr_chat_context(projeto_id, db)

    # Se dados vieram do formulario, adicionar ao contexto
    logger.info(f"[TR Chat] Dados recebidos: modelo={message.modelo_execucao}, prazo={message.prazo_entrega}")

    if message.modelo_execucao:
        context.dados_coletados['modelo_execucao'] = message.modelo_execucao
    if message.prazo_entrega:
        context.dados_coletados['prazo_entrega'] = message.prazo_entrega

    # Converter historico para objetos Message
    history = [
        Message(role=msg["role"], content=msg["content"])
        for msg in message.history
    ]

    # Modelo a ser usado
    selected_model = message.model or settings.OPENROUTER_DEFAULT_MODEL

    # Criar agente e processar mensagem
    agent = TRChatAgent(model_override=selected_model)

    async def stream_chat():
        reasoning_buffer = ""
        content_buffer = ""
        try:
            async for chunk_data in agent.chat(message.content, history, context):
                # chunk_data agora eh um dict {"type": "...", "content": "..."}
                
                if chunk_data["type"] == "reasoning":
                    reasoning_buffer += chunk_data["content"]
                    yield f"data: {json.dumps({'type': 'reasoning', 'content': reasoning_buffer})}\n\n"
                
                elif chunk_data["type"] == "content":
                    chunk = chunk_data["content"]
                    content_buffer += chunk
                    yield f"data: {json.dumps({'type': 'chunk', 'content': content_buffer})}\n\n"
                    # Forcar flush do evento
                    await asyncio.sleep(0)

            # Verificar se a resposta contem marcador de geracao
            should_generate = '[GERAR_TR]' in content_buffer

            # Fallback: detectar se o usuario autorizou a geracao na mensagem atual
            if not should_generate:
                user_msg = message.content.lower().strip()
                authorization_phrases = [
                    'gere', 'gerar', 'pode gerar', 'inicie', 'inicie a geracao',
                    'sim', 'ok', 'confirmo', 'autorizo', 'prossiga', 'vai', 'manda',
                    'pode iniciar', 'inicia', 'gera', 'faca', 'faz', 'execute',
                    'confirma', 'positivo', 'afirmativo', 'isso', 'isso mesmo'
                ]
                if any(phrase in user_msg for phrase in authorization_phrases):
                    # Verificar se ja temos dados suficientes para gerar
                    has_content = len(history) >= 1  # Pelo menos uma mensagem
                    has_etp = context.etp is not None
                    if has_content and has_etp:
                        should_generate = True
                        logger.info(f"[TR Chat] Autorizacao detectada na mensagem do usuario: '{user_msg}'")

            if should_generate:
                # Remover o marcador da mensagem exibida
                buffer_limpo = content_buffer.replace('[GERAR_TR]', '').strip()
                yield f"data: {json.dumps({'type': 'action', 'action': 'generate', 'message': 'Iniciando geracao do TR...'})}\n\n"

            yield f"data: {json.dumps({'type': 'done', 'full_response': content_buffer})}\n\n"

        except Exception as e:
            logger.error(f"Erro no chat TR: {e}")
            yield f"data: {json.dumps({'type': 'error', 'error': str(e)})}\n\n"

    return StreamingResponse(
        stream_chat(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        }
    )


@router.post("/tr/chat/{projeto_id}/gerar")
async def gerar_tr_stream(
    projeto_id: int,
    body: TRChatGenerateInput,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(auth_get_current_user),
):
    """
    Gera o TR baseado no historico da conversa.

    Chamado quando a IA sinaliza que esta pronta para gerar.
    """
    logger.info(f"[TR Gen] === INICIANDO GERACAO para projeto {projeto_id} ===")
    logger.info(f"[TR Gen] Historico recebido: {len(body.history)} mensagens")

    # Buscar contexto do projeto com artefatos aprovados
    context = await _build_tr_chat_context(projeto_id, db)
    logger.info(f"[TR Gen] Contexto construido: projeto={context.projeto_titulo}, etp={context.etp is not None}, dfd={context.dfd is not None}, cotacao={context.pesquisa_precos is not None}")

    # Se dados vieram do formulario, adicionar ao contexto
    if body.modelo_execucao:
        context.dados_coletados['modelo_execucao'] = body.modelo_execucao
    if body.prazo_entrega:
        context.dados_coletados['prazo_entrega'] = body.prazo_entrega
    if body.gestor:
        context.dados_coletados['responsavel_gestor'] = body.gestor
    if body.fiscal:
        context.dados_coletados['responsavel_fiscal'] = body.fiscal
    if body.data_limite:
        context.dados_coletados['data_pretendida'] = body.data_limite

    # Incluir base de conhecimento dos anexos
    if body.attachments:
        textos_anexos = [f"[{att.get('filename', 'arquivo')}]: {att['extracted_text']}" for att in body.attachments if att.get("extracted_text")]
        if textos_anexos:
            context.dados_coletados['base_conhecimento'] = "\n\n".join(textos_anexos)

    # Converter historico para objetos Message
    messages = [
        Message(role=msg["role"], content=msg["content"])
        for msg in body.history
    ]
    logger.info(f"[TR Gen] Mensagens convertidas: {len(messages)}")

    # Modelo a ser usado
    selected_model = body.model or settings.OPENROUTER_DEFAULT_MODEL
    logger.info(f"[TR Gen] Iniciando geracao streaming com modelo: {selected_model}")

    # Carregar skills ativas
    active_skills_instr = ""
    if body.active_skills:
        skills_objs = await _load_skills_ativas_by_ids(body.active_skills, current_user.id, db)
        if skills_objs:
            active_skills_instr = "\nDIRETRIZES DE HABILIDADES SELECIONADAS:\n"
            for skill in skills_objs:
                active_skills_instr += f"- {skill.nome}: {skill.instrucao}\n"
            logger.info(f"[TR Gen] {len(skills_objs)} skill(s) ativada(s).")

    # Criar agente e gerar
    agent = TRChatAgent(model_override=selected_model, active_skills_instr=active_skills_instr)
    logger.info(f"[TR Gen] Agente criado, iniciando geracao...")

    async def stream_generate():
        reasoning_buffer = ""
        content_buffer = ""
        chunk_count = 0
        try:
            async for chunk_data in agent.gerar(context, messages):
                if chunk_data["type"] == "reasoning":
                    reasoning_buffer += chunk_data["content"]
                    yield f"data: {json.dumps({'type': 'reasoning', 'content': reasoning_buffer})}\n\n"
                
                elif chunk_data["type"] == "content":
                    chunk = chunk_data["content"]
                    chunk_count += 1
                    content_buffer += chunk
                    if chunk_count <= 5 or chunk_count % 10 == 0:
                        logger.debug(f"[TR Gen] Chunk #{chunk_count}: {chunk[:100]}...")
            # Tentar parsear JSON final
            try:
                cleaned = content_buffer.strip()
                if cleaned.startswith("```json"):
                    cleaned = cleaned[7:]
                if cleaned.startswith("```"):
                    cleaned = cleaned[3:]
                if cleaned.endswith("```"):
                    cleaned = cleaned[:-3]

                parsed = json.loads(cleaned.strip())
                logger.info(f"[TR Gen] JSON parseado com sucesso. Campos: {list(parsed.keys())}")
                yield f"data: {json.dumps({'type': 'complete', 'success': True, 'data': parsed})}\n\n"
            except json.JSONDecodeError as je:
                logger.warning(f"[TR Gen] Falha ao parsear JSON: {je}")
                logger.warning(f"[TR Gen] Raw buffer: {content_buffer[:300]}...")
                yield f"data: {json.dumps({'type': 'complete', 'success': True, 'raw': content_buffer})}\n\n"

        except Exception as e:
            logger.error(f"[TR Gen] === ERRO NA GERACAO ===: {e}", exc_info=True)
            yield f"data: {json.dumps({'type': 'error', 'error': str(e)})}\n\n"

    return StreamingResponse(
        stream_generate(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        }
    )


class TRRegenerarCampoInput(BaseModel):
    """Input para regenerar um campo especifico do TR."""
    campo: str
    history: List[Dict[str, Any]] = []
    prompt_adicional: Optional[str] = None
    valor_atual: Optional[str] = None
    model: Optional[str] = None
    active_skills: Optional[List[int]] = []
    attachments: Optional[List[Dict[str, Any]]] = None


@router.post("/tr/chat/{projeto_id}/regenerar-campo")
async def regenerar_campo_tr(
    projeto_id: int,
    body: TRRegenerarCampoInput,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(auth_get_current_user),
):
    """
    Regenera um campo especifico do TR usando IA.

    Args:
        projeto_id: ID do projeto
        body: Campo a regenerar, historico e instrucoes adicionais

    Returns:
        JSON com o novo valor do campo
    """
    logger.info(f"[TR Regen] Regenerando campo '{body.campo}' para projeto {projeto_id}")
    logger.info(f"[TR Regen] Prompt adicional: {body.prompt_adicional}")
    logger.info(f"[TR Regen] Valor atual: {body.valor_atual[:100] if body.valor_atual else 'Nenhum'}...")

    # Labels dos campos para mensagens amigaveis
    campos_labels = {
        'definicao_objeto': 'Definicao do Objeto (TR-01)',
        'justificativa': 'Justificativa e Fundamentacao (TR-02)',
        'especificacao_tecnica': 'Especificacao Tecnica (TR-03)',
        'obrigacoes': 'Obrigacoes das Partes (TR-04)',
        'criterios_aceitacao': 'Criterios de Aceitacao e Pagamento (TR-05)',
    }

    campo_label = campos_labels.get(body.campo, body.campo)

    # Buscar contexto do projeto
    context = await _build_tr_chat_context(projeto_id, db)

    # Adicionar anexos especificos da regeneração (se houver) ao contexto
    if body.attachments:
        textos_anexos = [f"[{att.get('filename', 'arquivo')}]: {att['extracted_text']}" for att in body.attachments if att.get("extracted_text")]
        if textos_anexos:
            base_conhecimento_field = "\n\nANEXOS ADICIONAIS PARA ESTE CAMPO:\n" + "\n\n".join(textos_anexos)
            if 'base_conhecimento' in context.dados_coletados:
                context.dados_coletados['base_conhecimento'] += "\n" + base_conhecimento_field
            else:
                context.dados_coletados['base_conhecimento'] = base_conhecimento_field

    # Construir prompt para regeneracao do campo especifico
    conversa_resumo = ""
    if body.history:
        partes = []
        for msg in body.history[-5:]:  # Ultimas 5 mensagens
            prefixo = "Usuario:" if msg.get("role") == "user" else "IA:"
            partes.append(f"{prefixo} {msg.get('content', '')[:200]}")
        conversa_resumo = "\n".join(partes)

    system_prompt = f"""Voce e um especialista em Termos de Referencia do TRE-GO.

Sua tarefa e regenerar APENAS o campo "{campo_label}" de um TR (Termo de Referencia).

REGRAS:
1. Retorne APENAS o novo texto do campo, sem JSON, sem aspas extras, sem markdown
2. Use linguagem formal, tecnica e objetiva
3. Foque na fundamentacao legal (Lei 14.133/2021, art. 6, XXIII)
4. Se o usuario deu instrucoes especificas, siga-as
5. O texto deve ser conciso mas completo"""

    # Incluir contexto do ETP se disponivel
    etp_context = ""
    if context.etp:
        etp_context = f"""
CONTEXTO DO ETP APROVADO:
- Solucao: {context.etp.get('descricao_solucao', 'N/A')[:300] if context.etp.get('descricao_solucao') else 'N/A'}
- Requisitos: {context.etp.get('requisitos_contratacao', 'N/A')[:300] if context.etp.get('requisitos_contratacao') else 'N/A'}
"""

    user_prompt = f"""PROJETO: {context.projeto_titulo}
{etp_context}
CAMPO A REGENERAR: {campo_label}

VALOR ATUAL DO CAMPO:
{body.valor_atual or 'Nao preenchido'}

CONTEXTO DA CONVERSA:
{conversa_resumo or 'Nao disponivel'}

INSTRUCOES DO USUARIO:
{body.prompt_adicional or 'Nenhuma instrucao especifica - melhore o texto mantendo a essencia.'}

Gere o novo texto para o campo "{campo_label}". Retorne APENAS o texto, sem formatacao extra."""

    try:
        from openai import AsyncOpenAI
        client = AsyncOpenAI(
            api_key=settings.OPENROUTER_API_KEY,
            base_url=settings.OPENROUTER_BASE_URL,
            timeout=settings.OPENROUTER_TIMEOUT,
        )

        # Modelo a ser usado
        selected_model = body.model or settings.OPENROUTER_DEFAULT_MODEL

        # Carregar skills ativas
        skills_context = ""
        if body.active_skills:
            skills_objs = await _load_skills_ativas_by_ids(body.active_skills, current_user.id, db)
            if skills_objs:
                skills_context = "\nDIRETRIZES DE HABILIDADES ATIVAS:\n"
                for skill in skills_objs:
                    skills_context += f"- {skill.nome}: {skill.instrucao}\n"

        # Injetar skills no system prompt
        if skills_context:
            system_prompt += f"\n\n{skills_context}"

        response = await client.chat.completions.create(
            model=selected_model,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            temperature=0.5,
            max_tokens=3000,
        )

        novo_valor = response.choices[0].message.content.strip()

        # Limpar possiveis aspas extras
        if novo_valor.startswith('"') and novo_valor.endswith('"'):
            novo_valor = novo_valor[1:-1]

        logger.info(f"[TR Regen] Campo '{body.campo}' regenerado com sucesso. Novo valor: {novo_valor[:100]}...")

        return {
            "success": True,
            "campo": body.campo,
            "value": novo_valor,
            "label": campo_label
        }

    except Exception as e:
        logger.error(f"[TR Regen] Erro ao regenerar campo: {e}", exc_info=True)
        return {
            "success": False,
            "error": str(e),
            "campo": body.campo
        }


async def _build_tr_chat_context(projeto_id: int, db: AsyncSession) -> ChatContext:
    """Constroi o ChatContext para o agente TR conversacional.

    Inclui ETP (obrigatorio), DFD, PGR e Cotacoes APROVADOS como contexto.
    O Edital usa _build_edital_chat_context (definida abaixo).
    """

    # Buscar projeto
    result = await db.execute(
        select(Projeto).filter(Projeto.id == projeto_id)
    )
    projeto = result.scalars().first()

    if not projeto:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Projeto {projeto_id} nao encontrado"
        )

    # Buscar itens PAC
    itens_pac = await pac_service.get_itens_by_projeto(projeto, db)

    # Criar contexto
    # Criar contexto
    skills = await _load_skills_ativas(projeto_id, db, "tr", projeto.usuario_id)
    context = ChatContext(
        projeto_id=projeto.id,
        projeto_titulo=projeto.titulo,
        setor_usuario="Unidade Requisitante",
        skills=skills,
        itens_pac=itens_pac or [],
    )

    # Buscar ETP APROVADO ou PUBLICADO (obrigatorio para TR)
    etp_result = await db.execute(
        select(ETP)
        .filter(ETP.projeto_id == projeto_id, ETP.status.in_(["aprovado", "publicado"]))
        .order_by(ETP.data_criacao.desc())
        .limit(1)
    )
    etp = etp_result.scalars().first()
    if etp:
        context.etp = {
            "id": etp.id,
            "descricao_necessidade": etp.descricao_necessidade,
            "requisitos_contratacao": etp.requisitos_contratacao,
            "estimativa_quantidades": etp.estimativa_quantidades,
            "levantamento_mercado": etp.levantamento_mercado,
            "descricao_solucao": etp.descricao_solucao,
            "justificativa_parcelamento": etp.justificativa_parcelamento,
            "resultados_pretendidos": etp.resultados_pretendidos,
            "viabilidade_contratacao": etp.viabilidade_contratacao,
            "versao": etp.versao,
        }

    # Buscar DFD APROVADO
    dfd_result = await db.execute(
        select(DFD)
        .filter(DFD.projeto_id == projeto_id, DFD.status.in_(["aprovado", "publicado"]))
        .order_by(DFD.data_criacao.desc())
        .limit(1)
    )
    dfd = dfd_result.scalars().first()
    if dfd:
        context.dfd = {
            "id": dfd.id,
            "descricao_objeto": dfd.descricao_objeto,
            "justificativa": dfd.justificativa,
            "alinhamento_estrategico": dfd.alinhamento_estrategico,
            "grau_prioridade": dfd.grau_prioridade,
            "versao": dfd.versao,
        }

    # Buscar Cotacoes APROVADAS
    pp_result = await db.execute(
        select(PesquisaPrecos)
        .filter(PesquisaPrecos.projeto_id == projeto_id, PesquisaPrecos.status.in_(["aprovado", "publicado"]))
        .order_by(PesquisaPrecos.data_criacao.desc())
        .limit(1)
    )
    pp = pp_result.scalars().first()
    if pp:
        context.pesquisa_precos = {
            "id": pp.id,
            "valor_total_cotacao": pp.valor_total_cotacao or 0,
            "quantidade_fornecedores": len(pp.itens_cotados or []),
            "versao": pp.versao,
        }

    # Buscar PGR APROVADO
    pgr_result = await db.execute(
        select(Riscos)
        .filter(Riscos.projeto_id == projeto_id, Riscos.status.in_(["aprovado", "publicado"]))
        .order_by(Riscos.data_criacao.desc())
        .limit(1)
    )
    pgr = pgr_result.scalars().first()
    if pgr:
        context.pgr = {
            "id": pgr.id,
            "identificacao_objeto": pgr.identificacao_objeto,
            "resumo_analise_planejamento": pgr.resumo_analise_planejamento,
            "resumo_analise_selecao": pgr.resumo_analise_selecao,
            "resumo_analise_gestao": pgr.resumo_analise_gestao,
            "versao": pgr.versao,
        }

    return context


# ========== ENDPOINTS DE CHAT (EDITAL) ==========

class EditalChatMessageInput(BaseModel):
    """Mensagem enviada pelo usuario no chat Edital."""
    content: str
    history: List[dict] = []
    modalidade: Optional[str] = None
    criterio: Optional[str] = None
    modo_disputa: Optional[str] = None


class EditalChatGenerateInput(BaseModel):
    """Dados para geracao do Edital a partir do chat."""
    history: List[dict] = []
    modalidade: Optional[str] = None
    criterio: Optional[str] = None
    modo_disputa: Optional[str] = None
    attachments: Optional[List[Dict[str, Any]]] = None


class EditalChatInitResponse(BaseModel):
    """Resposta inicial do chat Edital."""
    mensagem_inicial: str
    projeto_id: int
    projeto_titulo: str
    tr_aprovado: bool
    etp_aprovado: bool
    dfd_aprovado: bool
    pgr_aprovado: bool
    cotacao_aprovada: bool
    valor_estimado: float


@router.get("/edital/chat/init/{projeto_id}")
async def iniciar_chat_edital(
    projeto_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(auth_get_current_user),
) -> EditalChatInitResponse:
    """Inicializa o chat para geracao de Edital."""
    context = await _build_edital_chat_context(projeto_id, db)
    agent = EditalChatAgent()
    mensagem_inicial = agent.get_mensagem_inicial(context)

    valor_estimado = 0.0
    if context.pesquisa_precos:
        valor_estimado = context.pesquisa_precos.get('valor_total_cotacao', 0)

    return EditalChatInitResponse(
        mensagem_inicial=mensagem_inicial,
        projeto_id=context.projeto_id,
        projeto_titulo=context.projeto_titulo,
        tr_aprovado=context.tr is not None,
        etp_aprovado=context.etp is not None,
        dfd_aprovado=context.dfd is not None,
        pgr_aprovado=context.pgr is not None,
        cotacao_aprovada=context.pesquisa_precos is not None,
        valor_estimado=valor_estimado,
    )


@router.post("/edital/chat/{projeto_id}")
async def chat_edital(
    projeto_id: int,
    message: EditalChatMessageInput,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(auth_get_current_user),
):
    """Processa uma mensagem do chat Edital e retorna resposta em streaming."""
    context = await _build_edital_chat_context(projeto_id, db)

    if message.modalidade:
        context.dados_coletados['modalidade'] = message.modalidade
    if message.criterio:
        context.dados_coletados['criterio_julgamento'] = message.criterio
    if message.modo_disputa:
        context.dados_coletados['modo_disputa'] = message.modo_disputa

    history = [Message(role=msg["role"], content=msg["content"]) for msg in message.history]
    agent = EditalChatAgent()

    async def stream_chat():
        reasoning_buffer = ""
        content_buffer = ""
        try:
            async for chunk_data in agent.chat(message.content, history, context):
                # chunk_data agora eh um dict {"type": "...", "content": "..."}
                
                if chunk_data["type"] == "reasoning":
                    reasoning_buffer += chunk_data["content"]
                    yield f"data: {json.dumps({'type': 'reasoning', 'content': reasoning_buffer})}\n\n"
                
                elif chunk_data["type"] == "content":
                    chunk = chunk_data["content"]
                    content_buffer += chunk
                    yield f"data: {json.dumps({'type': 'chunk', 'content': content_buffer})}\n\n"
                    # Forcar flush do evento
                    await asyncio.sleep(0)

            should_generate = '[GERAR_EDITAL]' in content_buffer
            if not should_generate:
                user_msg = message.content.lower().strip()
                auth_phrases = ['gere', 'gerar', 'pode gerar', 'inicie', 'sim', 'ok', 'confirmo', 'autorizo', 'padrao', 'configuracoes padrao']
                if any(phrase in user_msg for phrase in auth_phrases):
                    if len(history) >= 1 or context.tr is not None:
                        should_generate = True

            if should_generate:
                yield f"data: {json.dumps({'type': 'action', 'action': 'generate', 'message': 'Iniciando geracao do Edital...'})}\n\n"

            yield f"data: {json.dumps({'type': 'done', 'full_response': content_buffer})}\n\n"
        except Exception as e:
            logger.error(f"Erro no chat Edital: {e}")
            yield f"data: {json.dumps({'type': 'error', 'error': str(e)})}\n\n"

    return StreamingResponse(stream_chat(), media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "Connection": "keep-alive", "X-Accel-Buffering": "no"})


@router.post("/edital/chat/{projeto_id}/gerar")
async def gerar_edital_from_chat(
    projeto_id: int,
    body: EditalChatGenerateInput,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(auth_get_current_user),
):
    """Gera o Edital baseado no historico da conversa."""
    logger.info(f"[Edital Gen] Iniciando geracao para projeto {projeto_id}")
    context = await _build_edital_chat_context(projeto_id, db)

    if body.modalidade:
        context.dados_coletados['modalidade'] = body.modalidade
    if body.criterio:
        context.dados_coletados['criterio_julgamento'] = body.criterio
    if body.modo_disputa:
        context.dados_coletados['modo_disputa'] = body.modo_disputa

    # Incluir base de conhecimento dos anexos
    if body.attachments:
        textos_anexos = [f"[{att.get('filename', 'arquivo')}]: {att['extracted_text']}" for att in body.attachments if att.get("extracted_text")]
        if textos_anexos:
            context.dados_coletados['base_conhecimento'] = "\n\n".join(textos_anexos)

    messages = [Message(role=msg["role"], content=msg["content"]) for msg in body.history]
    agent = EditalChatAgent()

    async def stream_generate():
        reasoning_buffer = ""
        content_buffer = ""
        try:
            async for chunk_data in agent.gerar(context, messages):
                if chunk_data["type"] == "reasoning":
                    reasoning_buffer += chunk_data["content"]
                    yield f"data: {json.dumps({'type': 'reasoning', 'content': reasoning_buffer})}\n\n"
                
                elif chunk_data["type"] == "content":
                    chunk = chunk_data["content"]
                    content_buffer += chunk
                    yield f"data: {json.dumps({'type': 'chunk', 'content': content_buffer})}\n\n"

            try:
                cleaned = content_buffer.strip()
                for prefix in ["```json", "```"]:
                    if cleaned.startswith(prefix):
                        cleaned = cleaned[len(prefix):]
                if cleaned.endswith("```"):
                    cleaned = cleaned[:-3]
                parsed = json.loads(cleaned.strip())
                yield f"data: {json.dumps({'type': 'complete', 'success': True, 'data': parsed})}\n\n"
            except json.JSONDecodeError:
                yield f"data: {json.dumps({'type': 'complete', 'success': True, 'raw': content_buffer})}\n\n"
        except Exception as e:
            logger.error(f"[Edital Gen] Erro: {e}", exc_info=True)
            yield f"data: {json.dumps({'type': 'error', 'error': str(e)})}\n\n"

    return StreamingResponse(stream_generate(), media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "Connection": "keep-alive", "X-Accel-Buffering": "no"})


class EditalRegenerarCampoInput(BaseModel):
    """Input para regenerar um campo especifico do Edital."""
    campo: str
    history: List[Dict[str, Any]] = []
    prompt_adicional: Optional[str] = None
    valor_atual: Optional[str] = None
    model: Optional[str] = None
    active_skills: Optional[List[int]] = []
    attachments: Optional[List[Dict[str, Any]]] = None


@router.post("/edital/chat/{projeto_id}/regenerar-campo")
async def regenerar_campo_edital(
    projeto_id: int,
    body: EditalRegenerarCampoInput,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(auth_get_current_user),
):
    """Regenera um campo especifico do Edital usando IA."""
    campos_labels = {
        'objeto': 'Objeto da Licitacao',
        'condicoes_participacao': 'Condicoes de Participacao',
        'criterios_julgamento': 'Criterios de Julgamento',
        'fase_lances': 'Sessao Publica e Recursos',
    }
    campo_label = campos_labels.get(body.campo, body.campo)
    context = await _build_edital_chat_context(projeto_id, db)

    # Adicionar anexos especificos da regeneração (se houver) ao contexto
    if body.attachments:
        textos_anexos = [f"[{att.get('filename', 'arquivo')}]: {att['extracted_text']}" for att in body.attachments if att.get("extracted_text")]
        if textos_anexos:
            base_conhecimento_field = "\n\nANEXOS ADICIONAIS PARA ESTE CAMPO:\n" + "\n\n".join(textos_anexos)
            if 'base_conhecimento' in context.dados_coletados:
                context.dados_coletados['base_conhecimento'] += "\n" + base_conhecimento_field
            else:
                context.dados_coletados['base_conhecimento'] = base_conhecimento_field

    # Modelo a ser usado
    selected_model = body.model or settings.OPENROUTER_DEFAULT_MODEL

    # Carregar skills ativas
    skills_context = ""
    if body.active_skills:
        skills_objs = await _load_skills_ativas_by_ids(body.active_skills, current_user.id, db)
        if skills_objs:
            skills_context = "\nDIRETRIZES DE HABILIDADES ATIVAS:\n"
            for skill in skills_objs:
                skills_context += f"- {skill.nome}: {skill.instrucao}\n"

    system_prompt = f"""Voce e um especialista em Editais de Licitacao do TRE-GO.
Regenere APENAS o campo "{campo_label}" usando linguagem juridica precisa (Lei 14.133/2021).

{skills_context}

Retorne APENAS o texto, sem JSON ou markdown."""

    tr_ctx = f"\nTR: {context.tr.get('definicao_objeto', '')[:300]}" if context.tr else ""
    user_prompt = f"PROJETO: {context.projeto_titulo} | TRE-GO | UASG: 070017{tr_ctx}\nCAMPO: {campo_label}\nATUAL: {body.valor_atual or 'Vazio'}\nINSTRUCOES: {body.prompt_adicional or 'Melhore o texto.'}"

    try:
        from openai import AsyncOpenAI
        client = AsyncOpenAI(api_key=settings.OPENROUTER_API_KEY, base_url=settings.OPENROUTER_BASE_URL, timeout=settings.OPENROUTER_TIMEOUT)
        response = await client.chat.completions.create(
            model=selected_model,
            messages=[{"role": "system", "content": system_prompt}, {"role": "user", "content": user_prompt}],
            temperature=0.4, max_tokens=4000,
        )
        novo_valor = response.choices[0].message.content.strip()
        if novo_valor.startswith('"') and novo_valor.endswith('"'):
            novo_valor = novo_valor[1:-1]
        return {"success": True, "campo": body.campo, "value": novo_valor, "label": campo_label}
    except Exception as e:
        logger.error(f"[Edital Regen] Erro: {e}", exc_info=True)
        return {"success": False, "error": str(e), "campo": body.campo}


async def _build_edital_chat_context(projeto_id: int, db: AsyncSession) -> ChatContext:
    """Constroi o ChatContext para o agente Edital conversacional."""
    result = await db.execute(select(Projeto).filter(Projeto.id == projeto_id))
    projeto = result.scalars().first()
    if not projeto:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Projeto {projeto_id} nao encontrado")

    itens_pac = await pac_service.get_itens_by_projeto(projeto, db)
    skills = await _load_skills_ativas(projeto_id, db, "edital", projeto.usuario_id)
    context = ChatContext(projeto_id=projeto.id, projeto_titulo=projeto.titulo, setor_usuario="Unidade Requisitante", itens_pac=itens_pac or [], skills=skills)

    # TR APROVADO ou PUBLICADO
    tr_result = await db.execute(select(TR).filter(TR.projeto_id == projeto_id, TR.status.in_(["aprovado", "publicado"])).order_by(TR.data_criacao.desc()).limit(1))
    tr = tr_result.scalars().first()
    if tr:
        context.tr = {"id": tr.id, "definicao_objeto": tr.definicao_objeto, "justificativa": tr.justificativa, "especificacao_tecnica": tr.especificacao_tecnica, "versao": tr.versao}

    # ETP APROVADO ou PUBLICADO
    etp_result = await db.execute(select(ETP).filter(ETP.projeto_id == projeto_id, ETP.status.in_(["aprovado", "publicado"])).order_by(ETP.data_criacao.desc()).limit(1))
    etp = etp_result.scalars().first()
    if etp:
        context.etp = {"id": etp.id, "descricao_necessidade": etp.descricao_necessidade, "descricao_solucao": etp.descricao_solucao, "versao": etp.versao}

    # DFD APROVADO ou PUBLICADO
    dfd_result = await db.execute(select(DFD).filter(DFD.projeto_id == projeto_id, DFD.status.in_(["aprovado", "publicado"])).order_by(DFD.data_criacao.desc()).limit(1))
    dfd = dfd_result.scalars().first()
    if dfd:
        context.dfd = {"id": dfd.id, "descricao_objeto": dfd.descricao_objeto, "justificativa": dfd.justificativa, "versao": dfd.versao}

    # Cotacoes APROVADAS ou PUBLICADAS
    pp_result = await db.execute(select(PesquisaPrecos).filter(PesquisaPrecos.projeto_id == projeto_id, PesquisaPrecos.status.in_(["aprovado", "publicado"])).order_by(PesquisaPrecos.data_criacao.desc()).limit(1))
    pp = pp_result.scalars().first()
    if pp:
        context.pesquisa_precos = {"id": pp.id, "valor_total_cotacao": pp.valor_total_cotacao or 0, "versao": pp.versao}

    # PGR APROVADO ou PUBLICADO
    pgr_result = await db.execute(select(Riscos).filter(Riscos.projeto_id == projeto_id, Riscos.status.in_(["aprovado", "publicado"])).order_by(Riscos.data_criacao.desc()).limit(1))
    pgr = pgr_result.scalars().first()
    if pgr:
        context.pgr = {"id": pgr.id, "identificacao_objeto": pgr.identificacao_objeto, "versao": pgr.versao}

    return context


# ========== DEEP RESEARCH ==========
@router.post("/deep-research/stream")
async def stream_deep_research(
    request: DeepResearchRequest,
    current_user: User = Depends(auth_get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Endpoint de streaming para Deep Research.
    Retorna eventos SSE com o progresso da pesquisa.
    """
    return StreamingResponse(
        deep_research_service.stream_research(request.topic, request.context),
        media_type="text/event-stream"
    )


# ========== JUSTIFICATIVA DE EXCEPCIONALIDADE (JE) ==========

@router.get("/justificativa_excepcionalidade/chat/init/{projeto_id}")
async def iniciar_chat_je(
    projeto_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(auth_get_current_user),
) -> ChatInitResponse:
    """
    Inicializa o chat para geração de Justificativa de Excepcionalidade.
    
    Retorna a mensagem inicial da IA e dados do projeto.
    """
    # Buscar contexto do projeto
    context = await _build_chat_context(projeto_id, db, "justificativa_excepcionalidade")
    
    # Criar agente e obter mensagem inicial
    agent = JustificativaExcepcionalidadeChatAgent()
    mensagem_inicial = agent.get_mensagem_inicial(context)
    
    return ChatInitResponse(
        mensagem_inicial=mensagem_inicial,
        projeto_id=context.projeto_id,
        projeto_titulo=context.projeto_titulo,
        itens_pac_count=len(context.itens_pac),
    )


@router.post("/justificativa_excepcionalidade/chat/{projeto_id}")
async def chat_je(
    projeto_id: int,
    message: ChatMessageInput,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(auth_get_current_user),
):
    """
    Processa uma mensagem do chat para JE e retorna resposta em streaming.

    Quando a IA detectar que está pronta para gerar, retorna:
    {"action": "generate", "message": "..."}
    """
    # Buscar contexto do projeto
    context = await _build_chat_context(projeto_id, db, "justificativa_excepcionalidade")

    # Converter histórico para objetos Message
    history = [
        Message(role=msg["role"], content=msg["content"])
        for msg in message.history
    ]

    # Usar modelo selecionado pelo usuário ou padrão
    modelo_ia = message.model or settings.OPENROUTER_DEFAULT_MODEL
    agent = JustificativaExcepcionalidadeChatAgent(model_override=modelo_ia)
    
    async def stream_chat():
        reasoning_buffer = ""
        content_buffer = ""
        try:
            async for chunk_data in agent.chat(message.content, history, context, message.attachments):
                if chunk_data["type"] == "reasoning":
                    reasoning_buffer += chunk_data["content"]
                    yield f"data: {json.dumps({'type': 'reasoning', 'content': reasoning_buffer})}\n\n"
                
                elif chunk_data["type"] == "content":
                    chunk = chunk_data["content"]
                    content_buffer += chunk
                    yield f"data: {json.dumps({'type': 'chunk', 'content': content_buffer})}\n\n"
                    await asyncio.sleep(0)

            # Verificar se a resposta contém marcador de geração
            should_generate = '[GERAR_JE]' in content_buffer
            
            if not should_generate:
                user_msg = message.content.lower().strip()
                authorization_phrases = [
                    'gere', 'gerar', 'pode gerar', 'inicie', 'inicie a geração',
                    'sim', 'ok', 'confirmo', 'autorizo', 'prossiga', 'vai', 'manda',
                    'pode iniciar', 'inicia', 'gera', 'faça', 'faz', 'execute',
                    'confirma', 'positivo', 'afirmativo', 'isso', 'isso mesmo'
                ]
                if any(phrase in user_msg for phrase in authorization_phrases):
                    has_content = len(history) >= 2
                    if has_content:
                        should_generate = True
            
            if should_generate:
                buffer_limpo = content_buffer.replace('[GERAR_JE]', '').strip()
                yield f"data: {json.dumps({'type': 'action', 'action': 'generate', 'message': 'Iniciando geração da Justificativa de Excepcionalidade...'})}\n\n"

            yield f"data: {json.dumps({'type': 'done', 'full_response': content_buffer})}\n\n"

        except Exception as e:
            logger.error(f"Erro no chat JE: {e}")
            yield f"data: {json.dumps({'type': 'error', 'error': str(e)})}\n\n"
    
    return StreamingResponse(
        stream_chat(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        }
    )


@router.post("/justificativa_excepcionalidade/chat/{projeto_id}/gerar")
async def gerar_je_from_chat(
    projeto_id: int,
    body: ChatGenerateInput,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(auth_get_current_user),
):
    """
    Gera a Justificativa de Excepcionalidade baseada no histórico da conversa.

    Chamado quando a IA sinaliza que está pronta para gerar.
    """
    logger.info(f"[JE Gen] === INICIANDO GERAÇÃO para projeto {projeto_id} ===")
    
    # Buscar contexto do projeto
    context = await _build_chat_context(projeto_id, db, "justificativa_excepcionalidade")

    # Converter histórico para objetos Message
    messages = [
        Message(role=msg["role"], content=msg["content"])
        for msg in body.history
    ]

    # Incluir texto extraído dos anexos (base de conhecimento) no contexto
    if body.attachments:
        textos_anexos = []
        for att in body.attachments:
            if att.get("extracted_text"):
                textos_anexos.append(f"[{att.get('filename', 'arquivo')}]: {att['extracted_text']}")
        if textos_anexos:
            context.dados_coletados['base_conhecimento'] = "\n\n".join(textos_anexos)

    # Usar modelo selecionado pelo usuário ou padrão
    modelo_ia = body.model or settings.OPENROUTER_DEFAULT_MODEL
    agent = JustificativaExcepcionalidadeChatAgent(model_override=modelo_ia)
    
    async def stream_generation():
        reasoning_buffer = ""
        json_buffer = ""
        try:
            async for chunk_data in agent.gerar(context, messages):
                if chunk_data["type"] == "reasoning":
                    reasoning_buffer += chunk_data["content"]
                    yield f"data: {json.dumps({'type': 'reasoning', 'content': reasoning_buffer})}\n\n"
                
                elif chunk_data["type"] == "content":
                    chunk = chunk_data["content"]
                    json_buffer += chunk
                    yield f"data: {json.dumps({'type': 'chunk', 'content': json_buffer})}\n\n"
                    await asyncio.sleep(0)

            # Tentar fazer parse do JSON gerado
            try:
                je_data = json.loads(json_buffer)
                logger.info(f"[JE Gen] JSON gerado com sucesso: {len(je_data)} campos")
                yield f"data: {json.dumps({'type': 'complete', 'success': True, 'data': je_data})}\n\n"
            except json.JSONDecodeError as e:
                logger.error(f"[JE Gen] Erro ao fazer parse do JSON: {e}")
                yield f"data: {json.dumps({'type': 'error', 'error': f'Erro ao processar resposta: {str(e)}'})}\n\n"

        except Exception as e:
            logger.error(f"Erro na geração JE: {e}")
            yield f"data: {json.dumps({'type': 'error', 'error': str(e)})}\n\n"
    
    return StreamingResponse(
        stream_generation(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        }
    )


@router.post("/justificativa_excepcionalidade/chat/{projeto_id}/regenerar-campo")
async def regenerar_campo_je(
    projeto_id: int,
    body: RegenerarCampoInput,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(auth_get_current_user),
):
    """
    Regenera um campo específico da Justificativa de Excepcionalidade.
    
    Recebe o histórico e o campo a regenerar, retorna novo conteúdo.
    """
    logger.info(f"[JE Regen] Regenerando campo '{body.campo}' do projeto {projeto_id}")
    
    # Buscar contexto do projeto
    context = await _build_chat_context(projeto_id, db, "justificativa_excepcionalidade")

    # Usar modelo selecionado pelo usuário ou padrão
    modelo_ia = body.model or settings.OPENROUTER_DEFAULT_MODEL
    agent = JustificativaExcepcionalidadeChatAgent(model_override=modelo_ia)
    
    # Converter ChatContext para dict para regenerar_campo (BaseAgent)
    from dataclasses import asdict
    context_dict = asdict(context)
    
    async def stream_regen():
        content_buffer = ""
        try:
            # Chamar agent.regenerar_campo com os parâmetros corretos
            # O método retorna string chunks, não dicts com type
            async for chunk in agent.regenerar_campo(
                campo=body.campo,
                contexto=context_dict,
                valor_atual=body.valor_atual,
                instrucoes=body.prompt_adicional,
            ):
                content_buffer += chunk
                yield f"data: {json.dumps({'type': 'chunk', 'content': content_buffer})}\n\n"
                await asyncio.sleep(0)

            logger.info(f"[JE Regen] Regeneração concluída para campo '{body.campo}'")
            yield f"data: {json.dumps({'type': 'done', 'campo': body.campo, 'content': content_buffer})}\n\n"

        except Exception as e:
            logger.error(f"[JE Regen] Erro ao regenerar campo JE '{body.campo}': {e}", exc_info=True)
            yield f"data: {json.dumps({'type': 'error', 'error': str(e)})}\n\n"
    
    return StreamingResponse(
        stream_regen(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        }
    )

