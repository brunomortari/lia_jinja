"""
Justificativa Excepcionalidade Chat Config
===========================================
Justificativa de Excepcionalidade — Special artefact without DB model.
"""

from app.services.agents import JustificativaExcepcionalidadeChatAgent
from ._factory import ArtefactChatConfig

config = ArtefactChatConfig(
    tipo="justificativa_excepcionalidade",
    label="Justificativa de Excepcionalidade",
    marker="[GERAR_JE]",
    agent_chat_class=JustificativaExcepcionalidadeChatAgent,
    context_deps=["dfd", "pp"],  # Minimal context
    persistido=False,  # Not persisted to DB
)
