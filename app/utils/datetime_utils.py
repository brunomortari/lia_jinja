"""
Sistema LIA - Utilitários de Data/Hora
=======================================
Funções centralizadas para trabalhar com datetime no fuso de Brasília.

Autor: Equipe TRE-GO
Data: Fevereiro 2026
"""

from datetime import datetime, timezone, timedelta, date
import logging

logger = logging.getLogger(__name__)

# Timezone de Brasília (UTC-3)
BRASILIA_TZ = timezone(timedelta(hours=-3))


def now_brasilia() -> datetime:
    """
    Retorna datetime atual no fuso horário de Brasília (UTC-3).
    
    Returns:
        datetime naive (sem tzinfo) no horário de Brasília
    """
    return datetime.now(BRASILIA_TZ).replace(tzinfo=None)


def parse_date(date_str: str) -> date | None:
    """
    Parse date from various formats.
    
    Tenta parsear data em múltiplos formatos comuns:
    - ISO: YYYY-MM-DD
    - BR: DD/MM/YYYY
    - Alt: DD-MM-YYYY
    
    Args:
        date_str: String com data
        
    Returns:
        datetime.date ou None se parsing falhar
    """
    if not date_str or not date_str.strip():
        return None
        
    date_str = date_str.strip()
    
    for fmt in ['%Y-%m-%d', '%d/%m/%Y', '%d-%m-%Y']:
        try:
            return datetime.strptime(date_str, fmt).date()
        except ValueError:
            continue
    
    logger.warning(f"Could not parse date: {date_str}")
    return None
