"""
Sistema LIA - Agente TRS (Termo de Referência Simplificado)
===========================================================
Termo de Referência Simplificado para Dispensa por Valor Baixo - Lei 14.133/2021, Art. 75

Fluxo: Dispensa por Valor Baixo

Autor: Equipe TRE-GO
Data: Fevereiro 2026
"""

import json
from typing import Dict, Any

from .base_agent import BaseAgent


class TRSAgent(BaseAgent):
    """
    Agente especializado em Termo de Referência Simplificado (TRS).
    
    Para dispensas por valor baixo (Lei 14.133/2021, Art. 75),
    o TR pode ser simplificado, sem exigências rigorosas de especificação.
    
    Reduzir burocracia mantendo os requisitos técnicos mínimos.
    """
    
    agent_type = "trs"
    temperature = 0.5
    
    campos = [
        "especificacao_objeto",
        "criterios_qualidade_simplificados",
        "prazos_entrega",
        "valor_referencia_dispensa",
        "justificativa_dispensa"
    ]
    
    def build_user_prompt(self, contexto: Dict[str, Any]) -> str:
        """Constrói o prompt para geração do TRS."""
        
        parts = []
        
        # Informações do projeto
        if contexto.get("projeto_titulo"):
            parts.append(f"PROJETO: {contexto['projeto_titulo']}")
        
        if contexto.get("setor_usuario"):
            parts.append(f"SETOR REQUISITANTE: {contexto['setor_usuario']}")
        
        # Valor estimado
        if contexto.get("valor_estimado"):
            parts.append(f"VALOR ESTIMADO: R$ {contexto['valor_estimado']:,.2f}")
        
        # Descrição do objeto
        if contexto.get("descricao_objeto"):
            parts.append(f"\nDESCRIÇÃO DO OBJETO:\n{contexto['descricao_objeto']}")
        
        # Especificações técnicas
        if contexto.get("especificacoes_tecnicas"):
            parts.append(f"\nESPECIFICAÇÕES TÉCNICAS:\n{contexto['especificacoes_tecnicas']}")
        
        # Cronograma desejado
        if contexto.get("cronograma"):
            parts.append(f"\nCRONOGRAMA DESEJADO:\n{contexto['cronograma']}")
        
        # Normas/certificações exigidas
        if contexto.get("normas_aplicaveis"):
            parts.append(f"\nNORMAS/CERTIFICAÇÕES:\n{contexto['normas_aplicaveis']}")
        
        parts.append("""
Prepare um TRS SIMPLIFICADO contendo:
1. Especificação clara (sem excessos)
2. Critérios de qualidade (lista simplificada)
3. Prazos de entrega
4. Valor de referência
5. Justificativa legal

Retorne APENAS o JSON válido.""")
        
        return "\n".join(parts)
