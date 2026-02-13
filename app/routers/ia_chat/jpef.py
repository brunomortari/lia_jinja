"""
Sistema LIA - JPEF Chat Config
===============================
Configuração do chat para Justificativa de Preço e Escolha de Fornecedor.
"""

from ._factory import ArtefactChatConfig
from app.services.agents import JPEFChatAgent

config = ArtefactChatConfig(
    tipo="jpef",
    label="Justificativa de Preço e Escolha de Fornecedor",
    marker="[GERAR_JPEF]",
    agent_chat_class=JPEFChatAgent,
    context_deps=["dfd", "etp", "trs", "ade"]
)
