"""
Edital Chat Config
==================
Edital de Licitação — Procura por TR, ETP, DFD, PGR, PesquisaPrecos.
"""

from app.services.agents import EditalChatAgent
from ._factory import ArtefactChatConfig

config = ArtefactChatConfig(
    tipo="edital",
    label="Edital de Licitação",
    marker="[GERAR_EDITAL]",
    agent_chat_class=EditalChatAgent,
    context_deps=["tr", "etp", "dfd", "pgr", "pp"],  # Full context
    persistido=True,
)
