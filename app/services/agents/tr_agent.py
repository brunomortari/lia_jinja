"""
Sistema LIA - Agente TR
=======================
Termo de Referência (Lei 14.133/2021, art. 6º, XXIII)

Documento que contém todas as especificações técnicas e condições
para a contratação de bens e serviços.

Autor: Equipe TRE-GO
Data: Janeiro 2026
"""

import json
from typing import Dict, Any

from .base_agent import BaseAgent


class TRAgent(BaseAgent):
    """
    Agente especializado em Termo de Referência.
    
    O TR é documento obrigatório que define o objeto da contratação
    com todas as especificações técnicas e condições de execução.
    """
    
    agent_type = "tr"
    temperature = 0.4
    
    campos = [
        "definicao_objeto",
        "fundamentacao_legal",
        "descricao_solucao",
        "requisitos_contratacao",
        "modelo_execucao",
        "modelo_gestao",
        "criterios_medicao",
        "obrigacoes_contratante",
        "obrigacoes_contratada",
        "sancoes",
        "condicoes_pagamento",
        "vigencia",
    ]
    
    def build_user_prompt(self, contexto: Dict[str, Any]) -> str:
        """Constrói o prompt do usuário para geração do TR."""
        
        projeto_titulo = contexto.get("projeto_titulo", "")
        setor = contexto.get("setor_usuario", "Unidade Requisitante")
        itens_pac = contexto.get("itens_pac", [])
        
        # Dados do DFD
        dfd = contexto.get("dfd", {})
        
        # Dados do ETP
        etp = contexto.get("etp", {})
        
        # Dados da pesquisa de preços
        pesquisa = contexto.get("pesquisa_precos", {})
        
        parts = [
            "ELABORAR TERMO DE REFERÊNCIA",
            "",
            f"PROJETO: {projeto_titulo}",
            f"SETOR REQUISITANTE: {setor}",
        ]
        
        if itens_pac:
            parts.append(f"\nITENS DO PAC: {json.dumps(itens_pac, ensure_ascii=False)}")
        
        if dfd:
            parts.append("\nDADOS DO DFD:")
            if dfd.get("descricao_objeto_padronizada"):
                parts.append(f"- Objeto: {dfd['descricao_objeto_padronizada']}")
            if dfd.get("justificativa_tecnica"):
                parts.append(f"- Justificativa: {dfd['justificativa_tecnica']}")
        
        if etp:
            parts.append("\nDADOS DO ETP:")
            if etp.get("descricao_solucao"):
                parts.append(f"- Solução: {etp['descricao_solucao']}")
            if etp.get("estimativa_quantidades"):
                parts.append(f"- Quantidades: {etp['estimativa_quantidades']}")
        
        if pesquisa:
            parts.append("\nDADOS DA PESQUISA DE PREÇOS:")
            if pesquisa.get("valor_total"):
                parts.append(f"- Valor Total: R$ {pesquisa['valor_total']:,.2f}")
            if pesquisa.get("itens"):
                parts.append(f"- Itens cotados: {len(pesquisa['itens'])}")
        
        parts.append("""
Gere o Termo de Referência completo com todos os elementos obrigatórios:
1. definicao_objeto
2. fundamentacao_legal
3. descricao_solucao
4. requisitos_contratacao
5. modelo_execucao
6. modelo_gestao
7. criterios_medicao
8. obrigacoes_contratante
9. obrigacoes_contratada
10. sancoes
11. condicoes_pagamento
12. vigencia

Retorne APENAS o JSON válido conforme schema.""")
        
        return "\n".join(parts)
