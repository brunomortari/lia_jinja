"""
Sistema LIA - RDVE Chat Config
===============================
Configuração do chat para Relatório de Vantagem Econômica (Adesão a Ata).
"""

from ._factory import ArtefactChatConfig
from app.services.agents import RDVEChatAgent

config = ArtefactChatConfig(
    tipo="rdve",
    label="Relatório de Vantagem Econômica",
    marker="[GERAR_RDVE]",
    agent_chat_class=RDVEChatAgent,
    context_deps=["dfd", "etp"]
)
