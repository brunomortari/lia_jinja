"""
Sistema LIA - JPEF Chat Agent
==============================
Chat conversacional para Justificativa de Preço e Escolha de Fornecedor.

Fluxo: Dispensa por Valor Baixo
Lei 14.133/2021, Art. 75

Autor: Equipe TRE-GO
Data: Fevereiro 2026
"""

from typing import Dict, Any, List, Optional
from .conversational_agent import ConversationalAgent, ChatContext, Message, ChatState


class JPEFChatAgent(ConversationalAgent):
    """
    Agente conversacional para Justificativa de Preço e Escolha de Fornecedor (JPEF).
    
    Fundamenta a escolha do fornecedor e demonstra que o preço é vantajoso
    para dispensas por valor baixo.
    """
    
    agent_type = "jpef"
    
    temperature = 0.5
    
    campos = [
        "justificativa_fornecedor",
        "analise_preco_praticado",
        "preco_final_contratacao"
    ]

    generation_marker = "[GERAR_JPEF]"
    
    def construir_prompt_geracao(
        self,
        context: ChatContext,
        history: List[Message],
        extra_instructions: Optional[str] = None
    ) -> str:
        """Constrói prompt para geração da JPEF."""
        
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

Gere Justificativa de Preço e Escolha de Fornecedor (JPEF) fundamentada.

**INSTRUÇÕES:**
1. Justifique escolha do fornecedor com critérios objetivos
2. Demonstre que preço é competitivo/vantajoso com comparações
3. Cite fontes de pesquisa de preço (cotações, tabelas, contratos)
4. Valor final deve estar alinhado com mercado
5. Use linguagem técnica mas clara

Retorne JSON:
{{
    "justificativa_fornecedor": "Fundamentação da escolha do fornecedor...",
    "analise_preco_praticado": "Análise comparativa de preço com fontes...",
    "preco_final_contratacao": "R$ X.XXX,XX"
}}"""
        
        return prompt
