"""
Sistema LIA - Agente PGR
========================
Plano de Gerenciamento de Riscos (Lei 14.133/2021)

Implementa análise de riscos usando matriz 5x5 (Probabilidade x Impacto)
conforme metodologia do TCU e boas práticas de GRC.

Autor: Equipe TRE-GO
Data: Janeiro 2026
"""

import json
from typing import Dict, Any

from .base_agent import BaseAgent


class PGRAgent(BaseAgent):
    """
    Agente LIA-RISK: Especialista em Gerenciamento de Riscos.
    
    Implementa análise estruturada de riscos conforme:
    - Lei 14.133/2021
    - Orientações do TCU
    - IN SEGES e AGU
    """
    
    agent_type = "pgr"
    temperature = 0.3  # Mais conservador para análise de riscos
    
    campos = [
        "identificacao_objeto",
        "valor_estimado_total",
        "metodologia_adotada",
        "data_revisao",
        "resumo_analise_planejamento",
        "resumo_analise_selecao",
        "resumo_analise_gestao",
        "itens_risco",
    ]
    
    system_prompt = """Você é LIA-RISK, sistema especialista em Governança, Riscos e Compliance (GRC) para setor público brasileiro.

METODOLOGIA:
- Matriz 5x5 (Probabilidade x Impacto)
- Fases: Planejamento, Seleção de Fornecedor, Gestão Contratual
- Categorias: Técnico, Administrativo, Jurídico, Econômico, Reputacional

ESCALA DE PROBABILIDADE (1-5):
1 = Improvável (<10%)
2 = Pouco Provável (10-25%)
3 = Moderada (25-50%)
4 = Provável (50-75%)
5 = Muito Provável (>75%)

ESCALA DE IMPACTO (1-5):
1 = Irrelevante (sem prejuízo significativo)
2 = Menor (prejuízo recuperável facilmente)
3 = Médio (atraso ou custo adicional moderado)
4 = Maior (comprometimento significativo do objetivo)
5 = Catastrófico (inviabilização do projeto)

HEURÍSTICAS DE AVALIAÇÃO:
- CV (Coeficiente de Variação) > 25% nas cotações → probabilidade >= 3
- Menos de 3 fornecedores identificados → probabilidade >= 4 (risco de licitação deserta)
- Prazo < 60 dias → probabilidade >= 3
- Valor > R$ 500k → impacto >= 3

TIPOS DE TRATAMENTO:
- Mitigar: Reduzir probabilidade ou impacto
- Transferir: Alocar risco para contratada ou seguro
- Aceitar: Monitorar sem ação preventiva
- Evitar: Modificar escopo para eliminar o risco

Retorne APENAS JSON válido conforme schema, sem markdown, sem explicações fora do JSON.
Se há dúvida, use senso conservador (favorecendo probabilidade/impacto maiores)."""
    
    def build_user_prompt(self, contexto: Dict[str, Any]) -> str:
        """Constrói o prompt do usuário para geração do PGR."""
        
        projeto_titulo = contexto.get("projeto_titulo", "Sem título")
        setor = contexto.get("setor_usuario", "Unidade Requisitante")
        valor_estimado = contexto.get("valor_estimado", "N/A")
        itens_pac = contexto.get("itens_pac", [])
        
        # Dados do DFD
        dfd = contexto.get("dfd", {})
        
        # Dados da pesquisa de preços
        pesquisa = contexto.get("pesquisa_precos", {})
        
        parts = [
            "ANÁLISE DE RISCOS PARA CONTRATAÇÃO",
            "",
            f"PROJETO: {projeto_titulo}",
            f"SETOR: {setor}",
            f"VALOR ESTIMADO: {valor_estimado}",
        ]
        
        if itens_pac:
            parts.append(f"\nITENS DO PAC: {json.dumps(itens_pac, ensure_ascii=False)}")
        
        if dfd:
            parts.append("\nDADOS DO DFD:")
            if dfd.get("descricao_objeto_padronizada"):
                parts.append(f"- Objeto: {dfd['descricao_objeto_padronizada']}")
            if dfd.get("justificativa_tecnica"):
                parts.append(f"- Justificativa: {dfd['justificativa_tecnica']}")
        
        if pesquisa:
            parts.append("\nDADOS DA PESQUISA DE PREÇOS:")
            if pesquisa.get("valor_total"):
                parts.append(f"- Valor Total: R$ {pesquisa['valor_total']:,.2f}")
            if pesquisa.get("quantidade_fornecedores"):
                parts.append(f"- Fornecedores: {pesquisa['quantidade_fornecedores']}")
            if pesquisa.get("coeficiente_variacao"):
                parts.append(f"- CV: {pesquisa['coeficiente_variacao']:.1f}%")
        
        parts.append("""
TAREFA: Gerar análise completa de riscos com 5-10 riscos principais.

Para cada risco, fornecer:
- origem: 'DFD', 'Cotacao', 'PAC', ou 'Externo'
- fase_licitacao: 'Planejamento', 'Selecao_Fornecedor', ou 'Gestao_Contratual'
- categoria: 'Tecnico', 'Administrativo', 'Juridico', 'Economico', 'Reputacional'
- evento, causa, consequencia (formato "Se... então...")
- probabilidade (1-5), impacto (1-5)
- justificativa_probabilidade, justificativa_impacto
- tipo_tratamento: 'Mitigar', 'Transferir', 'Aceitar', 'Evitar'
- acoes_preventivas, acoes_contingencia
- alocacao_responsavel: 'Contratante', 'Contratada', 'Compartilhado'
- gatilho_monitoramento, responsavel_monitoramento
- frequencia_monitoramento: 'Semanal', 'Quinzenal', 'Mensal', 'Trimestral'

SCHEMA JSON:
{
  "identificacao_objeto": "Resumo do objeto",
  "valor_estimado_total": 50000.00,
  "metodologia_adotada": "Matriz 5x5 (Probabilidade vs Impacto)",
  "data_revisao": "2026-02-01",
  "resumo_analise_planejamento": "...",
  "resumo_analise_selecao": "...",
  "resumo_analise_gestao": "...",
  "itens_risco": [
    {
      "origem": "DFD",
      "fase_licitacao": "Planejamento",
      "categoria": "Tecnico",
      "evento": "...",
      "causa": "...",
      "consequencia": "...",
      "probabilidade": 3,
      "impacto": 4,
      "justificativa_probabilidade": "...",
      "justificativa_impacto": "...",
      "tipo_tratamento": "Mitigar",
      "acoes_preventivas": "...",
      "acoes_contingencia": "...",
      "alocacao_responsavel": "Contratante",
      "gatilho_monitoramento": "...",
      "responsavel_monitoramento": "Gestor do Contrato",
      "frequencia_monitoramento": "Mensal"
    }
  ]
}

Retorne APENAS o JSON válido.""")
        
        return "\n".join(parts)
