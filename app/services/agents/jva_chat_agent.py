"""
Sistema LIA - JVA Chat Agent
=============================
Chat conversacional para elaboração de Justificativa de Vantagem e Conveniência da Adesão.

Fluxo: Adesão a Ata de Registro de Preços
Lei 14.133/2021, Art. 37

Autor: Equipe TRE-GO
Data: Fevereiro 2026
"""

from typing import Dict, Any, List, Optional
from .conversational_agent import ConversationalAgent, ChatContext, Message, ChatState


class JVAChatAgent(ConversationalAgent):
    """
    Agente conversacional para Justificativa de Vantagem da Adesão (JVA).
    
    Diferente do RDVE (econômico), a JVA aborda aspectos jurídicos,
    de conveniência administrativa e oportunidade da adesão.
    """
    
    agent_type = "jva"
    
    temperature = 0.6
    
    campos = [
        "fundamentacao_legal",
        "justificativa_conveniencia",
        "declaracao_conformidade"
    ]

    generation_marker = "[GERAR_JVA]"
    
    def construir_prompt_geracao(
        self,
        context: ChatContext,
        history: List[Message],
        extra_instructions: Optional[str] = None
    ) -> str:
        """Constrói prompt para geração da JVA."""
        
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

Com base nas informações, gere Justificativa de Vantagem e Conveniência da Adesão (JVA) tecnicamente fundamentada e juridicamente sólida.

**INSTRUÇÕES:**
1. Cite expressamente Lei 14.133/2021, Art. 37 e parágrafos
2. Fundamente conveniência com argumentos práticos e objetivos
3. Ateste conformidade com limites legais
4. Use linguagem jurídica formal mas clara

Retorne JSON:
{{
    "fundamentacao_legal": "Base jurídica completa com citações...",
    "justificativa_conveniencia": "Argumentação de conveniência e oportunidade...",
    "declaracao_conformidade": "Declaração de conformidade com requisitos legais..."
}}"""
        
        return prompt
