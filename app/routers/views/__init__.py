"""
Sistema LIA - Views Module Aggregator
=====================================
Agrega todos os routers de views em um único router principal.

Autor: Equipe TRE-GO
Data: Janeiro 2026
"""

from fastapi import APIRouter

from .auth_views import router as auth_router
from .home_views import router as home_router
from .projeto_views import router as projeto_router

# Exportar componentes compartilhados do common para quem precisar
from .common import (
    templates,
    limiter,
    ARTEFATO_CONFIG,
    DFD_CONFIG_DICT,
    verificar_dependencias,
    get_template_context,
    get_csrf_token_for_template,
    validate_csrf_token,
    require_login
)


# Router principal que agrega todos os sub-routers
router = APIRouter()

# Incluir sub-routers
router.include_router(auth_router, tags=["auth"])
router.include_router(home_router, tags=["home"])
router.include_router(projeto_router, tags=["projetos"])


__all__ = [
    "router",
    "templates",
    "limiter",
    "ARTEFATO_CONFIG",
    "DFD_CONFIG_DICT",
    "verificar_dependencias",
    "get_template_context",
    "get_csrf_token_for_template",
    "validate_csrf_token",
    "require_login"
]
