"""
Sistema LIA - Agente CHK Conversacional
=======================================
Agente que conversa com o usuario para coletar informacoes
e gerar o Checklist de Instrucao (AGU/SEGES).

O Checklist verifica a conformidade documental do processo
licitatorio conforme a Lei 14.133/2021.

Autor: Equipe TRE-GO
Data: Fevereiro 2026
"""

import json
from typing import Dict, Any, List, Optional

from .conversational_agent import ConversationalAgent, ChatContext, Message


class CHKChatAgent(ConversationalAgent):
    """
    Agente conversacional para Checklist de Instrucao (AGU/SEGES).

    Coleta informacoes sobre:
    - Quais documentos ja estao no processo
    - Referencias de folhas/paginas de cada documento
    - Observacoes sobre pendencias
    - Autoridade validadora
    """

    agent_type = "checklist_conformidade"

    nome_artefato = "Checklist de Instrução"

    temperature_chat = 0.7
    temperature_generate = 0.4

    dados_necessarios = [
        "Documentos presentes no processo (DFD, ETP, TR, PGR, etc.)",
        "Referências de folhas/páginas de cada documento",
        "Disponibilidade orçamentária (sim/não)",
        "Parecer jurídico (sim/não/pendente)",
        "Observações ou pendências identificadas",
        "Nome da autoridade validadora (opcional)",
    ]

    campos_chk = [
        "itens_verificacao",
        "dfd_presente",
        "dfd_folhas",
        "etp_presente",
        "etp_folhas",
        "tr_presente",
        "tr_folhas",
        "matriz_riscos_presente",
        "matriz_riscos_folhas",
        "disponibilidade_orcamentaria_presente",
        "disponibilidade_orcamentaria_folhas",
        "parecer_juridico_presente",
        "parecer_juridico_folhas",
        "validado_por",
        "observacoes_gerais",
        "status_conformidade",
    ]

    def get_mensagem_inicial(self, context: ChatContext) -> str:
        """Mensagem inicial customizada para CHK."""

        # Info sobre artefatos existentes
        artefatos_info = []
        if context.dfd:
            artefatos_info.append("✅ DFD aprovado")
        if context.etp:
            artefatos_info.append("✅ ETP aprovado")
        if context.tr:
            artefatos_info.append("✅ TR aprovado")
        if context.pgr:
            artefatos_info.append("✅ PGR (Matriz de Riscos) aprovado")
        if context.pesquisa_precos:
            artefatos_info.append("✅ Pesquisa de Preços aprovada")

        artefatos_str = "\n".join(artefatos_info) if artefatos_info else "Nenhum artefato aprovado encontrado."

        return f"""Olá! Sou a **LIA**, sua assistente para elaboração do **Checklist de Instrução** conforme modelos AGU/SEGES.

Projeto: **{context.projeto_titulo}**

**📋 Artefatos detectados no processo:**
{artefatos_str}

Vou te ajudar a verificar a conformidade documental do processo licitatório conforme a **Lei 14.133/2021**.

**Para começar: há algum documento adicional no processo que eu deva considerar?**
(Ex: disponibilidade orçamentária, parecer jurídico, portarias, etc.)

Ou se preferir, posso gerar o checklist automaticamente com base nos artefatos já aprovados."""

    def build_chat_system_prompt(self, context: ChatContext) -> str:
        """Constroi o system prompt para o modo chat."""
        checklist = "\n".join([f"- {item}" for item in self.dados_necessarios])

        base_prompt = f"""{self.system_prompt_chat}

CONTEXTO DO PROJETO:
- ID: {context.projeto_id}
- Titulo: {context.projeto_titulo}
- Setor: {context.setor_usuario}
- Itens PAC: {len(context.itens_pac)} itens
"""

        # Adicionar contexto dos artefatos existentes
        if context.dfd:
            base_prompt += "\nDFD APROVADO: Sim"
            desc = context.dfd.get('descricao_objeto', context.dfd.get('descricao_objeto_padronizada', ''))
            if desc:
                base_prompt += f"\n  - Objeto: {desc[:150]}"

        if context.etp:
            base_prompt += "\nETP APROVADO: Sim"
            desc = context.etp.get('descricao_necessidade', '')
            if desc:
                base_prompt += f"\n  - Necessidade: {desc[:150]}"

        if context.tr:
            base_prompt += "\nTR APROVADO: Sim"
            obj = context.tr.get('definicao_objeto', '')
            if obj:
                base_prompt += f"\n  - Objeto TR: {obj[:150]}"

        if context.pgr:
            base_prompt += "\nMATRIZ DE RISCOS (PGR) APROVADA: Sim"

        if context.pesquisa_precos:
            base_prompt += "\nPESQUISA DE PRECOS APROVADA: Sim"
            valor = context.pesquisa_precos.get('valor_total_cotacao', context.pesquisa_precos.get('valor_total', 0))
            if valor:
                base_prompt += f"\n  - Valor Total: R$ {valor:,.2f}"

        base_prompt += f"""

DADOS IMPORTANTES A COLETAR:
{checklist}

INSTRUCOES:
1. Converse naturalmente para entender a situacao documental do processo
2. Use os artefatos ja aprovados que ja temos no contexto - NAO pergunte sobre eles!
3. Pergunte apenas sobre documentos que NAO temos no sistema (disponibilidade orcamentaria, parecer juridico, portarias)
4. ASSIM QUE o usuario responder sobre documentos adicionais ou pedir para gerar, IMEDIATAMENTE:
   - Faca um resumo breve dos documentos identificados
   - Adicione [GERAR_CHK] ao final da mensagem
5. Se o usuario pedir "gerar", "criar", "fazer o checklist", adicione [GERAR_CHK] imediatamente
6. NUNCA mencione JSON, schemas ou formatos tecnicos
7. Seja conciso - 1-2 mensagens no maximo antes de mostrar [GERAR_CHK]"""

        return base_prompt

    def build_generate_prompt(self, context: ChatContext, conversa_resumo: str) -> str:
        """Prompt especifico para geracao do Checklist."""

        # Detectar artefatos presentes
        dfd_status = "sim" if context.dfd else "nao"
        etp_status = "sim" if context.etp else "nao"
        tr_status = "sim" if context.tr else "nao"
        pgr_status = "sim" if context.pgr else "nao"
        pp_status = "sim" if context.pesquisa_precos else "nao"

        return f"""PROJETO: {context.projeto_titulo}
SETOR REQUISITANTE: {context.setor_usuario}

ARTEFATOS PRESENTES NO SISTEMA:
- DFD: {dfd_status}
- ETP: {etp_status}
- TR: {tr_status}
- Matriz de Riscos (PGR): {pgr_status}
- Pesquisa de Preços: {pp_status}

INFORMACOES COLETADAS NA CONVERSA COM O USUARIO:
{conversa_resumo}

Com base nas informacoes acima, gere o Checklist de Instrucao (AGU/SEGES) completo.

IMPORTANTE:
- Marque como "sim" os documentos que existem no sistema
- Para documentos que existem, preencha as folhas com "Anexo Digital - Sistema LIA"
- Para documentos mencionados pelo usuario, use as informacoes fornecidas
- Determine o status_conformidade com base na completude do processo
- Gere itens_verificacao detalhados com TODOS os itens exigidos pela AGU/SEGES
- Retorne APENAS o JSON, sem markdown

SCHEMA:
{{
  "dfd_presente": "sim" | "nao" | "nao_se_aplica",
  "dfd_folhas": "string ou null",
  "etp_presente": "sim" | "nao" | "nao_se_aplica",
  "etp_folhas": "string ou null",
  "tr_presente": "sim" | "nao" | "nao_se_aplica",
  "tr_folhas": "string ou null",
  "matriz_riscos_presente": "sim" | "nao" | "nao_se_aplica",
  "matriz_riscos_folhas": "string ou null",
  "disponibilidade_orcamentaria_presente": "sim" | "nao" | "nao_se_aplica",
  "disponibilidade_orcamentaria_folhas": "string ou null",
  "parecer_juridico_presente": "sim" | "nao" | "nao_se_aplica",
  "parecer_juridico_folhas": "string ou null",
  "validado_por": "string ou null",
  "observacoes_gerais": "string",
  "status_conformidade": "conforme" | "nao_conforme" | "conforme_com_ressalvas",
  "itens_verificacao": [
    {{
      "item": "string (numero do item)",
      "descricao": "string (descricao do item de verificacao)",
      "status": "sim" | "nao" | "nao_se_aplica",
      "referencia_folhas": "string (referencia das folhas/paginas)",
      "observacoes": "string ou null"
    }}
  ]
}}"""
