"""
Sistema LIA - Agente ETP
========================
Estudo Técnico Preliminar (Lei 14.133/2021, art. 18, §1º e IN 58/2022)

O ETP contém 15 campos obrigatórios conforme a legislação:
1. Descrição da necessidade
2. Área requisitante
3. Descrição dos requisitos
4. Estimativa das quantidades
5. Levantamento de mercado
6. Estimativa do valor
7. Descrição da solução
8. Justificativa técnica
9. Justificativa econômica
10. Benefícios
11. Providências prévias
12. Contratações correlatas
13. Impactos ambientais
14. Posicionamento do demandante
15. Viabilidade ou não da contratação

Autor: Equipe TRE-GO
Data: Janeiro 2026
"""

import json
from typing import Dict, Any

from .base_agent import BaseAgent


class ETPAgent(BaseAgent):
    """
    Agente especializado em Estudo Técnico Preliminar (ETP).
    
    O ETP é documento preparatório que fundamenta tecnicamente
    a contratação pública, conforme Lei 14.133/2021 e IN 58/2022.
    """
    
    agent_type = "etp"
    temperature = 0.5
    
    campos = [
        "descricao_necessidade",
        "area_requisitante", 
        "descricao_requisitos",
        "estimativa_quantidades",
        "levantamento_mercado",
        "estimativa_valor",
        "descricao_solucao",
        "justificativa_tecnica",
        "justificativa_economica",
        "beneficios",
        "providencias_previas",
        "contratacoes_correlatas",
        "impactos_ambientais",
        "posicionamento_demandante",
        "viabilidade_contratacao",
    ]
    
    system_prompt = """Você é um Especialista em Estudos Técnicos Preliminares conforme Lei 14.133/2021 (art. 18, §1º) e IN SEGES/ME nº 58/2022. Seu papel é elaborar ETPs completos e fundamentados para contratações públicas.

LEGISLAÇÃO BASE:
- Lei 14.133/2021, art. 18, §1º: Elementos obrigatórios do ETP
- IN SEGES/ME nº 58/2022: Procedimentos para elaboração do ETP
- Decreto 10.947/2022: Planejamento das contratações

DIRETRIZES:
1. Linguagem formal, técnica e impessoal
2. Fundamentar cada campo com base legal quando aplicável
3. Ser objetivo e direto, evitando redundâncias
4. Demonstrar o nexo entre a necessidade e a solução proposta
5. Considerar aspectos de sustentabilidade (art. 11, Lei 14.133)
6. Retornar APENAS JSON válido, sem markdown, sem explicações

SAÍDA ESPERADA (JSON com 15 campos obrigatórios):
{
  "descricao_necessidade": "Descrição detalhada da necessidade que origina a contratação, demonstrando o problema a ser resolvido e sua relevância para a Administração.",
  "area_requisitante": "Nome da unidade/setor requisitante com suas competências regimentais.",
  "descricao_requisitos": "Requisitos técnicos, funcionais e de desempenho que a solução deve atender, incluindo níveis de serviço esperados.",
  "estimativa_quantidades": "Quantitativos estimados com memória de cálculo, metodologia utilizada e período de referência.",
  "levantamento_mercado": "Análise das soluções disponíveis no mercado, comparativo entre alternativas e justificativa da escolha.",
  "estimativa_valor": "Valor estimado da contratação com metodologia de pesquisa de preços conforme IN 65/2021.",
  "descricao_solucao": "Descrição completa da solução escolhida, incluindo bens, serviços, ou combinação necessária.",
  "justificativa_tecnica": "Razões técnicas que fundamentam a escolha da solução, demonstrando adequação aos requisitos.",
  "justificativa_economica": "Demonstração da economicidade e vantajosidade da solução escolhida frente às alternativas.",
  "beneficios": "Resultados e benefícios esperados com a contratação para a Administração.",
  "providencias_previas": "Ações preparatórias necessárias antes da contratação (capacitação, infraestrutura, etc.).",
  "contratacoes_correlatas": "Identificação de contratos vigentes relacionados e análise de possível agregação de demandas.",
  "impactos_ambientais": "Análise de impactos ambientais e medidas de sustentabilidade conforme art. 11 da Lei 14.133.",
  "posicionamento_demandante": "Declaração formal da área requisitante sobre a necessidade e urgência da contratação.",
  "viabilidade_contratacao": "Conclusão sobre a viabilidade ou não da contratação, com parecer técnico fundamentado."
}"""
    
    def build_user_prompt(self, contexto: Dict[str, Any]) -> str:
        """Constrói o prompt do usuário para geração do ETP."""
        
        projeto_titulo = contexto.get("projeto_titulo", "")
        setor = contexto.get("setor_usuario", "Unidade Requisitante")
        itens_pac = contexto.get("itens_pac", [])
        
        # Dados do DFD (se existir)
        dfd = contexto.get("dfd", {})
        
        # Dados da pesquisa de preços (se existir)
        pesquisa = contexto.get("pesquisa_precos", {})
        
        parts = [
            "ELABORAR ESTUDO TÉCNICO PRELIMINAR",
            "",
            f"PROJETO: {projeto_titulo}",
            f"SETOR REQUISITANTE: {setor}",
        ]
        
        if itens_pac:
            parts.append(f"\nITENS DO PAC: {json.dumps(itens_pac, ensure_ascii=False)}")
        
        if dfd:
            parts.append("\nDADOS DO DFD:")
            if dfd.get("justificativa_tecnica"):
                parts.append(f"- Justificativa: {dfd['justificativa_tecnica']}")
            if dfd.get("descricao_objeto_padronizada"):
                parts.append(f"- Objeto: {dfd['descricao_objeto_padronizada']}")
        
        if pesquisa:
            parts.append("\nDADOS DA PESQUISA DE PREÇOS:")
            if pesquisa.get("valor_total"):
                parts.append(f"- Valor Total Estimado: R$ {pesquisa['valor_total']:,.2f}")
            if pesquisa.get("quantidade_fornecedores"):
                parts.append(f"- Fornecedores Consultados: {pesquisa['quantidade_fornecedores']}")
        
        parts.append("""
Gere o ETP completo com os 15 campos obrigatórios:
1. descricao_necessidade
2. area_requisitante
3. descricao_requisitos
4. estimativa_quantidades
5. levantamento_mercado
6. estimativa_valor
7. descricao_solucao
8. justificativa_tecnica
9. justificativa_economica
10. beneficios
11. providencias_previas
12. contratacoes_correlatas
13. impactos_ambientais
14. posicionamento_demandante
15. viabilidade_contratacao

Retorne APENAS o JSON válido.""")
        
        return "\n".join(parts)
