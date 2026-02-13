"""
Sistema LIA - Agente TR Conversacional
=======================================
Agente que conversa com o usuário para coletar informações
e gerar o Termo de Referência.

O TR contém 5 campos principais e requer ETP aprovado como base:
1. Definição do Objeto (TR-01)
2. Justificativa e Fundamentação (TR-02)
3. Especificação Técnica (TR-03)
4. Obrigações das Partes (TR-04)
5. Critérios de Aceitação e Pagamento (TR-05)

Autor: Equipe TRE-GO
Data: Fevereiro 2026
"""

import json
from typing import Dict, Any, List, Optional

from .conversational_agent import ConversationalAgent, ChatContext, Message


class TRChatAgent(ConversationalAgent):
    """
    Agente conversacional para Termo de Referência.
    
    Requer contextos de artefatos aprovados:
    - ETP (obrigatório) - Base para especificações
    - DFD (informativo) - Origem da demanda
    - Pesquisa de Preços (valores)
    - PGR (riscos)
    
    Gera os 5 campos obrigatórios do TR:
    1. Definição do objeto
    2. Justificativa e fundamentação
    3. Especificação técnica
    4. Obrigações das partes
    5. Critérios de aceitação e pagamento
    """
    
    agent_type = "tr"
    
    nome_artefato = "TR"
    
    temperature_chat = 0.7
    temperature_generate = 0.4  # Mais preciso para documento formal
    max_tokens_generate = 10000  # TR pode ser extenso
    
    dados_necessarios = [
        "Solução escolhida (do ETP)",
        "Modelo de execução/entrega",
        "Requisitos de qualificação técnica",
        "Níveis de serviço esperados",
        "Responsáveis (gestor e fiscal)",
    ]
    
    campos_tr = [
        "definicao_objeto",
        "justificativa",
        "especificacao_tecnica",
        "obrigacoes",
        "criterios_aceitacao",
    ]

    def __init__(self, model_override: Optional[str] = None, active_skills_instr: str = ""):
        super().__init__(model_override=model_override)
        self.active_skills_instr = active_skills_instr

    def build_chat_system_prompt(self, context: ChatContext) -> str:
        base_prompt = super().build_chat_system_prompt(context)
        if self.active_skills_instr:
            base_prompt += f"\n\n{self.active_skills_instr}"
        return base_prompt

    def build_generate_prompt(self, context: ChatContext, conversa_resumo: str) -> str:
        prompt = super().build_generate_prompt(context, conversa_resumo)
        if self.active_skills_instr:
            prompt += f"\n\n{self.active_skills_instr}"
        return prompt

    def get_mensagem_inicial(self, context: ChatContext) -> str:
        """Mensagem inicial customizada para TR."""
        
        # Verificar se tem ETP aprovado (obrigatório)
        etp_info = ""
        if context.etp:
            solucao = context.etp.get('descricao_solucao', 'solução não especificada')[:100]
            etp_info = f"\n\n✅ **ETP aprovado**: {solucao}..."
        else:
            etp_info = "\n\n⚠️ **Atenção**: Não encontrei ETP aprovado. O TR requer ETP para ser gerado."
        
        # Verificar DFD
        dfd_info = ""
        if context.dfd:
            dfd_info = "\n✅ **DFD disponível**: Justificativa será importada."
        
        # Verificar pesquisa de preços
        preco_info = ""
        if context.pesquisa_precos:
            valor = context.pesquisa_precos.get('valor_total_cotacao', 0)
            if valor:
                preco_info = f"\n💰 **Valor estimado**: R$ {valor:,.2f}"
        
        # Verificar PGR
        pgr_info = ""
        if context.pgr:
            pgr_info = "\n⚠️ **PGR disponível**: Riscos serão considerados."
        
        return f"""👋 Olá! Sou a **LIA**, sua assistente para elaboração do **TR** (Termo de Referência).

📁 Projeto: **{context.projeto_titulo}**{etp_info}{dfd_info}{preco_info}{pgr_info}

O TR define as especificações técnicas e condições para a contratação conforme a Lei 14.133/2021.

💬 **Há algum detalhe específico sobre o modelo de execução** (prazo de entrega, local, forma de suporte) que preciso considerar?

Ou posso iniciar a geração com os dados que já temos?"""

    def build_generate_prompt(self, context: ChatContext, conversa_resumo: str) -> str:
        """Prompt específico para geração do TR."""
        
        itens_pac_str = json.dumps(context.itens_pac, ensure_ascii=False, indent=2) if context.itens_pac else "[]"
        
        # Dados do DFD
        dfd_str = ""
        if context.dfd:
            dfd_str = f"""
DFD APROVADO:
- Objeto: {context.dfd.get('descricao_objeto', 'N/A')}
- Justificativa: {context.dfd.get('justificativa', 'N/A')}
- Alinhamento Estratégico: {context.dfd.get('alinhamento_estrategico', 'N/A')}
"""
        
        # Dados do ETP (mais importante para TR)
        etp_str = ""
        if context.etp:
            etp_str = f"""
ETP APROVADO (BASE PRINCIPAL):
- Descrição da Solução: {context.etp.get('descricao_solucao', 'N/A')}
- Requisitos da Contratação: {context.etp.get('requisitos_contratacao', 'N/A')}
- Estimativa de Quantidades: {context.etp.get('estimativa_quantidades', 'N/A')}
- Levantamento de Mercado: {context.etp.get('levantamento_mercado', 'N/A')[:500] if context.etp.get('levantamento_mercado') else 'N/A'}
- Justificativa de Parcelamento: {context.etp.get('justificativa_parcelamento', 'N/A')}
- Viabilidade: {context.etp.get('viabilidade_contratacao', 'N/A')}
"""
        
        # Dados da Pesquisa de Preços
        preco_str = ""
        if context.pesquisa_precos:
            valor = context.pesquisa_precos.get('valor_total_cotacao', 0)
            preco_str = f"""
PESQUISA DE PREÇOS APROVADA:
- Valor Total Estimado: R$ {valor:,.2f}
- Metodologia: Conforme IN 65/2021
"""
        
        # Dados do PGR
        pgr_str = ""
        if context.pgr:
            pgr_str = f"""
PGR (RISCOS MAPEADOS):
- Riscos de Planejamento: {context.pgr.get('resumo_analise_planejamento', 'N/A')[:300] if context.pgr.get('resumo_analise_planejamento') else 'N/A'}
- Riscos de Gestão: {context.pgr.get('resumo_analise_gestao', 'N/A')[:300] if context.pgr.get('resumo_analise_gestao') else 'N/A'}
"""
        
        return f"""PROJETO: {context.projeto_titulo}
SETOR REQUISITANTE: {context.setor_usuario}

ITENS DO PAC VINCULADOS:
{itens_pac_str}
{dfd_str}{etp_str}{preco_str}{pgr_str}
INFORMAÇÕES ADICIONAIS COLETADAS NA CONVERSA:
{conversa_resumo}

Com base em TODOS os dados acima, gere o TR completo com os 5 campos obrigatórios.

REGRAS:
1. Use os dados do ETP como base principal (solução, requisitos, quantidades)
2. Use os dados do DFD para justificativa
3. Use os valores da Pesquisa de Preços para estimativas
4. Se houver PGR, considere os riscos nas obrigações e critérios
5. Complemente com os detalhes de execução mencionados na conversa
6. Retorne APENAS o JSON válido, sem markdown

SCHEMA DO TR:
{{
  "definicao_objeto": "string (2-3 parágrafos com descrição completa)",
  "justificativa": "string (fundamentação legal e justificativa)",
  "especificacao_tecnica": "string (requisitos detalhados, normas, qualificação)",
  "obrigacoes": "string (obrigações das partes, SLAs, penalidades)",
  "criterios_aceitacao": "string (medição, aceitação, pagamento)"
}}"""
