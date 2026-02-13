"""
Sistema LIA - Utilities para Deprecação de Endpoints
=====================================================
Helpers para marcar endpoints legados e logar avisos.

Autor: Equipe TRE-GO
Data: Fevereiro 2026
"""

import logging

logger = logging.getLogger(__name__)


def log_deprecation(endpoint: str, alternative: str = None):
    """
    Log deprecation warning for legacy endpoints.
    
    Args:
        endpoint: O endpoint que está deprecated
        alternative: Endpoint ou instrução alternativa (opcional)
    """
    message = f"⚠️ DEPRECATED: Endpoint {endpoint} é legado."
    
    if alternative:
        message += f" Use {alternative} ao invés."
    
    logger.warning(message)
