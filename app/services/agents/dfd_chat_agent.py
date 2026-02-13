"""
Sistema LIA - Agente DFD Conversacional
=======================================
Agente que conversa com o usuário para coletar informações
e gerar o Documento de Formalização da Demanda.

Autor: Equipe TRE-GO
Data: Fevereiro 2026
"""

import json
from typing import Dict, Any, List

from .conversational_agent import ConversationalAgent, ChatContext, Message


class DFDChatAgent(ConversationalAgent):
    """
    Agente conversacional para Documento de Formalização da Demanda.
    
    Coleta informações sobre:
    - Necessidade/problema a resolver
    - Objetivo da contratação
    - Urgência/prazo desejado
    - Gestor e fiscal sugeridos
    """
    
    agent_type = "dfd"
    
    nome_artefato = "DFD"
    
    temperature_chat = 0.7
    temperature_generate = 0.6
    
    dados_necessarios = [
        "Descrição da necessidade/problema a resolver",
        "Objetivo da contratação",
        "Alinhamento com itens do PAC",
        "Prazo/urgência (se houver)",
        "Gestor sugerido (opcional)",
        "Fiscal sugerido (opcional)",
    ]
    
    campos_dfd = [
        "justificativa_tecnica",
        "descricao_objeto_padronizada",
        "id_item_pca",
        "prioridade_sugerida",
        "analise_alinhamento",
        "data_pretendida",
        "responsavel_gestor",
        "responsavel_fiscal",
    ]

    def get_mensagem_inicial(self, context: ChatContext) -> str:
        """Mensagem inicial customizada para DFD."""

        # Construir info sobre itens PAC
        pac_info = ""
        if context.itens_pac:
            if len(context.itens_pac) == 1:
                item = context.itens_pac[0]
                desc = item.get('descricao', item.get('objeto', 'Item'))[:80]
                pac_info = f"\n\n📋 Item do PAC vinculado: **{desc}**"
            else:
                pac_info = f"\n\n📋 **{len(context.itens_pac)} itens do PAC** já vinculados a este projeto."

        return f"""👋 Olá! Sou a **LIA**, sua assistente para elaboração do **DFD**.

📁 Projeto: **{context.projeto_titulo}**{pac_info}

Vou te ajudar a criar um documento completo e bem fundamentado conforme a Lei 14.133/2021.

💬 **Para começar, me conta: qual problema ou necessidade motivou essa contratação?**"""

    def build_generate_prompt(self, context: ChatContext, conversa_resumo: str) -> str:
        """Prompt específico para geração do DFD."""
        
        itens_pac_str = json.dumps(context.itens_pac, ensure_ascii=False, indent=2)
        
        return f"""PROJETO: {context.projeto_titulo}
SETOR REQUISITANTE: {context.setor_usuario}

ITENS DO PAC VINCULADOS:
{itens_pac_str}

INFORMAÇÕES COLETADAS NA CONVERSA COM O USUÁRIO:
{conversa_resumo}

Com base nas informações acima, gere o DFD completo.

IMPORTANTE:
- Use as informações da conversa para preencher os campos
- A justificativa deve ser formal e demonstrar essencialidade
- Se o usuário mencionou prazo, use em data_pretendida
- Se mencionou nomes para gestor/fiscal, use nos campos apropriados
- Alinhe o id_item_pca com o item mais relevante do PAC fornecido
- Retorne APENAS o JSON, sem markdown

SCHEMA:
{{
  "justificativa_tecnica": "string",
  "descricao_objeto_padronizada": "string", 
  "id_item_pca": number,
  "prioridade_sugerida": "Alta" | "Média" | "Baixa",
  "analise_alinhamento": "string",
  "data_pretendida": "string ou null",
  "responsavel_gestor": "string ou null",
  "responsavel_fiscal": "string ou null"
}}"""
