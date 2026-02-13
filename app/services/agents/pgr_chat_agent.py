"""
Sistema LIA - Agente PGR Conversacional
=======================================
Agente que conversa com o usuario para coletar informacoes
e gerar o Plano de Gerenciamento de Riscos (PGR).

O PGR analisa riscos em 3 fases:
- Planejamento
- Selecao de Fornecedor
- Gestao Contratual

Autor: Equipe TRE-GO
Data: Fevereiro 2026
"""

import json
from typing import Dict, Any, List, Optional

from .conversational_agent import ConversationalAgent, ChatContext, Message


class PGRChatAgent(ConversationalAgent):
    """
    Agente conversacional para Plano de Gerenciamento de Riscos.

    Coleta informacoes sobre:
    - Areas de preocupacao especificas
    - Prazo desejado para a contratacao
    - Historico de problemas em contratacoes similares
    - Focos de risco prioritarios
    """

    agent_type = "pgr"

    nome_artefato = "PGR"

    temperature_chat = 0.7
    temperature_generate = 0.4  # Mais conservador para analise de riscos

    dados_necessarios = [
        "Areas de preocupacao especificas (ex: prazo, fornecedores, tecnologia)",
        "Prazo desejado para a contratacao",
        "Historico de problemas em contratacoes similares (se houver)",
        "Focos de risco prioritarios",
        "Equipe responsavel pelo monitoramento (opcional)",
    ]

    campos_pgr = [
        "identificacao_objeto",
        "valor_estimado_total",
        "metodologia_adotada",
        "data_revisao",
        "resumo_analise_planejamento",
        "resumo_analise_selecao",
        "resumo_analise_gestao",
        "itens_risco",
    ]

    def get_mensagem_inicial(self, context: ChatContext) -> str:
        """Mensagem inicial customizada para PGR."""

        # Info sobre DFD aprovado
        dfd_info = ""
        if context.dfd:
            desc = context.dfd.get('descricao_objeto', context.dfd.get('descricao_objeto_padronizada', ''))
            if desc:
                dfd_info = f"\n\n**DFD Aprovado:** {desc[:100]}..."

        # Info sobre cotacoes
        cotacao_info = ""
        if context.pesquisa_precos:
            valor = context.pesquisa_precos.get('valor_total_cotacao', context.pesquisa_precos.get('valor_total', 0))
            if valor:
                cotacao_info = f"\n**Valor Estimado:** R$ {valor:,.2f}"

        return f"""Ola! Sou a **LIA-RISK**, sua assistente para elaboracao do **Plano de Gerenciamento de Riscos**.

Projeto: **{context.projeto_titulo}**{dfd_info}{cotacao_info}

Vou te ajudar a identificar e planejar a gestao de riscos desta contratacao conforme a Lei 14.133/2021.

**Para comecar: quais areas mais te preocupam nesta contratacao?**
(Ex: prazo de entrega, disponibilidade de fornecedores, complexidade tecnica, orcamento)"""

    def build_chat_system_prompt(self, context: ChatContext) -> str:
        """
        Constroi o system prompt para o modo chat.
        Inclui contexto do projeto, DFD e cotacoes aprovados.
        """
        checklist = "\n".join([f"- {item}" for item in self.dados_necessarios])

        base_prompt = f"""{self.system_prompt_chat}

CONTEXTO DO PROJETO:
- ID: {context.projeto_id}
- Titulo: {context.projeto_titulo}
- Setor: {context.setor_usuario}
- Itens PAC: {len(context.itens_pac)} itens
"""

        # Adicionar contexto do DFD aprovado
        if context.dfd:
            base_prompt += f"""
DADOS DO DFD APROVADO (use como base para riscos):
- Objeto: {context.dfd.get('descricao_objeto', context.dfd.get('descricao_objeto_padronizada', 'N/A'))}
- Justificativa: {context.dfd.get('justificativa', context.dfd.get('justificativa_tecnica', 'N/A'))[:200]}...
"""

        # Adicionar contexto das cotacoes aprovadas
        if context.pesquisa_precos:
            valor = context.pesquisa_precos.get('valor_total_cotacao', context.pesquisa_precos.get('valor_total', 0))
            qtd_forn = context.pesquisa_precos.get('quantidade_fornecedores', 0)
            cv = context.pesquisa_precos.get('coeficiente_variacao', 0)

            base_prompt += f"""
DADOS DA PESQUISA DE PRECOS APROVADA:
- Valor Total: R$ {valor:,.2f}
- Fornecedores: {qtd_forn}
- Coeficiente de Variacao: {cv:.1f}%
"""
            # Alertas automaticos
            if cv > 25:
                base_prompt += "- ALERTA: CV alto indica volatilidade de mercado!\n"
            if qtd_forn < 3:
                base_prompt += "- ALERTA: Poucos fornecedores - risco de licitacao deserta!\n"

        # Dados ja coletados (formulario preenchido pelo usuario)
        if context.dados_coletados:
            base_prompt += "\n\nDADOS JA INFORMADOS PELO USUARIO (NAO PERGUNTE NOVAMENTE):"
            if context.dados_coletados.get('areas_preocupacao'):
                base_prompt += f"\n- Areas de preocupacao: {context.dados_coletados['areas_preocupacao']}"
            if context.dados_coletados.get('prazo_desejado'):
                base_prompt += f"\n- Prazo desejado: {context.dados_coletados['prazo_desejado']}"
            if context.dados_coletados.get('historico_problemas'):
                base_prompt += f"\n- Historico de problemas: {context.dados_coletados['historico_problemas']}"
            if context.dados_coletados.get('equipe_responsavel'):
                base_prompt += f"\n- Equipe responsavel: {context.dados_coletados['equipe_responsavel']}"

        base_prompt += f"""

DADOS IMPORTANTES A COLETAR:
{checklist}

INSTRUCOES:
1. Converse naturalmente para coletar as preocupacoes do usuario
2. Use os dados do DFD e cotacoes que ja temos no contexto - NAO pergunte sobre eles!
3. ASSIM QUE o usuario mencionar 1+ areas de preocupacao, IMEDIATAMENTE:
   - Faca um resumo breve
   - Adicione [GERAR_PGR] ao final da mensagem
4. Se o usuario pedir "gerar", "criar", "fazer o PGR", adicione [GERAR_PGR] imediatamente
5. NUNCA mencione JSON, schemas ou formatos tecnicos
6. Seja conciso - 2-3 mensagens no maximo antes de mostrar [GERAR_PGR]"""

        return base_prompt

    def build_generate_prompt(self, context: ChatContext, conversa_resumo: str) -> str:
        """Prompt especifico para geracao do PGR."""

        itens_pac_str = json.dumps(context.itens_pac, ensure_ascii=False, indent=2) if context.itens_pac else "[]"

        # Dados do DFD
        dfd_str = "Nenhum DFD aprovado disponivel."
        if context.dfd:
            dfd_str = f"""
- Objeto: {context.dfd.get('descricao_objeto', context.dfd.get('descricao_objeto_padronizada', 'N/A'))}
- Justificativa: {context.dfd.get('justificativa', context.dfd.get('justificativa_tecnica', 'N/A'))}
"""

        # Dados das cotacoes
        cotacao_str = "Nenhuma cotacao aprovada disponivel."
        if context.pesquisa_precos:
            valor = context.pesquisa_precos.get('valor_total_cotacao', context.pesquisa_precos.get('valor_total', 0))
            qtd_forn = context.pesquisa_precos.get('quantidade_fornecedores', 0)
            cv = context.pesquisa_precos.get('coeficiente_variacao', 0)
            cotacao_str = f"""
- Valor Total: R$ {valor:,.2f}
- Quantidade de Fornecedores: {qtd_forn}
- Coeficiente de Variacao: {cv:.1f}%
"""

        # Valor estimado
        valor_estimado = 0.0
        if context.pesquisa_precos:
            valor_estimado = context.pesquisa_precos.get('valor_total_cotacao', context.pesquisa_precos.get('valor_total', 0))

        return f"""PROJETO: {context.projeto_titulo}
SETOR REQUISITANTE: {context.setor_usuario}
VALOR ESTIMADO: R$ {valor_estimado:,.2f}

ITENS DO PAC VINCULADOS:
{itens_pac_str}

DADOS DO DFD APROVADO:
{dfd_str}

DADOS DA PESQUISA DE PRECOS APROVADA:
{cotacao_str}

INFORMACOES COLETADAS NA CONVERSA COM O USUARIO:
{conversa_resumo}

Com base nas informacoes acima, gere o PGR completo.

IMPORTANTE:
- Use as preocupacoes mencionadas pelo usuario para priorizar riscos
- Se houver CV alto nas cotacoes, inclua risco de volatilidade de mercado
- Se houver poucos fornecedores, inclua risco de licitacao deserta
- Se o usuario mencionou problemas anteriores, use como base para riscos
- Gere entre 5-10 riscos bem fundamentados
- Distribua riscos entre as 3 fases
- Retorne APENAS o JSON, sem markdown

SCHEMA:
{{
  "identificacao_objeto": "string",
  "valor_estimado_total": number,
  "metodologia_adotada": "Matriz 5x5 (Probabilidade vs Impacto)",
  "data_revisao": "YYYY-MM-DD",
  "resumo_analise_planejamento": "string",
  "resumo_analise_selecao": "string",
  "resumo_analise_gestao": "string",
  "itens_risco": [
    {{
      "origem": "DFD | Cotacao | PAC | Externo",
      "fase_licitacao": "Planejamento | Selecao_Fornecedor | Gestao_Contratual",
      "categoria": "Tecnico | Administrativo | Juridico | Economico | Reputacional",
      "evento": "string",
      "causa": "string",
      "consequencia": "string",
      "probabilidade": number (1-5),
      "impacto": number (1-5),
      "justificativa_probabilidade": "string",
      "justificativa_impacto": "string",
      "tipo_tratamento": "Mitigar | Transferir | Aceitar | Evitar",
      "acoes_preventivas": "string",
      "acoes_contingencia": "string",
      "alocacao_responsavel": "Contratante | Contratada | Compartilhado",
      "gatilho_monitoramento": "string",
      "responsavel_monitoramento": "string",
      "frequencia_monitoramento": "Semanal | Quinzenal | Mensal | Trimestral"
    }}
  ]
}}"""
