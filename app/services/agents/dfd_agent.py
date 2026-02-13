"""
Sistema LIA - Agente DFD
========================
Documento de Formalização da Demanda (Lei 14.133/2021)

Autor: Equipe TRE-GO
Data: Janeiro 2026
"""

import json
from typing import Dict, Any

from .base_agent import BaseAgent


class DFDAgent(BaseAgent):
    """
    Agente especializado em Documento de Formalização da Demanda (DFD).
    
    O DFD é o primeiro documento do ciclo de contratações públicas,
    onde o setor requisitante formaliza sua necessidade.
    """
    
    agent_type = "dfd"
    temperature = 0.6
    
    campos = [
        "justificativa_tecnica",
        "descricao_objeto_padronizada",
        "id_item_pca",
        "prioridade_sugerida",
        "analise_alinhamento",
        "data_pretendida",
        "responsavel_gestor",
        "responsavel_fiscal",
    ]
    
    def build_user_prompt(self, contexto: Dict[str, Any]) -> str:
        """Constrói o prompt do usuário para geração do DFD."""
        
        setor = contexto.get("setor_usuario", "Unidade Requisitante")
        input_usuario = contexto.get("input_usuario", contexto.get("descricao_necessidade", ""))
        itens_pac = contexto.get("itens_pac", contexto.get("json_pca_items", []))
        atribuicoes = contexto.get("contexto_atribuicoes", "")
        
        parts = [
            f"O usuário do setor '{setor}' deseja contratar: '{input_usuario}'.",
        ]
        
        if itens_pac:
            parts.append(f"Itens do PCA disponíveis para este setor: {json.dumps(itens_pac, ensure_ascii=False)}")
        
        if atribuicoes:
            parts.append(f"Atribuições regimentais do setor: {atribuicoes}")
        
        parts.append("""
Gere o objeto JSON contendo:
- justificativa_tecnica
- descricao_objeto_padronizada
- id_item_pca
- prioridade_sugerida
- analise_alinhamento
- data_pretendida (extraia do texto do usuario se mencionado, formato DD/MM/AAAA ou descricao como 'primeiro semestre de 2025')
- responsavel_gestor (extraia o nome se mencionado pelo usuario)
- responsavel_fiscal (extraia o nome se mencionado pelo usuario)""")
        
        return "\n".join(parts)
