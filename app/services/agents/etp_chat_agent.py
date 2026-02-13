"""
Sistema LIA - Agente ETP Conversacional
=======================================
Agente que conversa com o usuário para coletar informações
e gerar o Estudo Técnico Preliminar.

O ETP contém 15 campos obrigatórios conforme Lei 14.133/2021, art. 18, §1º
e IN SEGES/ME nº 58/2022.

Autor: Equipe TRE-GO
Data: Fevereiro 2026
"""

import json
from typing import Dict, Any, List, Optional

from .conversational_agent import ConversationalAgent, ChatContext, Message


class ETPChatAgent(ConversationalAgent):
    """
    Agente conversacional para Estudo Técnico Preliminar.
    
    Requer contextos de artefatos aprovados:
    - DFD (obrigatório)
    - Pesquisa de Preços (valores)
    - PGR (riscos)
    
    Gera os 15 campos obrigatórios do ETP:
    1. Descrição da necessidade (ETP-01)
    2. Área requisitante (ETP-02)
    3. Requisitos da contratação (ETP-03)
    4. Estimativa de quantidades (ETP-04)
    5. Levantamento de mercado (ETP-05)
    6. Estimativa do valor (ETP-06)
    7. Descrição da solução (ETP-07)
    8. Parcelamento do objeto (ETP-08)
    9. Contratações correlatas (ETP-09)
    10. Alinhamento ao PCA (ETP-10)
    11. Resultados pretendidos (ETP-11)
    12. Providências prévias (ETP-12)
    13. Impactos ambientais (ETP-13)
    14. Análise de riscos (ETP-14)
    15. Viabilidade da contratação (ETP-15)
    """
    
    agent_type = "etp"
    
    nome_artefato = "ETP"
    
    temperature_chat = 0.7
    temperature_generate = 0.5
    max_tokens_generate = 12000  # ETP é mais extenso
    
    dados_necessarios = [
        "Entendimento da necessidade (já deve estar no DFD)",
        "Requisitos técnicos específicos",
        "Exigências de qualificação ou certificação",
        "Cenários de mercado considerados",
        "Justificativa da solução escolhida",
        "Providências prévias necessárias",
    ]
    
    campos_etp = [
        "descricao_necessidade",
        "area_requisitante",
        "requisitos_contratacao",
        "estimativa_quantidades",
        "levantamento_mercado",
        "estimativa_valor",
        "descricao_solucao",
        "justificativa_parcelamento",
        "contratacoes_correlatas",
        "alinhamento_pca",
        "resultados_pretendidos",
        "providencias_previas",
        "impactos_ambientais",
        "analise_riscos",
        "viabilidade_contratacao",
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
        """Mensagem inicial customizada para ETP."""
        
        # Verificar se tem DFD aprovado
        dfd_info = ""
        if context.dfd:
            descricao = context.dfd.get('descricao_objeto', 'objeto não especificado')[:100]
            dfd_info = f"\n\n✅ **DFD aprovado**: {descricao}..."
        else:
            dfd_info = "\n\n⚠️ **Atenção**: Não encontrei DFD aprovado. Recomendo aprovar o DFD antes de gerar o ETP."
        
        # Verificar pesquisa de preços
        preco_info = ""
        if context.pesquisa_precos:
            valor = context.pesquisa_precos.get('valor_total_cotacao', 0)
            if valor:
                preco_info = f"\n💰 **Valor estimado**: R$ {valor:,.2f}"
        
        # Verificar PGR
        pgr_info = ""
        if context.pgr:
            pgr_info = "\n⚠️ **PGR disponível**: Riscos já mapeados serão incluídos."
        
        return f"""👋 Olá! Sou a **LIA**, sua assistente para elaboração do **ETP** (Estudo Técnico Preliminar).

📁 Projeto: **{context.projeto_titulo}**{dfd_info}{preco_info}{pgr_info}

O ETP fundamenta tecnicamente a contratação conforme a Lei 14.133/2021. Vou usar os dados do DFD e Pesquisa de Preços como base.

💬 **Há algum requisito técnico específico** (certificações, normas, qualificações) que preciso considerar? 

Ou posso iniciar a geração com os dados que já temos?"""

    def build_generate_prompt(self, context: ChatContext, conversa_resumo: str) -> str:
        """Prompt específico para geração do ETP."""
        
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
{json.dumps(context.pgr, ensure_ascii=False, indent=2)}
"""
        
        return f"""PROJETO: {context.projeto_titulo}
SETOR REQUISITANTE: {context.setor_usuario}

ITENS DO PAC VINCULADOS:
{itens_pac_str}
{dfd_str}{preco_str}{pgr_str}
INFORMAÇÕES ADICIONAIS COLETADAS NA CONVERSA:
{conversa_resumo}

Com base em TODOS os dados acima, gere o ETP completo com os 15 campos obrigatórios.

REGRAS:
1. Use os dados do DFD como base para descricao_necessidade
2. Use os valores da Pesquisa de Preços para estimativa_valor
3. Se houver PGR, use para analise_riscos
4. Complemente com os requisitos técnicos mencionados na conversa
5. Retorne APENAS o JSON válido, sem markdown, sem backticks
6. IMPORTANTE: Escape todos os caracteres especiais (quebras de linha devem ser \\n, aspas como \\")

SCHEMA DO ETP:
{{
  "descricao_necessidade": "string (2-3 parágrafos com quebras de linha como \\\\n)",
  "area_requisitante": "string",
  "requisitos_contratacao": "string (incluir normas técnicas)",
  "estimativa_quantidades": "string (memória de cálculo)",
  "levantamento_mercado": "string (análise comparativa)",
  "estimativa_valor": "string (valor e metodologia)",
  "descricao_solucao": "string",
  "justificativa_parcelamento": "string (Súmula 247 TCU)",
  "contratacoes_correlatas": "string ou null",
  "alinhamento_pca": "string",
  "resultados_pretendidos": "string",
  "providencias_previas": "string ou null",
  "impactos_ambientais": "string (sustentabilidade)",
  "analise_riscos": "string (do PGR ou análise geral)",
  "viabilidade_contratacao": "string (parecer final)"
}}"""
