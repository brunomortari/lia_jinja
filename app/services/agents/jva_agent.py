"""
Sistema LIA - Agente JVA (Justificativa de Vantagem e Conveniência da Adesão)
=============================================================================
Justificativa de Vantagem, Conveniência e Oportunidade da Adesão - Lei 14.133/2021, Art. 37

Fluxo: Adesão a Ata de Registro de Preços

Autor: Equipe TRE-GO
Data: Fevereiro 2026
"""

import json
from typing import Dict, Any

from .base_agent import BaseAgent


class JVAAgent(BaseAgent):
    """
    Agente especializado em Justificativa de Vantagem da Adesão (JVA).
    
    Documento legal que funda juridicamente a decisão de fazer adesão a ata,
    demonstrando conveniência e oportunidade sob aspectos técnicos e legais.
    
    Diferente do RDVE (econômico), JVA aborda:
    - Fundamentação legal da adesão
    - Conveniência e oportunidade
    - Declaração de conformidade com Lei 14.133/2021
    """
    
    agent_type = "jva"
    temperature = 0.6
    
    campos = [
        "fundamentacao_legal",
        "justificativa_conveniencia",
        "declaracao_conformidade"
    ]
    
    def build_user_prompt(self, contexto: Dict[str, Any]) -> str:
        """Constrói o prompt para geração da JVA."""
        
        parts = []
        
        # Informações do projeto
        if contexto.get("projeto_titulo"):
            parts.append(f"PROJETO: {contexto['projeto_titulo']}")
        
        if contexto.get("setor_usuario"):
            parts.append(f"ÓRGÃO/SETOR: {contexto['setor_usuario']}")
        
        # Dados da ata selecionada
        ata_dados = contexto.get("ata_selecionada", {})
        if ata_dados:
            parts.append(f"\nATA DE REGISTRO:")
            if ata_dados.get("numero"):
                parts.append(f"  Número: {ata_dados['numero']}")
            if ata_dados.get("orgao_gerenciador"):
                parts.append(f"  Órgão Gerenciador: {ata_dados['orgao_gerenciador']}")
            if ata_dados.get("data_vigencia"):
                parts.append(f"  Vigência: {ata_dados['data_vigencia']}")
        
        # Objeto da contratação
        if contexto.get("objeto"):
            parts.append(f"\nOBJETO DA CONTRATAÇÃO:\n{contexto['objeto']}")
        
        # Justificativa de opportunidade
        if contexto.get("justificativa_oportunidade"):
            parts.append(f"\nOPORTUNIDADE:\n{contexto['justificativa_oportunidade']}")
        
        # Vantagens específicas
        if contexto.get("vantagens_adesao"):
            parts.append(f"\nVANTAGENS MENCIONADAS:\n{contexto['vantagens_adesao']}")
        
        parts.append("""
Redija a JVA em 3 partes:
1. FUNDAMENTAÇÃO LEGAL: Citar artigos aplicáveis
2. JUSTIFICATIVA DE CONVENIÊNCIA: Razões administrativas
3. DECLARAÇÃO DE CONFORMIDADE: Atesto de conformidade

Retorne APENAS o JSON válido com os 3 campos.""")
        
        return "\n".join(parts)
