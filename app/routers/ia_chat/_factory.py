"""
Sistema LIA - Chat Router Factory
==================================
Generic factory that creates 4 chat endpoints for any artefact type.

Eliminates 80% code duplication across DFD, ETP, PGR, TR, Edital, etc.
Each config defines only its differences:
- Agent classes
- Generation marker
- Context dependencies
- Optional extra fields
"""

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Any, Dict, List, Optional, Type
from dataclasses import dataclass
import json
import logging
import asyncio
from datetime import datetime

from app.database import get_db
from app.config import settings
from app.auth import current_active_user as auth_get_current_user
from app.models.user import User
from app.schemas.ia_schemas import ChatMessageInput, ChatGenerateInput, ChatInitResponse, RegenerarCampoInput, Message
from app.services.agents import ConversationalAgent
from ._context import carregar_skills_ativas, stream_agent_response

logger = logging.getLogger(__name__)


@dataclass
class ArtefactChatConfig:
    """Configuration for an artefact chat endpoint factory"""
    tipo: str  # "dfd", "etp", "pgr", "tr", "edital", "pesquisa_precos", "je"
    label: str  # "Documento de Formalização da Demanda"
    marker: str  # "[GERAR_DFD]"
    agent_chat_class: Type[ConversationalAgent]  # DFDChatAgent, etc.
    context_deps: List[str]  # ["dfd", "pp"] — which artefacts to load
    campos_extra: Optional[Dict[str, Any]] = None  # Extra fields per artefact
    persistido: bool = True  # Whether artefact has a DB model (False for JE)


def criar_chat_router(config: ArtefactChatConfig) -> APIRouter:
    """
    Factory: creates 4 endpoints for an artefact's chat flow.
    
    Args:
        config: ArtefactChatConfig with tipo, agent_class, context_deps, etc.
    
    Returns:
        APIRouter with endpoints:
        - GET /chat/init/{projeto_id}
        - POST /chat/{projeto_id}
        - POST /chat/{projeto_id}/gerar
        - POST /chat/{projeto_id}/regenerar-campo
    """
    
    router = APIRouter()
    
    # Import here to avoid circular imports
    from ._context import construir_contexto_chat
    
    # ========== INIT ==========
    @router.get("/chat/init/{projeto_id}", response_model=ChatInitResponse)
    async def init_chat(
        projeto_id: int,
        db: AsyncSession = Depends(get_db),
        current_user: User = Depends(auth_get_current_user),
    ):
        """Inicializa conversa com contexto do projeto"""
        logger.info(f"[{config.tipo.upper()} Chat Init] Projeto {projeto_id}")
        
        try:
            context = await construir_contexto_chat(
                projeto_id=projeto_id,
                db=db,
                tipo_artefato=config.tipo,
                context_deps=config.context_deps
            )
            
            skills = await carregar_skills_ativas(projeto_id, db)
            
            return ChatInitResponse(
                projeto_id=projeto_id,
                projeto_titulo=context.projeto_titulo,
                setor_usuario=context.setor_usuario,
                welcome_message=f"Bem-vindo ao fluxo de {config.label}! 🚀",
                initial_fields=[],  # Pode ser customizado por config
                skills_ativas=skills
            )
        except Exception as e:
            logger.error(f"[{config.tipo.upper()} Init] Erro: {e}")
            raise HTTPException(status_code=400, detail=str(e))
    
    
    # ========== CHAT ==========
    @router.post("/chat/{projeto_id}")
    async def chat_message(
        projeto_id: int,
        body: ChatMessageInput,
        db: AsyncSession = Depends(get_db),
        current_user: User = Depends(auth_get_current_user),
    ):
        """Chat stream — responde mensagens do usuário"""
        logger.info(f"[{config.tipo.upper()} Chat] Projeto {projeto_id}, msg: {body.content[:50]}...")
        
        try:
            # Build context
            context = await construir_contexto_chat(
                projeto_id=projeto_id,
                db=db,
                tipo_artefato=config.tipo,
                context_deps=config.context_deps
            )
            
            # Convert history to Message objects
            history = [
                Message(role=msg["role"], content=msg["content"])
                for msg in body.history
            ]
            
            # Create agent
            modelo_ia = body.model or settings.OPENROUTER_DEFAULT_MODEL
            agent = config.agent_chat_class(model_override=modelo_ia)
            
            async def stream_chat():
                """SSE stream for chat response"""
                reasoning_buffer = ""
                content_buffer = ""
                marker_sent = False
                try:
                    async for chunk_data in agent.chat(
                        message=body.content,
                        history=history,
                        context=context,
                        attachments=body.attachments or []
                    ):
                        if chunk_data["type"] == "reasoning":
                            reasoning_buffer += chunk_data["content"]
                            yield f"data: {json.dumps({'type': 'reasoning', 'content': reasoning_buffer})}\n\n"
                        
                        elif chunk_data["type"] == "content":
                            content_buffer += chunk_data["content"]
                            yield f"data: {json.dumps({'type': 'chunk', 'content': content_buffer})}\n\n"
                        
                        # Check for generation marker
                        if not marker_sent and (config.marker in content_buffer or "iniciando a geração" in content_buffer.lower()):
                            marker_sent = True
                            yield f"data: {json.dumps({'type': 'action', 'action': 'generate', 'message': f'Pronto para gerar {config.label}...'})}\n\n"
                    
                    # Stream finished — send done event
                    yield f"data: {json.dumps({'type': 'done'})}\n\n"
                
                except Exception as e:
                    logger.error(f"[{config.tipo.upper()} Chat] Stream error: {e}")
                    yield f"data: {json.dumps({'type': 'error', 'error': str(e)})}\n\n"
            
            return StreamingResponse(
                stream_chat(),
                media_type="text/event-stream",
                headers={"Cache-Control": "no-cache", "Connection": "keep-alive"}
            )
        
        except Exception as e:
            logger.error(f"[{config.tipo.upper()} Chat] Erro: {e}")
            raise HTTPException(status_code=400, detail=str(e))
    
    
    # ========== GENERATE ==========
    @router.post("/chat/{projeto_id}/gerar")
    async def gerar_from_chat(
        projeto_id: int,
        body: ChatGenerateInput,
        db: AsyncSession = Depends(get_db),
        current_user: User = Depends(auth_get_current_user),
    ):
        """Generate artefact from chat history — SSE stream"""
        logger.info(f"[{config.tipo.upper()} Gen] Projeto {projeto_id}")
        
        try:
            # Build context
            context = await construir_contexto_chat(
                projeto_id=projeto_id,
                db=db,
                tipo_artefato=config.tipo,
                context_deps=config.context_deps
            )
            
            # Convert history to Message objects
            messages = [
                Message(role=msg["role"], content=msg["content"])
                for msg in body.history
            ]
            
            # Add attachments/skills to context
            if body.attachments:
                textos_anexos = []
                for att in body.attachments:
                    if att.get("extracted_text"):
                        textos_anexos.append(f"[{att.get('filename', 'arquivo')}]: {att['extracted_text']}")
                if textos_anexos:
                    context.dados_coletados['base_conhecimento'] = "\n\n".join(textos_anexos)
            
            # Create agent
            modelo_ia = body.model or settings.OPENROUTER_DEFAULT_MODEL
            agent = config.agent_chat_class(model_override=modelo_ia)
            
            async def stream_generation():
                """SSE stream for generation"""
                reasoning_buffer = ""
                json_buffer = ""
                try:
                    async for chunk_data in agent.gerar(context, messages):
                        if chunk_data["type"] == "reasoning":
                            reasoning_buffer += chunk_data["content"]
                            yield f"data: {json.dumps({'type': 'reasoning', 'content': reasoning_buffer})}\n\n"
                        
                        elif chunk_data["type"] == "content":
                            json_buffer += chunk_data["content"]
                            yield f"data: {json.dumps({'type': 'chunk', 'content': json_buffer})}\n\n"
                            await asyncio.sleep(0)
                    
                    # Try to parse final JSON
                    try:
                        # Clean up JSON: remove markdown backticks if present
                        cleaned = json_buffer.strip()
                        if cleaned.startswith('```json'):
                            cleaned = cleaned[7:]
                        if cleaned.startswith('```'):
                            cleaned = cleaned[3:]
                        if cleaned.endswith('```'):
                            cleaned = cleaned[:-3]
                        
                        artefato_data = json.loads(cleaned)
                        logger.info(f"[{config.tipo.upper()} Gen] JSON generated: {len(artefato_data)} fields")
                        yield f"data: {json.dumps({'type': 'complete', 'success': True, 'data': artefato_data})}\n\n"
                    except json.JSONDecodeError as e:
                        logger.error(f"[{config.tipo.upper()} Gen] JSON parse error: {e}")
                        logger.error(f"[{config.tipo.upper()} Gen] Raw buffer (first 500 chars): {json_buffer[:500]}")
                        yield f"data: {json.dumps({'type': 'error', 'error': f'JSON parse error: {str(e)}'})}\n\n"
                
                except Exception as e:
                    logger.error(f"[{config.tipo.upper()} Gen] Error: {e}")
                    yield f"data: {json.dumps({'type': 'error', 'error': str(e)})}\n\n"
            
            return StreamingResponse(
                stream_generation(),
                media_type="text/event-stream",
                headers={"Cache-Control": "no-cache", "Connection": "keep-alive"}
            )
        
        except Exception as e:
            logger.error(f"[{config.tipo.upper()} Gen] Erro: {e}")
            raise HTTPException(status_code=400, detail=str(e))
    
    
    # ========== REGENERATE FIELD ==========
    @router.post("/chat/{projeto_id}/regenerar-campo")
    async def regenerar_campo(
        projeto_id: int,
        body: RegenerarCampoInput,
        db: AsyncSession = Depends(get_db),
        current_user: User = Depends(auth_get_current_user),
    ):
        """Regenerate a single field — SSE stream"""
        logger.info(f"[{config.tipo.upper()} Regen] Campo '{body.campo}' do projeto {projeto_id}")
        
        try:
            # Build context
            context = await construir_contexto_chat(
                projeto_id=projeto_id,
                db=db,
                tipo_artefato=config.tipo,
                context_deps=config.context_deps
            )
            
            # Create agent
            modelo_ia = body.model or settings.OPENROUTER_DEFAULT_MODEL
            agent = config.agent_chat_class(model_override=modelo_ia)
            
            # Convert context to dict for regenerar_campo (if needed)
            from dataclasses import asdict
            context_dict = asdict(context)
            
            async def stream_regen():
                """SSE stream for field regeneration"""
                content_buffer = ""
                first_chunk_trimmed = False
                try:
                    async for chunk in agent.regenerar_campo(
                        campo=body.campo,
                        contexto=context_dict,
                        valor_atual=body.valor_atual,
                        instrucoes=body.prompt_adicional,
                    ):
                        content_buffer += chunk
                        # Trim leading whitespace from the very first non-empty chunk
                        if not first_chunk_trimmed and content_buffer.strip():
                            content_buffer = content_buffer.lstrip()
                            first_chunk_trimmed = True
                        yield f"data: {json.dumps({'type': 'chunk', 'content': content_buffer})}\n\n"
                        await asyncio.sleep(0)
                    
                    logger.info(f"[{config.tipo.upper()} Regen] Complete para '{body.campo}'")
                    yield f"data: {json.dumps({'type': 'done', 'campo': body.campo, 'content': content_buffer})}\n\n"
                
                except Exception as e:
                    logger.error(f"[{config.tipo.upper()} Regen] Error: {e}")
                    yield f"data: {json.dumps({'type': 'error', 'error': str(e)})}\n\n"
            
            return StreamingResponse(
                stream_regen(),
                media_type="text/event-stream",
                headers={"Cache-Control": "no-cache", "Connection": "keep-alive"}
            )
        
        except Exception as e:
            logger.error(f"[{config.tipo.upper()} Regen] Erro: {e}")
            raise HTTPException(status_code=400, detail=str(e))
    
    
    return router
