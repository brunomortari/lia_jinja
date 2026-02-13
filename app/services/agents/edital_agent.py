"""
Sistema LIA - Agente Edital
===========================
Edital de Licitação (Lei 14.133/2021)

Documento que estabelece as regras da licitação, incluindo
prazos, condições de participação, julgamento e contratação.

Autor: Equipe TRE-GO
Data: Janeiro 2026
"""

import json
from typing import Dict, Any

from .base_agent import BaseAgent


class EditalAgent(BaseAgent):
    """
    Agente especializado em Edital de Licitação.
    
    Gera editais completos conforme Lei 14.133/2021,
    considerando todos os documentos anteriores do processo.
    """
    
    agent_type = "edital"
    temperature = 0.3  # Mais conservador para documento jurídico
    
    campos = [
        "preambulo",
        "objeto",
        "prazos",
        "sistema_eletronico",
        "condicoes_participacao",
        "proposta",
        "sessao_publica",
        "recursos",
        "penalidades",
        "pagamento",
        "anexos",
        "disposicoes_finais",
    ]
    
    def build_user_prompt(self, contexto: Dict[str, Any]) -> str:
        """Constrói o prompt do usuário para geração do Edital."""
        
        projeto_titulo = contexto.get("projeto_titulo", "")
        setor = contexto.get("setor_usuario", "Unidade Requisitante")
        itens_pac = contexto.get("itens_pac", [])
        
        # Dados dos documentos anteriores
        dfd = contexto.get("dfd", {})
        etp = contexto.get("etp", {})
        tr = contexto.get("tr", {})
        pgr = contexto.get("pgr", {})
        pesquisa = contexto.get("pesquisa_precos", {})
        
        parts = [
            "ELABORAR EDITAL DE LICITAÇÃO",
            "",
            f"PROJETO: {projeto_titulo}",
            f"ÓRGÃO: TRIBUNAL REGIONAL ELEITORAL DE GOIÁS",
        ]
        
        if itens_pac:
            parts.append(f"\nITENS DO PAC: {json.dumps(itens_pac, ensure_ascii=False)}")
        
        if dfd:
            parts.append("\nDADOS DO DFD:")
            if dfd.get("descricao_objeto_padronizada"):
                parts.append(f"- Objeto: {dfd['descricao_objeto_padronizada']}")
        
        if etp:
            parts.append("\nDADOS DO ETP:")
            if etp.get("descricao_solucao"):
                parts.append(f"- Solução: {etp['descricao_solucao'][:200]}...")
        
        if tr:
            parts.append("\nDADOS DO TR:")
            if tr.get("definicao_objeto"):
                obj = tr["definicao_objeto"]
                if isinstance(obj, dict):
                    parts.append(f"- Objeto: {obj.get('objeto', '')}")
                else:
                    parts.append(f"- Objeto: {obj}")
            if tr.get("descricao_solucao"):
                sol = tr["descricao_solucao"]
                if isinstance(sol, dict):
                    parts.append(f"- Valor Global: R$ {sol.get('valor_global_estimado', 0):,.2f}")
        
        if pesquisa:
            parts.append("\nDADOS DA PESQUISA DE PREÇOS:")
            if pesquisa.get("valor_total"):
                parts.append(f"- Valor Total Estimado: R$ {pesquisa['valor_total']:,.2f}")
        
        parts.append("""
Gere o Edital completo com todos os elementos obrigatórios:
1. preambulo
2. objeto
3. prazos (considerar datas plausíveis, mínimo 8 dias úteis para impugnação)
4. sistema_eletronico
5. condicoes_participacao
6. proposta
7. sessao_publica
8. recursos
9. penalidades
10. pagamento
11. anexos
12. disposicoes_finais

IMPORTANTE:
- UASG do TRE-GO: 070017
- Plataforma: Comprasnet 4.0
- Modalidade padrão: Pregão Eletrônico
- Foro: Seção Judiciária de Goiás

Retorne APENAS o JSON válido conforme schema.""")
        
        return "\n".join(parts)
