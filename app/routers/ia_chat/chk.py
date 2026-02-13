"""
CHK Chat Config
===============
Checklist de Instrução (AGU/SEGES) — Verifica conformidade documental.
"""

from app.services.agents.chk_chat_agent import CHKChatAgent
from ._factory import ArtefactChatConfig

config = ArtefactChatConfig(
    tipo="checklist_conformidade",
    label="Checklist de Instrução",
    marker="[GERAR_CHK]",
    agent_chat_class=CHKChatAgent,
    context_deps=["dfd", "etp", "tr", "pgr", "pp"],
    persistido=True,
)
