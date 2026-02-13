"""
Sistema LIA - Agente Wizard de Criacao de Skills
=================================================
Agente especializado em guiar o usuario na criacao
de novas skills (habilidades) via conversa.

Autor: Equipe TRE-GO
Data: Fevereiro 2026
"""

import json
import logging
import re
from typing import AsyncGenerator, List, Optional, Dict, Any
from openai import AsyncOpenAI

from app.config import settings

logger = logging.getLogger(__name__)


SKILL_WIZARD_SYSTEM_PROMPT = """Voce e um especialista em criar Skills (Habilidades) para o sistema LIA.

O sistema LIA gera documentos de licitacao publica (DFD, ETP, TR, PGR, Edital) usando IA.
Skills sao instrucoes comportamentais que modificam como a IA gera esses documentos.

EXEMPLOS DE SKILLS:
- "Auditoria Rigorosa": Sempre citar artigos especificos da Lei 14.133/2021
- "Sustentabilidade": Incluir criterios ambientais em todos os documentos
- "Linguagem Simplificada": Evitar jargao juridico, usar frases curtas

SEU OBJETIVO:
Guiar o usuario para criar uma skill bem definida, coletando:
1. **Nome** - Titulo curto e descritivo (max 200 chars)
2. **Descricao** - O que a skill faz em 1-2 frases (max 1000 chars)
3. **Instrucoes** - As regras que a IA deve seguir (max 5000 chars)

FLUXO DA CONVERSA:
1. Pergunte ao usuario o que ele deseja que a IA faca diferente
2. Faca perguntas de refinamento (1-2 perguntas, seja objetivo)
3. Quando tiver informacao suficiente, gere a skill e apresente um resumo
4. Se o usuario confirmar, adicione [SKILL_READY] seguido do JSON

FORMATO DE SAIDA (quando pronto):
Apresente um resumo legivel e ao final:
[SKILL_READY]
{"nome": "...", "descricao": "...", "instrucoes": "..."}

REGRAS:
- Seja conciso e direto (max 3-4 linhas por resposta)
- As instrucoes devem ser claras e acionaveis para uma IA
- Use linguagem formal nas instrucoes (elas serao injetadas no prompt)
- NUNCA mencione termos tecnicos como "JSON", "prompt", "API" ao usuario
- Se o usuario disser "sim", "confirmo", "pode criar" apos o resumo, emita [SKILL_READY] imediatamente"""


class SkillWizardAgent:
    """Agente para criacao guiada de skills via chat."""

    def __init__(self, model_override: Optional[str] = None):
        self.client = AsyncOpenAI(
            api_key=settings.OPENROUTER_API_KEY,
            base_url=settings.OPENROUTER_BASE_URL,
            timeout=settings.OPENROUTER_TIMEOUT,
        )
        self.model = model_override or settings.OPENROUTER_DEFAULT_MODEL

    async def chat(
        self,
        message: str,
        history: List[Dict[str, str]],
    ) -> AsyncGenerator[str, None]:
        """Processa mensagem do usuario e retorna resposta em streaming."""
        messages = [
            {"role": "system", "content": SKILL_WIZARD_SYSTEM_PROMPT}
        ]

        for msg in history[-10:]:
            messages.append({"role": msg["role"], "content": msg["content"]})

        messages.append({"role": "user", "content": message})

        logger.info(f"[SkillWizard] Chat com {len(messages)} mensagens, model={self.model}")

        try:
            stream = await self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                temperature=0.7,
                max_tokens=1024,
                stream=True,
            )

            async for chunk in stream:
                if chunk.choices and chunk.choices[0].delta.content:
                    yield chunk.choices[0].delta.content

        except Exception as e:
            logger.error(f"[SkillWizard] Erro no chat: {e}")
            raise

    @staticmethod
    def extract_skill_data(text: str) -> Optional[Dict[str, Any]]:
        """Extrai dados da skill do texto da resposta da IA."""
        if "[SKILL_READY]" not in text:
            return None

        # Pegar tudo apos [SKILL_READY]
        after_marker = text.split("[SKILL_READY]")[-1].strip()

        # Tentar encontrar JSON
        json_match = re.search(r'\{[^{}]*\}', after_marker, re.DOTALL)
        if not json_match:
            return None

        try:
            data = json.loads(json_match.group())
            # Validar campos obrigatorios
            if not data.get("nome") or not data.get("instrucoes"):
                return None
            return data
        except json.JSONDecodeError:
            return None

    def get_mensagem_inicial(self) -> str:
        return (
            "Ola! Vou te ajudar a criar uma nova **habilidade** para a IA.\n\n"
            "Habilidades sao instrucoes que modificam como a IA gera seus documentos. "
            "Por exemplo: ser mais rigoroso com citacoes legais, incluir criterios ambientais, "
            "ou usar linguagem simplificada.\n\n"
            "**Me conta: o que voce gostaria que a IA fizesse diferente ao gerar seus documentos?**"
        )
