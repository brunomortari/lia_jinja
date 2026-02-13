"""
Sistema LIA - Agente RDVE (Relatório de Vantagem Econômica)
===========================================================
Relatório de Demonstração de Vantagem Econômica - Lei 14.133/2021, Art. 37

Fluxo: Adesão a Ata de Registro de Preços

Autor: Equipe TRE-GO
Data: Fevereiro 2026
"""

import json
from typing import Dict, Any

from .base_agent import BaseAgent


class RDVEAgent(BaseAgent):
    """
    Agente especializado em Relatório de Vantagem Econômica (RDVE).
    
    Documento que comprova a vantagem econômica da adesão a uma ata
    de registro de preços em comparação com a contratação direta.
    
    Lei 14.133/2021, Art. 37:
    "A adesão será permitida desde que demonstrada vantajosidade
    de preços, prazos e condições em relação à contratação direta."
    """
    
    agent_type = "rdve"
    temperature = 0.5
    
    campos = [
        "comparativo_precos",
        "custo_processamento_adesao",
        "custo_processamento_direto",
        "conclusao_tecnica",
        "percentual_economia",
        "valor_economia_total"
    ]
    
    def build_user_prompt(self, contexto: Dict[str, Any]) -> str:
        """Constrói o prompt para geração do RDVE."""
        
        parts = []
        
        # Informações do projeto
        if contexto.get("projeto_titulo"):
            parts.append(f"PROJETO: {contexto['projeto_titulo']}")
        
        if contexto.get("valor_objeto"):
            parts.append(f"VALOR DO OBJETO: R$ {contexto.get('valor_objeto', 0):,.2f}")
        
        # Dados da ata selecionada
        ata_dados = contexto.get("ata_selecionada", {})
        if ata_dados:
            parts.append(f"\nATA DE REGISTRO SELECIONADA:")
            if ata_dados.get("numero"):
                parts.append(f"  Número: {ata_dados['numero']}")
            if ata_dados.get("fornecedor"):
                parts.append(f"  Fornecedor: {ata_dados['fornecedor']}")
            if ata_dados.get("preco_unitario"):
                parts.append(f"  Preço Unitário: R$ {ata_dados['preco_unitario']:,.2f}")
        
        # Cotações de mercado para comparação
        cotacoes = contexto.get("cotacoes_mercado", [])
        if cotacoes:
            parts.append(f"\nCOTAÇÕES DE MERCADO (Contratação Direta):")
            for i, cotacao in enumerate(cotacoes[:3], 1):
                if isinstance(cotacao, dict):
                    fornecedor = cotacao.get("fornecedor", f"Fornecedor {i}")
                    preco = cotacao.get("preco", 0)
                    parts.append(f"  {fornecedor}: R$ {preco:,.2f}")
                else:
                    parts.append(f"  {cotacao}")
        
        # Especificação do objeto
        if contexto.get("especificacao"):
            parts.append(f"\nESPECIFICAÇÃO DO OBJETO:\n{contexto['especificacao']}")
        
        # Instruções finais
        parts.append("""
Gere o RDVE comparando:
1. Preço da ata vs cotações de mercado
2. Custo de processamento estimado para adesão (menor: sem licitação)
3. Custo de processamento para contratação direta (maior: licitação completa)
4. Conclusão demonstrando a vantajosidade legal e econômica

Retorne APENAS o JSON válido.""")
        
        return "\n".join(parts)
