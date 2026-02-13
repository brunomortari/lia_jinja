"""
Sistema LIA - Router de Modelos de IA
======================================
Endpoint para gerenciar modelos disponíveis do OpenRouter
"""

from fastapi import APIRouter
from typing import Dict, Any

from app.config import settings, AVAILABLE_MODELS, MODEL_TIERS

router = APIRouter()


@router.get("/api/ia/models")
async def list_available_models() -> Dict[str, Any]:
    """
    Lista modelos disponíveis do OpenRouter para seleção pelo usuário.
    
    Returns:
        Dict contendo lista de modelos e modelo padrão
    """
    return {
        "models": AVAILABLE_MODELS,
        "default": settings.OPENROUTER_DEFAULT_MODEL,
        "tiers": MODEL_TIERS
    }


@router.get("/api/ia/models/current")
async def get_current_model() -> Dict[str, str]:
    """
    Retorna o modelo padrão configurado.
    
    Returns:
        Dict com ID e nome do modelo atual
    """
    return {
        "id": settings.OPENROUTER_DEFAULT_MODEL,
        "name": "Trinity Mini (Padrão)"
    }
