"""
Pesquisa de Preços Chat Config
==============================
Pesquisa de Preços — Market research artefact.
Note: No dedicated ChatAgent yet, will be created in step 6.
For now, using a placeholder or the base chat agent.
"""

from app.services.agents import ConversationalAgent
from ._factory import ArtefactChatConfig

# Placeholder — will replace with PesquisaPrecosChatAgent when created
config = ArtefactChatConfig(
    tipo="pesquisa_precos",
    label="Pesquisa de Preços",
    marker="[GERAR_PP]",
    agent_chat_class=ConversationalAgent,  # Placeholder
    context_deps=["dfd"],  # Minimal context
    persistido=True,
)
