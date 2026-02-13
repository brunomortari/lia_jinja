"""
Sistema LIA - Agente ADE (Aviso de Dispensa Eletrônica)
=======================================================
Aviso de Dispensa Eletrônica - Lei 14.133/2021, Art. 75

Fluxo: Dispensa por Valor Baixo

Autor: Equipe TRE-GO
Data: Fevereiro 2026
"""

import json
from typing import Dict, Any
from datetime import datetime

from .base_agent import BaseAgent


class ADEAgent(BaseAgent):
    """
    Agente especializado em Aviso de Dispensa Eletrônica (ADE).
    
    Para dispensas por valor baixo, é necessário publicar aviso eletrônico
    em plataforma específica (Portal de Compras, SEAI, etc).
    
    Este documento prepara os dados para publicação do aviso.
    """
    
    agent_type = "ade"
    temperature = 0.4
    
    campos = [
        "numero_aviso",
        "data_publicacao",
        "descricao_objeto",
        "link_portal_publicacao",
        "protocolo_publicacao"
    ]
    
    def build_user_prompt(self, contexto: Dict[str, Any]) -> str:
        """Constrói o prompt para geração da ADE."""
        
        parts = []
        
        # Órgão responsável
        if contexto.get("setor_usuario"):
            parts.append(f"ÓRGÃO RESPONSÁVEL: {contexto['setor_usuario']}")
        
        # Descrição do objeto
        if contexto.get("descricao_objeto"):
            parts.append(f"\nOBJETO DA DISPENSA:\n{contexto['descricao_objeto']}")
        
        # Valor máximo
        if contexto.get("valor_maximo"):
            parts.append(f"VALOR MÁXIMO: R$ {contexto['valor_maximo']:,.2f}")
        
        # Modalidade (Art. 75)
        if contexto.get("fundamento_legal"):
            parts.append(f"FUNDAMENTO LEGAL: {contexto['fundamento_legal']}")
        else:
            parts.append("FUNDAMENTO LEGAL: Lei 14.133/2021, Art. 75 - Dispensa de Licitação")
        
        # Portal de publicação
        if contexto.get("portal_publicacao"):
            parts.append(f"PORTAL DE PUBLICAÇÃO: {contexto['portal_publicacao']}")
        else:
            parts.append("PORTAL DE PUBLICAÇÃO: Portal de Compas (sugerido)")
        
        # Prazo de manifestação
        if contexto.get("prazo_manifestacao"):
            parts.append(f"PRAZO PARA MANIFESTAÇÃO: {contexto['prazo_manifestacao']}")
        else:
            parts.append("PRAZO PARA MANIFESTAÇÃO: 3 dias úteis (mínimo legal)")
        
        parts.append("""
Gere os dados do Aviso de Dispensa Eletrônica:
1. Número único do aviso
2. Data de publicação (data de hoje ou data informada)
3. Descrição do objeto conforme TRS
4. Link/referência do portal de publicação
5. Protocolo de publicação

Retorne APENAS o JSON válido.""")
        
        return "\n".join(parts)
