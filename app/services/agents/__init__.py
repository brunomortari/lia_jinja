"""
Sistema LIA - Agentes de IA
===========================
Módulos de geração de artefatos usando OpenAI SDK + OpenRouter.

Cada agente é especializado em um tipo de artefato:
- DFD: Documento de Formalização da Demanda
- ETP: Estudo Técnico Preliminar
- PGR: Plano de Gerenciamento de Riscos
- TR: Termo de Referência
- Edital: Edital de Licitação

Agentes Conversacionais:
- DFDChatAgent: Chat para coleta de dados e geração de DFD
- ETPChatAgent: Chat para elaboração de ETP
- PGRChatAgent: Chat para análise de riscos
- TRChatAgent: Chat para elaboração de TR

Infraestrutura:
- PromptLoader: Carrega prompts do banco de dados
- ContextBuilder: Constrói blocos de contexto compartilhados

Autor: Equipe TRE-GO
Data: Janeiro 2026
"""

from .base_agent import BaseAgent
from .conversational_agent import ConversationalAgent, ChatContext, Message, ChatState
from .prompt_loader import PromptLoader, load_prompt_cached, clear_prompt_cache
from .context_builder import ContextBuilder
from .dfd_agent import DFDAgent
from .dfd_chat_agent import DFDChatAgent
from .etp_agent import ETPAgent
from .etp_chat_agent import ETPChatAgent
from .pgr_agent import PGRAgent
from .pgr_chat_agent import PGRChatAgent
from .tr_agent import TRAgent
from .tr_chat_agent import TRChatAgent
from .edital_agent import EditalAgent
from .ed_chat_agent import EditalChatAgent
from .je_agent import JustificativaExcepcionalidadeAgent
from .je_chat_agent import JustificativaExcepcionalidadeChatAgent
from .chk_chat_agent import CHKChatAgent

# Agents de fluxos alternativos (Adesão Ata + Dispensa Valor)
from .rdve_agent import RDVEAgent
from .jva_agent import JVAAgent
from .trs_agent import TRSAgent
from .ade_agent import ADEAgent
from .jpef_agent import JPEFAgent
from .ce_agent import CEAgent

# Chat Agents de fluxos alternativos
from .rdve_chat_agent import RDVEChatAgent
from .jva_chat_agent import JVAChatAgent
from .trs_chat_agent import TRSChatAgent
from .ade_chat_agent import ADEChatAgent
from .jpef_chat_agent import JPEFChatAgent

__all__ = [
    "BaseAgent",
    "ConversationalAgent",
    "ChatContext",
    "Message",
    "ChatState",
    "PromptLoader",
    "load_prompt_cached",
    "clear_prompt_cache",
    "ContextBuilder",
    "DFDAgent",
    "DFDChatAgent",
    "ETPAgent",
    "ETPChatAgent",
    "PGRAgent",
    "PGRChatAgent",
    "TRAgent",
    "TRChatAgent",
    "EditalAgent",
    "EditalChatAgent",
    "JustificativaExcepcionalidadeAgent",
    "JustificativaExcepcionalidadeChatAgent",
    "CHKChatAgent",
    # Fluxos alternativos - Generation
    "RDVEAgent",
    "JVAAgent",
    "TRSAgent",
    "ADEAgent",
    "JPEFAgent",
    "CEAgent",
    # Fluxos alternativos - Chat
    "RDVEChatAgent",
    "JVAChatAgent",
    "TRSChatAgent",
    "ADEChatAgent",
    "JPEFChatAgent",
]
