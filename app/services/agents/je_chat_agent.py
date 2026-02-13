"""
Sistema LIA - Agente JE Conversacional
=======================================
Agente que conversa com o usuário para coletar informações
e gerar a Justificativa de Excepcionalidade.

Autor: Equipe TRE-GO
Data: Fevereiro 2026
"""

import json
from typing import Dict, Any, List

from .conversational_agent import ConversationalAgent, ChatContext, Message


class JustificativaExcepcionalidadeChatAgent(ConversationalAgent):
    """
    Agente conversacional para Justificativa de Excepcionalidade.
    
    Coleta informações sobre:
    - Razão da excepcionalidade
    - Fundamento legal
    - Urgência/emergência
    - Impacto da não execução
    - Tipo de contratação
    - Frequência
    - Prioridade
    """
    
    agent_type = "je"
    
    nome_artefato = "Justificativa de Excepcionalidade"
    
    temperature_chat = 0.7
    temperature_generate = 0.6
    
    dados_necessarios = [
        "Razão da excepcionalidade (por que fora do PAC)",
        "Fundamento legal (Lei 14.133/2021)",
        "Justificativa de emergência (se houver)",
        "Impacto da não execução",
        "Tipo de contratação (Serviços/Fornecimento/TI/Obras)",
        "Frequência (Anual/Mensal/Não se aplica)",
        "Prioridade (1-5)",
    ]
    
    campos_je = [
        "descricao",
        "justificativa_legal",
        "justificativa_emergencia",
        "impacto_inexecucao",
        "custo_estimado",
        "cronograma",
        "termos_referencia",
        "tipo_contratacao",
        "frequencia",
        "prioridade",
        "responsavel",
    ]

    def get_mensagem_inicial(self, context: ChatContext) -> str:
        """Mensagem inicial customizada para JE."""
        
        return f"""� **Bem-vindo ao Assistente de Justificativa de Excepcionalidade!**

Sou a **LIA**, sua assistente do TRE-GO para elaboração de Justificativa de Excepcionalidade conforme a **Lei 14.133/2021**.

**📋 Projeto:** {context.projeto_titulo}

**⚖️ Por que estou aqui?**
Esta justificativa permite você contratar **fora do PAC** quando há situações extraordinárias que justificam a excepcionalidade. A Lei 14.133/2021 permite isso em casos específicos e bem fundamentados.

**🎯 O que vamos fazer?**
Vou coletar informações através de uma conversa natural, e juntos vamos:
1. Fundamentar legalmente a excepcionalidade
2. Demonstrar a urgência/emergência (se houver)
3. Explicar o impacto se não executar
4. Definir o tipo e frequência da contratação

**💬 Vamos começar!**
Me conta: **qual é a razão extraordinária para esta contratação ser excepcional?** (O que a torna diferente do planejamento normal?)"""

    def build_generate_prompt(self, context: ChatContext, conversa_resumo: str) -> str:
        """Prompt específico para geração da JE."""
        
        return f"""PROJETO: {context.projeto_titulo}
SETOR REQUISITANTE: {context.setor_usuario}

INFORMAÇÕES COLETADAS NA CONVERSA COM O USUÁRIO:
{conversa_resumo}

Com base nas informações acima, gere a Justificativa de Excepcionalidade completa.

IMPORTANTE:
- Use as informações da conversa para preencher os campos
- A justificativa deve ser formal e demonstrar essencialidade para saída do PAC
- Cite apropriadamente a Lei 14.133/2021
- Se o usuário mencionou tipo de contratação, frequência ou prioridade, use esses dados
- Retorne APENAS o JSON, sem markdown

SCHEMA:
{{
  "descricao": "string",
  "justificativa_legal": "string",
  "justificativa_emergencia": "string ou null",
  "impacto_inexecucao": "string",
  "custo_estimado": "string ou null",
  "cronograma": "string ou null",
  "termos_referencia": "string ou null",
  "tipo_contratacao": "Serviços" | "Fornecimento" | "Tecnologia da Informação" | "Obras",
  "frequencia": "ANUAL" | "MENSAL" | "Não se Aplica",
  "prioridade": 1-5,
  "responsavel": "string ou null"
}}"""
