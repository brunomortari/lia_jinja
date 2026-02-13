"""
Sistema LIA - Agente Edital Conversacional
==========================================
Agente que conversa com o usuário para coletar informações
e gerar o Edital de Licitação.

Contexto utilizado: DFD, Cotações, PGR, ETP e TR aprovados.

Autor: Equipe TRE-GO
Data: Fevereiro 2026
"""

import json
from typing import Dict, Any, List

from .conversational_agent import ConversationalAgent, ChatContext, Message


class EditalChatAgent(ConversationalAgent):
    """
    Agente conversacional para Edital de Licitação.

    Coleta informações sobre:
    - Modalidade desejada (Pregão, Concorrência, etc)
    - Tipo de disputa (aberto, fechado, combinado)
    - Prazos específicos (se diferentes do padrão)
    - Critérios adicionais de julgamento
    - Requisitos específicos de habilitação
    """

    agent_type = "edital"

    nome_artefato = "Edital"

    temperature_chat = 0.7
    temperature_generate = 0.4  # Mais conservador para documento jurídico

    dados_necessarios = [
        "Modalidade de licitação (Pregão Eletrônico é padrão)",
        "Tipo de disputa (aberto, fechado ou combinado)",
        "Critério de julgamento (menor preço, melhor técnica, etc)",
        "Requisitos específicos de habilitação (se houver)",
        "Prazos diferenciados (se houver necessidade)",
        "Condições especiais de participação",
    ]

    campos_edital = [
        "objeto",
        "condicoes_participacao",
        "criterios_julgamento",
        "fase_lances",
        # Campos estruturados do schema completo
        "preambulo",
        "prazos",
        "sistema_eletronico",
        "proposta",
        "sessao_publica",
        "recursos",
        "penalidades",
        "pagamento",
        "anexos",
        "disposicoes_finais",
    ]

    def get_mensagem_inicial(self, context: ChatContext) -> str:
        """Mensagem inicial customizada para Edital."""

        # Verificar artefatos disponíveis
        artefatos_disponiveis = []
        if context.dfd:
            artefatos_disponiveis.append("DFD")
        if context.pesquisa_precos:
            artefatos_disponiveis.append("Cotações")
        if context.pgr:
            artefatos_disponiveis.append("PGR")
        if context.etp:
            artefatos_disponiveis.append("ETP")
        if context.tr:
            artefatos_disponiveis.append("TR")

        artefatos_str = ", ".join(artefatos_disponiveis) if artefatos_disponiveis else "Nenhum"

        # Valor estimado
        valor_str = ""
        if context.pesquisa_precos and context.pesquisa_precos.get('valor_total_cotacao'):
            valor = context.pesquisa_precos['valor_total_cotacao']
            valor_str = f"\n💰 Valor Estimado: **R$ {valor:,.2f}**"

        return f"""👋 Olá! Sou a **LIA**, sua assistente para elaboração do **Edital de Licitação**.

📁 Projeto: **{context.projeto_titulo}**
📋 Documentos disponíveis: **{artefatos_str}**{valor_str}

O Edital padrão do TRE-GO utiliza:
- **Pregão Eletrônico** (Comprasnet 4.0)
- Critério: **Menor Preço**
- Disputa: **Aberta**

💬 **Deseja usar as configurações padrão ou tem requisitos específicos?**"""

    def build_generate_prompt(self, context: ChatContext, conversa_resumo: str) -> str:
        """Prompt específico para geração do Edital."""

        # Construir contexto dos artefatos
        contexto_artefatos = []

        if context.dfd:
            contexto_artefatos.append(f"""
DFD (Documento de Formalização da Demanda):
- Objeto: {context.dfd.get('descricao_objeto', 'N/A')}
- Justificativa: {context.dfd.get('justificativa', 'N/A')[:300]}...""")

        if context.pesquisa_precos:
            valor = context.pesquisa_precos.get('valor_total_cotacao', 0)
            contexto_artefatos.append(f"""
PESQUISA DE PREÇOS:
- Valor Total Estimado: R$ {valor:,.2f}""")

        if context.pgr:
            contexto_artefatos.append(f"""
PGR (Plano de Gerenciamento de Riscos):
- Identificação: {context.pgr.get('identificacao_objeto', 'N/A')[:200]}...""")

        if context.etp:
            contexto_artefatos.append(f"""
ETP (Estudo Técnico Preliminar):
- Necessidade: {context.etp.get('descricao_necessidade', 'N/A')[:200]}...""")

        if context.tr:
            contexto_artefatos.append(f"""
TR (Termo de Referência):
- Objeto: {context.tr.get('definicao_objeto', 'N/A')[:200]}...""")

        artefatos_str = "\n".join(contexto_artefatos) if contexto_artefatos else "Nenhum artefato aprovado disponível."

        itens_pac_str = json.dumps(context.itens_pac, ensure_ascii=False, indent=2) if context.itens_pac else "[]"

        return f"""PROJETO: {context.projeto_titulo}
ÓRGÃO: TRIBUNAL REGIONAL ELEITORAL DE GOIÁS
UASG: 070017

ITENS DO PAC VINCULADOS:
{itens_pac_str}

DOCUMENTOS APROVADOS DO PROCESSO:
{artefatos_str}

INFORMAÇÕES COLETADAS NA CONVERSA COM O USUÁRIO:
{conversa_resumo}

Com base nas informações acima, gere o Edital de Licitação completo.

IMPORTANTE:
- Use as informações da conversa para definir modalidade, critério e tipo de disputa
- Se não especificado, use: Pregão Eletrônico, Menor Preço, Disputa Aberta
- Os prazos devem ser plausíveis (mínimo 8 dias úteis para impugnação)
- Inclua todas as cláusulas obrigatórias da Lei 14.133/2021
- Retorne APENAS o JSON, sem markdown

SCHEMA:
{{
  "objeto": "string (descrição do objeto com valor e dotação)",
  "condicoes_participacao": "string (impedimentos e requisitos de habilitação)",
  "criterios_julgamento": "string (critério, modo de disputa e requisitos da proposta)",
  "fase_lances": "string (fases da sessão, recursos, penalidades e disposições finais)"
}}"""
