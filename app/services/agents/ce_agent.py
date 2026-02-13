"""
Sistema LIA - Agente CE (Certidão de Enquadramento)
==================================================
Certidão de Enquadramento na Modalidade de Dispensa - Lei 14.133/2021, Art. 75

Fluxo: Dispensa por Valor Baixo

Autor: Equipe TRE-GO
Data: Fevereiro 2026
"""

import json
from typing import Dict, Any

from .base_agent import BaseAgent


class CEAgent(BaseAgent):
    """
    Agente especializado em Certidão de Enquadramento (CE).
    
    Documento formal atestando que a contratação se enquadra nos limites
    e condições da modalidade de Dispensa por Valor Baixo (Lei 14.133/2021, Art. 75).
    
    Este é o documento FINAL que encerra o fluxo de dispensa.
    """
    
    agent_type = "ce"
    temperature = 0.4
    
    campos = [
        "limite_legal_aplicavel",
        "valor_contratacao_analisada",
        "conclusao_enquadramento",
        "artigo_lei_aplicavel",
        "responsavel_certificacao",
        "data_certificacao"
    ]
    
    def build_user_prompt(self, contexto: Dict[str, Any]) -> str:
        """Constrói o prompt para geração da CE."""
        
        parts = []
        
        # Cabeçalho formal
        if contexto.get("setor_usuario"):
            parts.append(f"ÓRGÃO/SETOR: {contexto['setor_usuario']}")
        
        if contexto.get("projeto_titulo"):
            parts.append(f"PROJETO: {contexto['projeto_titulo']}")
        
        # Dados da contratação
        if contexto.get("valor_contratacao"):
            parts.append(f"\nVALOR DA CONTRATAÇÃO: R$ {contexto['valor_contratacao']:,.2f}")
        
        # Limite legal
        if contexto.get("limite_legal"):
            parts.append(f"LIMITE LEGAL APLICÁVEL: R$ {contexto['limite_legal']:,.2f}")
        else:
            parts.append(f"LIMITE LEGAL APLICÁVEL: R$ 8.800,00 (Art. 75, Lei 14.133/2021)")
        
        # Objeto resumido
        if contexto.get("descricao_objeto"):
            parts.append(f"\nOBJETO (resumo):\n{contexto['descricao_objeto'][:200]}...")
        
        # Fundamento legal
        parts.append(f"\nFUNDAMENTO LEGAL: Lei 14.133/2021, Art. 75 - Dispensa de Licitação")
        
        # Documentação gerada
        parts.append(f"\nDOCUMENTAÇÃO ANALISADA:")
        parts.append(f"  ✓ Termo de Referência Simplificado (TRS)")
        parts.append(f"  ✓ Aviso de Dispensa Eletrônica (ADE)")
        parts.append(f"  ✓ Justificativa de Preço e Escolha de Fornecedor (JPEF)")
        
        # Responsável pela certificação
        if contexto.get("responsavel_certificacao"):
            parts.append(f"\nRESPONSÁVEL PELA CERTIFICAÇÃO: {contexto['responsavel_certificacao']}")
        
        parts.append("""
Prepare a Certidão de Enquadramento finalizando:
1. Verificação de limite legal (valor ≤ limite)
2. Conformidade com Lei 14.133/2021, Art. 75
3. Conclusão formal de certificação
4. Referência ao artigo aplicável

Retorne APENAS o JSON válido.""")
        
        return "\n".join(parts)
