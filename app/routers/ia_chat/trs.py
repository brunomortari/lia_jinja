"""
Sistema LIA - TRS Chat Config
==============================
Configuração do chat para Termo de Referência Simplificado (Dispensa Valor Baixo).
"""

from ._factory import ArtefactChatConfig
from app.services.agents import TRSChatAgent

config = ArtefactChatConfig(
    tipo="trs",
    label="Termo de Referência Simplificado",
    marker="[GERAR_TRS]",
    agent_chat_class=TRSChatAgent,
    context_deps=["dfd", "etp"]
)
