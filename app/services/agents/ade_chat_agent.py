"""
Sistema LIA - ADE Chat Agent
=============================
Chat conversacional para elaboração de Aviso de Dispensa Eletrônica.

Fluxo: Dispensa por Valor Baixo
Lei 14.133/2021, Art. 75

Autor: Equipe TRE-GO
Data: Fevereiro 2026
"""

from typing import Dict, Any, List, Optional
from .conversational_agent import ConversationalAgent, ChatContext, Message, ChatState


class ADEChatAgent(ConversationalAgent):
    """
    Agente conversacional para Aviso de Dispensa Eletrônica (ADE).
    
    Prepara dados para publicação de aviso de dispensa em portal eletrônico,
    conforme exigência de transparência da Lei 14.133/2021.
    """
    
    agent_type = "ade"
    
    temperature = 0.4
    
    campos = [
        "numero_aviso",
        "data_publicacao",
        "descricao_objeto",
        "link_portal_publicacao",
        "protocolo_publicacao"
    ]

    generation_marker = "[GERAR_ADE]"
    
    def construir_prompt_geracao(
        self,
        context: ChatContext,
        history: List[Message],
        extra_instructions: Optional[str] = None
    ) -> str:
        """Constrói prompt para geração do ADE."""
        
        projeto_info = f"""
**PROJETO:** {context.projeto_titulo}
**SETOR:** {context.setor_usuario}
"""
        
        # Buscar TRS no contexto se disponível
        trs_info = ""
        if hasattr(context, 'trs_aprovados') and context.trs_aprovados:
            trs_info = f"\n**TRS APROVADO:** {context.trs_aprovados[0].get('especificacao_objeto', '')}"
        
        conversacao = "\n".join([
            f"{'Usuário' if msg.role == 'user' else 'Assistente'}: {msg.content}"
            for msg in history
        ])
        
        prompt = f"""{self.system_prompt}

{projeto_info}{trs_info}

**HISTÓRICO DA CONVERSA:**
{conversacao}

{extra_instructions or ''}

Gere Aviso de Dispensa Eletrônica (ADE) pronto para publicação.

**INSTRUÇÕES:**
1. Gere número de aviso no padrão institucional
2. Use data de hoje + 1 dia útil como data de publicação
3. Descrição objetiva e clara do objeto
4. Indique portal correto de publicação
5. Campo protocolo pode ficar vazio (preenchido após publicação)

Retorne JSON:
{{
    "numero_aviso": "XXX/2026-SETOR",
    "data_publicacao": "DD/MM/AAAA",
    "descricao_objeto": "Resumo objetivo...",
    "link_portal_publicacao": "https://...",
    "protocolo_publicacao": ""
}}"""
        
        return prompt
