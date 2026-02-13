"""
PGR Chat Config
===============
Plano de Gerenciamento de Riscos (Riscos artefact) — Procura por DFD, PesquisaPrecos.
"""

from app.services.agents import PGRChatAgent
from ._factory import ArtefactChatConfig

config = ArtefactChatConfig(
    tipo="pgr",
    label="Plano de Gerenciamento de Riscos",
    marker="[GERAR_PGR]",
    agent_chat_class=PGRChatAgent,
    context_deps=["dfd", "pp"],  # DFD + Prices
    persistido=True,
)
