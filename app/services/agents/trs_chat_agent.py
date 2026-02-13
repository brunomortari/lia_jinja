"""
Sistema LIA - TRS Chat Agent
=============================
Chat conversacional para elaboração de Termo de Referência Simplificado.

Fluxo: Dispensa por Valor Baixo
Lei 14.133/2021, Art. 75

Autor: Equipe TRE-GO
Data: Fevereiro 2026
"""

from typing import Dict, Any, List, Optional
from .conversational_agent import ConversationalAgent, ChatContext, Message, ChatState


class TRSChatAgent(ConversationalAgent):
    """
    Agente conversacional para Termo de Referência Simplificado (TRS).
    
    Versão reduzida do TR completo, adequada para dispensas por valor baixo.
    Foco em especificação objetiva sem excesso de formalismo.
    """
    
    agent_type = "trs"
    
    temperature = 0.5
    
    campos = [
        "especificacao_objeto",
        "criterios_qualidade_simplificados",
        "prazos_entrega",
        "valor_referencia_dispensa",
        "justificativa_dispensa"
    ]

    generation_marker = "[GERAR_TRS]"
    
    def construir_prompt_geracao(
        self,
        context: ChatContext,
        history: List[Message],
        extra_instructions: Optional[str] = None
    ) -> str:
        """Constrói prompt para geração do TRS."""
        
        projeto_info = f"""
**PROJETO:** {context.projeto_titulo}
**SETOR:** {context.setor_usuario}
"""
        
        conversacao = "\n".join([
            f"{'Usuário' if msg.role == 'user' else 'Assistente'}: {msg.content}"
            for msg in history
        ])
        
        prompt = f"""{self.system_prompt}

{projeto_info}

**HISTÓRICO DA CONVERSA:**
{conversacao}

{extra_instructions or ''}

Gere Termo de Referência Simplificado (TRS) objetivo e tecnicamente adequado.

**INSTRUÇÕES:**
1. Especificação técnica clara mas sem excesso de detalhes
2. Critérios de qualidade verificáveis objetivamente
3. Prazo realista de entrega/execução
4. Confirme que valor está dentro do limite de dispensa
5. Cite Lei 14.133/2021, Art. 75, inciso II

Retorne JSON:
{{
    "especificacao_objeto": "Descrição objetiva do objeto...",
    "criterios_qualidade_simplificados": "Critérios mínimos de aceitação...",
    "prazos_entrega": "Prazo de entrega/execução...",
    "valor_referencia_dispensa": "R$ X.XXX,XX",
    "justificativa_dispensa": "Fundamentação legal Art. 75, II..."
}}"""
        
        return prompt
