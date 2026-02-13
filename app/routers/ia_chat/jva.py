"""
Sistema LIA - JVA Chat Config
==============================
Configuração do chat para Justificativa de Vantagem da Adesão.
"""

from ._factory import ArtefactChatConfig
from app.services.agents import JVAChatAgent

config = ArtefactChatConfig(
    tipo="jva",
    label="Justificativa de Vantagem da Adesão",
    marker="[GERAR_JVA]",
    agent_chat_class=JVAChatAgent,
    context_deps=["dfd", "etp", "rdve"]
)
