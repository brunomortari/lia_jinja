"""
DFD Chat Config
===============
Documento de Formalização da Demanda — Artefato raiz do fluxo.
"""

from app.services.agents import DFDChatAgent
from ._factory import ArtefactChatConfig

config = ArtefactChatConfig(
    tipo="dfd",
    label="Documento de Formalização da Demanda",
    marker="[GERAR_DFD]",
    agent_chat_class=DFDChatAgent,
    context_deps=["dfd", "pp"],  # Load DFD (if editing) + prices
    persistido=True,
)
