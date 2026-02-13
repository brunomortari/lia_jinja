"""
ETP Chat Config
===============
Estudo Técnico Preliminar — Procura por DFD, PesquisaPrecos, PGR para contexto.
"""

from app.services.agents import ETPChatAgent
from ._factory import ArtefactChatConfig

config = ArtefactChatConfig(
    tipo="etp",
    label="Estudo Técnico Preliminar",
    marker="[GERAR_ETP]",
    agent_chat_class=ETPChatAgent,
    context_deps=["dfd", "pp", "pgr"],  # DFD + Prices + PGR context
    persistido=True,
)
