"""
Serviço de Lógica de Negócios para Artefatos.

Este módulo centraliza a lógica de mapeamento e processamento de dados para os
diferentes tipos de artefatos do sistema (ETP, TR, Riscos, etc.). Ele atua como
uma camada intermediária entre o Router e os Modelos de Banco de Dados.
"""
import json
from typing import Dict, Any, List
from app.models.artefatos import ARTEFATO_MAP


# ========== FUNCOES AUXILIARES ==========

def _to_text(val) -> str:
    """Converte valor para texto (string, dict ou list)."""
    if val is None:
        return ""
    if isinstance(val, dict):
        return json.dumps(val, ensure_ascii=False, indent=2)
    elif isinstance(val, list):
        return json.dumps(val, ensure_ascii=False, indent=2)
    return str(val)


def _consolidar(*parts) -> str:
    """Consolida multiplas partes de texto em uma string."""
    textos = [_to_text(p) for p in parts if p]
    return "\n\n".join(textos) if textos else ""


def _formatar_requisitos_contratacao(requisitos) -> str:
    """Formata requisitos de contratação (objeto ou texto) para texto."""
    if isinstance(requisitos, dict):
        partes = []
        if requisitos.get('negocios'):
            partes.append(f"**Requisitos de Negócio:**\n{requisitos['negocios']}")
        if requisitos.get('tecnicos'):
            partes.append(f"**Requisitos Técnicos:**\n{requisitos['tecnicos']}")
        if requisitos.get('temporais'):
            partes.append(f"**Requisitos Temporais:**\n{requisitos['temporais']}")
        if requisitos.get('qualificacao'):
            partes.append(f"**Qualificação Técnica:**\n{requisitos['qualificacao']}")
        return "\n\n".join(partes) if partes else ""
    return _to_text(requisitos)


def _formatar_levantamento_mercado(levantamento) -> str:
    """Formata levantamento de mercado (objeto ou texto) para texto."""
    if isinstance(levantamento, dict):
        partes = []
        solucoes = levantamento.get('solucoes', [])
        if solucoes:
            partes.append("**Soluções Identificadas:**")
            for i, sol in enumerate(solucoes, 1):
                partes.append(f"{i}. {sol}")
        if levantamento.get('conclusao'):
            partes.append(f"\n**Conclusão:**\n{levantamento['conclusao']}")
        return "\n".join(partes) if partes else ""
    return _to_text(levantamento)


def _formatar_estimativa_quantidades(estimativa) -> str:
    """Formata estimativa de quantidades (lista ou texto) para texto."""
    if isinstance(estimativa, list):
        partes = ["**Memória de Cálculo:**\n"]
        for item in estimativa:
            if isinstance(item, dict):
                nome = item.get('item', 'Item')
                qtd = item.get('quantidade', 0)
                unidade = item.get('unidade', 'un')
                valor = item.get('valor_unitario', 0)
                partes.append(f"- {nome}: {qtd} {unidade} x R$ {valor:.2f} = R$ {qtd * valor:.2f}")
            else:
                partes.append(f"- {item}")
        return "\n".join(partes)
    return _to_text(estimativa)


def _formatar_estimativa_valor(estimativa) -> str:
    """Formata estimativa de valor (objeto ou texto) para texto."""
    if isinstance(estimativa, dict):
        partes = []
        if estimativa.get('metodologia'):
            partes.append(f"**Metodologia:**\n{estimativa['metodologia']}")
        if estimativa.get('valor_total') is not None:
            partes.append(f"**Valor Total Estimado:** R$ {estimativa['valor_total']:,.2f}")
        return "\n\n".join(partes) if partes else ""
    return _to_text(estimativa)


def _formatar_contratacoes_correlatas(correlatas) -> str:
    """Formata contratações correlatas (lista ou texto) para texto."""
    if isinstance(correlatas, list):
        partes = ["**Contratações Interdependentes:**\n"]
        for i, item in enumerate(correlatas, 1):
            partes.append(f"{i}. {item}")
        return "\n".join(partes)
    return _to_text(correlatas)


def _formatar_riscos_criticos(riscos) -> str:
    """Formata riscos críticos (lista ou texto) para texto."""
    if isinstance(riscos, list):
        if not riscos:
            return "Não foram identificados riscos críticos que inviabilizem a contratação."
        partes = ["**Riscos Críticos Identificados:**\n"]
        for i, risco in enumerate(riscos, 1):
            if isinstance(risco, dict):
                desc = risco.get('risco', risco.get('descricao', str(risco)))
                nivel = risco.get('nivel', '')
                mitig = risco.get('mitigacao', '')
                partes.append(f"{i}. {desc}")
                if nivel:
                    partes.append(f"   - Nível: {nivel}")
                if mitig:
                    partes.append(f"   - Mitigação: {mitig}")
            else:
                partes.append(f"{i}. {risco}")
        return "\n".join(partes)
    return _to_text(riscos)


def mapear_campos_artefato(tipo: str, content: Dict[str, Any]) -> Dict[str, Any]:
    """Mapeia os campos do JSON gerado pela IA para o modelo de dados do banco.

    Recebe o conteúdo bruto (JSON) da IA e o transforma em um dicionário
    compatível com os campos do modelo SQLAlchemy correspondente ao tipo de artefato.

    Args:
        tipo (str): O tipo de artefato (ex: 'etp', 'tr', 'riscos').
        content (Dict[str, Any]): O conteúdo JSON retornado pela IA.

    Returns:
        Dict[str, Any]: Dicionário com as chaves corretas para criação/atualização no banco.
    """
    if tipo == "etp":
        # Processar campos estruturados para texto
        requisitos = content.get('requisitos_contratacao', '')
        levantamento = content.get('levantamento_mercado', '')
        estimativa_qtd = content.get('estimativa_quantidades', '')
        estimativa_val = content.get('estimativa_valor', '')
        correlatas = content.get('contratacoes_correlatas', '')
        riscos = content.get('riscos_criticos', [])
        
        # Extrair valor total se presente em estimativa_valor
        valor_total = None
        if isinstance(estimativa_val, dict):
            valor_total = estimativa_val.get('valor_total')
        
        return {
            # ETP-01: Descrição da Necessidade
            "descricao_necessidade": _to_text(content.get('descricao_necessidade', '')),
            # ETP-02: Área Requisitante
            "area_requisitante": _to_text(content.get('area_requisitante', '')),
            # ETP-03: Requisitos da Contratação
            "requisitos_contratacao": _formatar_requisitos_contratacao(requisitos),
            # ETP-04: Estimativa de Quantidades
            "estimativa_quantidades": _formatar_estimativa_quantidades(estimativa_qtd),
            "quantidades_detalhadas": estimativa_qtd if isinstance(estimativa_qtd, list) else None,
            # ETP-05: Levantamento de Mercado
            "levantamento_mercado": _formatar_levantamento_mercado(levantamento),
            "cenarios_mercado": levantamento.get('solucoes') if isinstance(levantamento, dict) else None,
            # ETP-06: Estimativa de Valor
            "estimativa_valor": _formatar_estimativa_valor(estimativa_val),
            "valor_total_estimado": valor_total,
            # ETP-07: Descrição da Solução
            "descricao_solucao": _to_text(content.get('descricao_solucao', '')),
            # ETP-08: Parcelamento
            "justificativa_parcelamento": _to_text(content.get('justificativa_parcelamento', '')),
            # ETP-09: Contratações Correlatas
            "contratacoes_correlatas": _formatar_contratacoes_correlatas(correlatas),
            "contratacoes_correlatas_lista": correlatas if isinstance(correlatas, list) else None,
            # ETP-10: Alinhamento PCA
            "alinhamento_pca": _to_text(content.get('alinhamento_pca', '')),
            # ETP-11: Resultados Pretendidos
            "resultados_pretendidos": _to_text(content.get('resultados_pretendidos', '')),
            # ETP-12: Providências Prévias
            "providencias_previas": _to_text(content.get('providencias_previas', '')),
            # ETP-13: Impactos Ambientais
            "impactos_ambientais": _to_text(content.get('impactos_ambientais', '')),
            # ETP-14: Análise de Riscos (resumo do PGR)
            "analise_riscos": _formatar_riscos_criticos(riscos),
            "riscos_criticos": riscos if isinstance(riscos, list) else None,
            # ETP-15: Viabilidade da Contratação
            "viabilidade_contratacao": _to_text(content.get('viabilidade_contratacao', '')),
        }

    elif tipo == "tr":
        return {
            "definicao_objeto": _consolidar(content.get('definicao_objeto')),
            "justificativa": _consolidar(content.get('fundamentacao_legal')),
            "especificacao_tecnica": _consolidar(
                content.get('descricao_solucao'),
                content.get('requisitos_contratacao'),
                content.get('modelo_execucao'),
                content.get('modelo_gestao')
            ),
            "obrigacoes": _consolidar(
                content.get('obrigacoes_contratante'),
                content.get('obrigacoes_contratada'),
                content.get('sancoes')
            ),
            "criterios_aceitacao": _consolidar(
                content.get('criterios_medicao'),
                content.get('condicoes_pagamento'),
                content.get('vigencia')
            ),
        }

    elif tipo == "riscos":
        return {
            "identificacao": _to_text(
                content.get('identificacao', content.get('identificação', ''))
            ),
            "riscos_planejamento": _to_text(
                content.get('riscos_planejamento', content.get('riscos_fase_planejamento', ''))
            ),
            "riscos_selecao": _to_text(
                content.get('riscos_selecao', content.get('riscos_fase_selecao', ''))
            ),
            "riscos_gestao": _to_text(
                content.get('riscos_gestao', content.get('riscos_fase_gestao_contratual', ''))
            ),
            "matriz_riscos": _to_text(
                content.get('matriz_riscos', content.get('matriz', ''))
            ),
            "tratamento_riscos": _to_text(
                content.get('tratamento_riscos', content.get('plano_comunicacao_riscos', ''))
            ),
            "plano_comunicacao": _to_text(
                content.get('plano_comunicacao', content.get('comunicacao', ''))
            ),
            "content_blocks": content,
        }

    elif tipo == "edital":
        return {
            "objeto": _consolidar(
                content.get('preambulo'),
                content.get('objeto'),
                content.get('prazos'),
                content.get('sistema_eletronico')
            ),
            "condicoes_participacao": _consolidar(content.get('condicoes_participacao')),
            "criterios_julgamento": _consolidar(content.get('proposta')),
            "fase_lances": _consolidar(
                content.get('sessao_publica'),
                content.get('recursos'),
                content.get('penalidades'),
                content.get('pagamento'),
                content.get('disposicoes_finais')
            ),
        }

    elif tipo == "pesquisa_precos":
        return {
            "content_blocks": content,
        }

    elif tipo == "checklist_conformidade":
        return {
            "dfd_presente": content.get('dfd_presente', 'nao'),
            "dfd_folhas": content.get('dfd_folhas', ''),
            "etp_presente": content.get('etp_presente', 'nao'),
            "etp_folhas": content.get('etp_folhas', ''),
            "tr_presente": content.get('tr_presente', 'nao'),
            "tr_folhas": content.get('tr_folhas', ''),
            "matriz_riscos_presente": content.get('matriz_riscos_presente', 'nao'),
            "matriz_riscos_folhas": content.get('matriz_riscos_folhas', ''),
            "disponibilidade_orcamentaria_presente": content.get('disponibilidade_orcamentaria_presente', 'nao'),
            "disponibilidade_orcamentaria_folhas": content.get('disponibilidade_orcamentaria_folhas', ''),
            "parecer_juridico_presente": content.get('parecer_juridico_presente', 'nao'),
            "parecer_juridico_folhas": content.get('parecer_juridico_folhas', ''),
            "validado_por": content.get('validado_por', ''),
            "observacoes_gerais": content.get('observacoes_gerais', ''),
            "status_conformidade": content.get('status_conformidade', 'nao_conforme'),
            "itens_verificacao": content.get('itens_verificacao', []),
        }

    return {}
