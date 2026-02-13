"""
Sistema LIA - Agente JPEF (Justificativa de Preço e Escolha de Fornecedor)
=========================================================================
Justificativa de Preço e Escolha de Fornecedor - Lei 14.133/2021, Art. 75

Fluxo: Dispensa por Valor Baixo

Autor: Equipe TRE-GO
Data: Fevereiro 2026
"""

import json
from typing import Dict, Any

from .base_agent import BaseAgent


class JPEFAgent(BaseAgent):
    """
    Agente especializado em Justificativa de Preço e Escolha de Fornecedor (JPEF).
    
    Para dispensas por valor baixo, justificar:
    1. O preço proposto e seu caráter competitivo
    2. A escolha do fornecedor entre interessados
    3. Conformidade com requisitos do TRS
    
    Diferente de uma licitação formal, mas ainda exigindo comprovação de vantajosidade.
    """
    
    agent_type = "jpef"
    temperature = 0.5
    
    campos = [
        "justificativa_fornecedor",
        "analise_preco_praticado",
        "preco_final_contratacao"
    ]
    
    def build_user_prompt(self, contexto: Dict[str, Any]) -> str:
        """Constrói o prompt para geração da JPEF."""
        
        parts = []
        
        # Informações do projeto
        if contexto.get("projeto_titulo"):
            parts.append(f"PROJETO: {contexto['projeto_titulo']}")
        
        # Objeto da contratação
        if contexto.get("descricao_objeto"):
            parts.append(f"\nOBJETO:\n{contexto['descricao_objeto']}")
        
        # Fornecedor selecionado
        if contexto.get("fornecedor_selecionado"):
            parts.append(f"\nFORNECEDOR SELECIONADO: {contexto['fornecedor_selecionado']}")
        
        if contexto.get("cnpj_fornecedor"):
            parts.append(f"CNPJ: {contexto['cnpj_fornecedor']}")
        
        # Histórico/referências do fornecedor
        if contexto.get("historico_fornecedor"):
            parts.append(f"\nHISTÓRICO/REFERÊNCIAS:\n{contexto['historico_fornecedor']}")
        
        # Preço proposto
        if contexto.get("preco_proposto"):
            parts.append(f"\nPREÇO PROPOSTO: R$ {contexto['preco_proposto']:,.2f}")
        
        # Cotações comparativas
        cotacoes = contexto.get("cotacoes_mercado", [])
        if cotacoes:
            parts.append(f"\nCOTAÇÕES DE MERCADO (para comparação):")
            for cotacao in cotacoes[:3]:
                if isinstance(cotacao, dict):
                    fornecedor = cotacao.get("fornecedor", "Fornecedor")
                    preco = cotacao.get("preco", 0)
                    parts.append(f"  {fornecedor}: R$ {preco:,.2f}")
        
        # Prazo
        if contexto.get("prazo_proposto"):
            parts.append(f"\nPRAZO PROPOSTO: {contexto['prazo_proposto']}")
        
        # Conformidade com TRS
        if contexto.get("conformidade_trs"):
            parts.append(f"\nCONFORMIDADE COM TRS:\n{contexto['conformidade_trs']}")
        
        parts.append("""
Prepare a JPEF justificando:
1. Capacidade e confiabilidade do fornecedor
2. Competitividade do preço proposto vs mercado
3. Conformidade com especificações técnicas

Retorne APENAS o JSON válido.""")
        
        return "\n".join(parts)
