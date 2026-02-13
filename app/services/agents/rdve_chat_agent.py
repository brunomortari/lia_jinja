"""
Sistema LIA - RDVE Chat Agent
==============================
Chat conversacional para elaboração de Relatório de Vantagem Econômica (Adesão a Ata).

Fluxo: Adesão a Ata de Registro de Preços
Lei 14.133/2021, Art. 37

Autor: Equipe TRE-GO
Data: Fevereiro 2026
"""

from typing import Dict, Any, List, Optional
from .conversational_agent import ConversationalAgent, ChatContext, Message, ChatState


class RDVEChatAgent(ConversationalAgent):
    """
    Agente conversacional para elaboração de Relatório de Vantagem Econômica.
    
    Conduz o usuário através das etapas de análise comparativa de preços
    entre adesão a ata e contratação direta.
    """
    
    agent_type = "rdve"
    
    temperature = 0.5
    
    campos = [
        "comparativo_precos",
        "custo_processamento_adesao",
        "custo_processamento_direto",
        "conclusao_tecnica",
        "percentual_economia",
        "valor_economia_total"
    ]

    generation_marker = "[GERAR_RDVE]"
    
    def construir_prompt_geracao(
        self,
        context: ChatContext,
        history: List[Message],
        extra_instructions: Optional[str] = None
    ) -> str:
        """Constrói prompt para geração do RDVE baseado no histórico do chat."""
        
        # Extrair contexto do projeto
        projeto_info = f"""
**PROJETO:** {context.projeto_titulo}
**SETOR:** {context.setor_usuario}
"""
        
        # Construir resumo das informações coletadas
        conversacao = "\n".join([
            f"{'Usuário' if msg.role == 'user' else 'Assistente'}: {msg.content}"
            for msg in history
        ])
        
        prompt = f"""{self.system_prompt}

{projeto_info}

**HISTÓRICO DA CONVERSA:**
{conversacao}

{extra_instructions or ''}

Com base nas informações coletadas, gere um Relatório de Vantagem Econômica (RDVE) completo e tecnicamente fundamentado.

**INSTRUÇÕES DE GERAÇÃO:**
1. Preencha TODOS os campos obrigatórios
2. Use valores monetários reais informados pelo usuário
3. Calcule corretamente percentual de economia
4. Fundamente a conclusão técnica com dados numéricos
5. Seja claro e objetivo - documento será anexado ao processo licitatório

Retorne APENAS um objeto JSON válido com a seguinte estrutura:
{{
    "comparativo_precos": "Tabela comparativa detalhada...",
    "custo_processamento_adesao": "R$ X.XXX,XX - Detalhamento...",
    "custo_processamento_direto": "R$ X.XXX,XX - Detalhamento...",
    "conclusao_tecnica": "Análise conclusiva fundamentada...",
    "percentual_economia": "XX.X%",
    "valor_economia_total": "R$ X.XXX,XX"
}}"""
        
        return prompt
