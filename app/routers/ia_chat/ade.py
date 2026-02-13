"""
Sistema LIA - ADE Chat Config
==============================
Configuração do chat para Aviso de Dispensa Eletrônica.
"""

from ._factory import ArtefactChatConfig
from app.services.agents import ADEChatAgent

config = ArtefactChatConfig(
    tipo="ade",
    label="Aviso de Dispensa Eletrônica",
    marker="[GERAR_ADE]",
    agent_chat_class=ADEChatAgent,
    context_deps=["dfd", "etp", "trs"]
)
