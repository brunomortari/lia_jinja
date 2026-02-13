"""
Sistema LIA - Router de Chat para Criacao de Skills
====================================================
Endpoint de streaming SSE para o wizard de criacao de skills.

Autor: Equipe TRE-GO
Data: Fevereiro 2026
"""

import json
import logging

from fastapi import APIRouter, Depends
from fastapi.responses import StreamingResponse

from app.models.user import User
from app.auth import current_active_user as get_current_user
from app.schemas.skills import SkillChatMessage
from app.services.agents.skill_wizard_agent import SkillWizardAgent

logger = logging.getLogger(__name__)

router = APIRouter()


@router.post("/skills/chat")
async def chat_skill_wizard(
    message: SkillChatMessage,
    current_user: User = Depends(get_current_user),
):
    """
    Chat streaming para o wizard de criacao de skills.

    Retorna SSE com chunks de texto. Quando a IA gera a skill,
    inclui [SKILL_READY] + JSON no texto.
    """
    modelo_ia = message.model
    agent = SkillWizardAgent(model_override=modelo_ia)

    async def stream_chat():
        buffer = ""
        try:
            async for chunk in agent.chat(message.content, message.history):
                buffer += chunk
                yield f"data: {json.dumps({'type': 'chunk', 'content': chunk})}\n\n"

            # Verificar se a resposta contem skill pronta
            skill_data = SkillWizardAgent.extract_skill_data(buffer)
            if skill_data:
                yield f"data: {json.dumps({'type': 'skill_ready', 'skill': skill_data})}\n\n"

            yield f"data: {json.dumps({'type': 'done', 'full_response': buffer})}\n\n"

        except Exception as e:
            logger.error(f"[SkillWizard] Erro no streaming: {e}")
            yield f"data: {json.dumps({'type': 'error', 'error': str(e)})}\n\n"

    return StreamingResponse(
        stream_chat(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )
