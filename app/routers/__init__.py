"""
Sistema LIA - Routers Package
==============================
Importa todos os routers da API
"""

# from . import projeto_skillsa, ia_pgr, export, artefatos, dfd, cotacao, prices
from .views import router as views_router

__all__ = [
    "pac",
    "ia",
    "ia_pgr",
    "export",
    "artefatos",
    "dfd",
    "cotacao",
    "prices",
    "views_router"
]
