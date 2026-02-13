"""
TR Chat Config
===============
Termo de Referência — Procura por ETP, DFD, PGR, PesquisaPrecos.
"""

from app.services.agents import TRChatAgent
from ._factory import ArtefactChatConfig

config = ArtefactChatConfig(
    tipo="tr",
    label="Termo de Referência",
    marker="[GERAR_TR]",
    agent_chat_class=TRChatAgent,
    context_deps=["etp", "dfd", "pgr", "pp"],  # Full context
    persistido=True,
)
