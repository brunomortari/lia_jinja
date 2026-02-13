"""
Sistema LIA - Agente JE
========================
Justificativa de Excepcionalidade (Lei 14.133/2021)

Autor: Equipe TRE-GO
Data: Fevereiro 2026
"""

import json
from typing import Dict, Any

from .base_agent import BaseAgent


class JustificativaExcepcionalidadeAgent(BaseAgent):
    """
    Agente especializado em Justificativa de Excepcionalidade.
    
    A Justificativa de Excepcionalidade permite contratações fora do PAC
    em situações extraordinárias conforme Lei 14.133/2021.
    """
    
    agent_type = "je"
    temperature = 0.6
    
    campos = [
        "descricao",
        "justificativa_legal",
        "justificativa_emergencia",
        "impacto_inexecucao",
        "custo_estimado",
        "cronograma",
        "termos_referencia",
        "tipo_contratacao",
        "frequencia",
        "prioridade",
        "responsavel",
    ]
    
    def build_user_prompt(self, contexto: Dict[str, Any]) -> str:
        """Constrói o prompt do usuário para geração da JE."""
        
        setor = contexto.get("setor_usuario", "Unidade Requisitante")
        input_usuario = contexto.get("input_usuario", contexto.get("descricao_necessidade", ""))
        atribuicoes = contexto.get("contexto_atribuicoes", "")
        
        parts = [
            f"O usuário do setor '{setor}' necessita de contratação extraordinária: '{input_usuario}'.",
        ]
        
        if atribuicoes:
            parts.append(f"Atribuições regimentais do setor: {atribuicoes}")
        
        parts.append("""
Gere o objeto JSON contendo:
- descricao
- justificativa_legal
- justificativa_emergencia
- impacto_inexecucao
- custo_estimado
- cronograma
- termos_referencia
- tipo_contratacao
- frequencia
- prioridade
- responsavel""")
        
        return "\n".join(parts)
