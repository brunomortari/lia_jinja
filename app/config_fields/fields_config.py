"""
Sistema LIA - Configurações de Campos de Artefatos
===================================================
Define as configurações de campos para UI e IA dos artefatos.
Cada campo tem metadados para renderização, validação e geração por IA.

Tipos de Campo:
- Tipo A = Apenas edição manual (readonly ou input do usuário)
- Tipo B = Pode ser regenerado por IA

Autor: Equipe TRE-GO
Data: Janeiro 2026
"""

from typing import Dict, Any


# ========== DFD - Documento de Formalização da Demanda ==========

DFD_CAMPOS_CONFIG: Dict[str, Any] = {
    # ========== CAMPOS AUTOMATICOS (Sistema preenche) ==========
    "numero_dfd": {
        "label": "Número do DFD",
        "tipo": "A",
        "descricao": "Gerado sequencialmente pelo banco de dados.",
        "placeholder": "Automático",
        "readonly": True,
        "fonte": "sistema"
    },
    "setor_requisitante": {
        "label": "Setor Requisitante",
        "tipo": "A",
        "descricao": "Setor do usuário logado.",
        "placeholder": "Setor requisitante...",
        "readonly": True,
        "fonte": "usuario.setor"
    },
    "responsavel_requisitante": {
        "label": "Responsável pela Demanda",
        "tipo": "A",
        "descricao": "Nome do usuário logado.",
        "placeholder": "Nome do responsável...",
        "readonly": True,
        "fonte": "usuario.nome"
    },
    "alinhamento_pca": {
        "label": "Alinhamento ao PCA",
        "tipo": "A",
        "descricao": "Itens do PAC vinculados ao projeto.",
        "placeholder": "Itens do PAC...",
        "readonly": True,
        "fonte": "projeto.itens_pac"
    },
    "valor_estimado": {
        "label": "Estimativa Preliminar",
        "tipo": "A",
        "descricao": "Calculado: quantidade_projeto x valor_por_item do PAC.",
        "placeholder": "0,00",
        "input_type": "number",
        "readonly": True,
        "fonte": "pac.valor_por_item"
    },
    "grau_prioridade": {
        "label": "Grau de Prioridade",
        "tipo": "A",
        "descricao": "Prioridade dos itens do PAC (P1=Alta, P2-P3=Média, P4-P5=Baixa).",
        "placeholder": "Prioridade...",
        "readonly": True,
        "fonte": "pac.prioridade"
    },
    "alinhamento_estrategico": {
        "label": "Alinhamento Estratégico",
        "tipo": "A",
        "descricao": "Objetivo estratégico dos itens do PAC.",
        "placeholder": "Objetivo estratégico...",
        "readonly": True,
        "fonte": "pac.objetivo"
    },

    # ========== CAMPOS PREENCHIDOS PELO USUARIO (antes da geracao) ==========
    "data_pretendida": {
        "label": "Data Pretendida para Contratação",
        "tipo": "A",
        "descricao": "Meta de disponibilização informada pelo usuário.",
        "placeholder": "dd/mm/aaaa",
        "input_type": "date",
        "input_usuario": True
    },
    "responsavel_gestor": {
        "label": "Gestor do Contrato",
        "tipo": "A",
        "descricao": "Nome do servidor que será o gestor do contrato.",
        "placeholder": "Nome completo do gestor",
        "input_usuario": True
    },
    "responsavel_fiscal": {
        "label": "Fiscal do Contrato",
        "tipo": "A",
        "descricao": "Nome do servidor que será o fiscal do contrato.",
        "placeholder": "Nome completo do fiscal",
        "input_usuario": True
    },

    # ========== CAMPOS GERADOS PELA IA ==========
    "descricao_objeto": {
        "label": "Descrição do Objeto",
        "tipo": "B",
        "descricao": "Resumo do objeto padronizado pela IA conforme Catálogo.",
        "placeholder": "Descrição gerada pela IA...",
        "campo_ia": "descricao_objeto_padronizada"
    },
    "justificativa": {
        "label": "Justificativa da Necessidade",
        "tipo": "B",
        "descricao": "Fundamentação no interesse público gerada pela IA.",
        "placeholder": "Justificativa gerada...",
        "campo_ia": "justificativa_tecnica"
    }
}


# ========== ETP - Estudo Técnico Preliminar ==========
# Estrutura conforme Lei 14.133/2021, Art. 18, §1º e IN SEGES/ME nº 58/2022

ETP_CAMPOS_CONFIG: Dict[str, Any] = {
    # ETP-01: Descrição da Necessidade
    "descricao_necessidade": {
        "label": "Descrição da Necessidade",
        "tipo": "B",
        "campo_ia": "descricao_necessidade",
        "descricao": "Fundamentação do interesse público e impacto da não-contratação.",
        "placeholder": "Descreva o contexto, o problema atual e a necessidade de negócio..."
    },
    # ETP-02: Área Requisitante
    "area_requisitante": {
        "label": "Área Requisitante",
        "tipo": "B",
        "campo_ia": "area_requisitante",
        "descricao": "Unidade/Setor que demanda a contratação.",
        "placeholder": "Informe a unidade requisitante..."
    },
    # ETP-03: Requisitos da Contratação
    "requisitos_contratacao": {
        "label": "Requisitos da Contratação",
        "tipo": "B",
        "campo_ia": "requisitos_contratacao",
        "descricao": "Requisitos técnicos, normas (ISO, ABNT), garantias, certificações.",
        "placeholder": "Liste os requisitos de negócio e técnicos..."
    },
    # ETP-04: Estimativa de Quantidades
    "estimativa_quantidades": {
        "label": "Estimativa de Quantidades",
        "tipo": "B",
        "campo_ia": "estimativa_quantidades",
        "descricao": "Memória de cálculo: (Consumo Médio x 12) + Margem de Segurança.",
        "placeholder": "Detalhe a memória de cálculo das quantidades..."
    },
    # ETP-05: Levantamento de Mercado
    "levantamento_mercado": {
        "label": "Levantamento de Mercado",
        "tipo": "B",
        "campo_ia": "levantamento_mercado",
        "descricao": "Análise comparativa de soluções: Compra vs Locação, SaaS vs Perpétua, etc.",
        "placeholder": "Descreva as soluções identificadas no mercado..."
    },
    # ETP-06: Estimativa de Valor
    "estimativa_valor": {
        "label": "Estimativa de Valor",
        "tipo": "B",
        "campo_ia": "estimativa_valor",
        "descricao": "Valor global/unitário com descrição da metodologia (Média, Mediana, Menor).",
        "placeholder": "Informe a estimativa de valor e metodologia..."
    },
    # ETP-07: Descrição da Solução
    "descricao_solucao": {
        "label": "Descrição da Solução",
        "tipo": "B",
        "campo_ia": "descricao_solucao",
        "descricao": "Definição do objeto com a solução escolhida do levantamento de mercado.",
        "placeholder": "Descreva a solução escolhida..."
    },
    # ETP-08: Parcelamento
    "justificativa_parcelamento": {
        "label": "Justificativa de Parcelamento",
        "tipo": "B",
        "campo_ia": "justificativa_parcelamento",
        "descricao": "Análise de divisibilidade: parcelamento ou justificativa para lote único.",
        "placeholder": "Justifique o parcelamento ou lote único..."
    },
    # ETP-09: Contratações Correlatas
    "contratacoes_correlatas": {
        "label": "Contratações Correlatas",
        "tipo": "B",
        "campo_ia": "contratacoes_correlatas",
        "descricao": "Contratações interdependentes (ex: Ar Condicionado -> Instalação Elétrica).",
        "placeholder": "Liste contratações correlatas, se houver..."
    },
    # ETP-10: Alinhamento ao PCA
    "alinhamento_pca": {
        "label": "Alinhamento ao PCA",
        "tipo": "B",
        "campo_ia": "alinhamento_pca",
        "descricao": "Verificação de constância no Plano de Contratações Anual.",
        "placeholder": "Informe o alinhamento com o PCA..."
    },
    # ETP-11: Resultados Pretendidos
    "resultados_pretendidos": {
        "label": "Resultados Pretendidos",
        "tipo": "B",
        "campo_ia": "resultados_pretendidos",
        "descricao": "Benefícios esperados: economicidade, eficácia, eficiência.",
        "placeholder": "Descreva os resultados esperados..."
    },
    # ETP-12: Providências Prévias
    "providencias_previas": {
        "label": "Providências Prévias",
        "tipo": "B",
        "campo_ia": "providencias_previas",
        "descricao": "Ações prévias: adequação de espaço, capacitação, infraestrutura.",
        "placeholder": "Liste as providências prévias necessárias..."
    },
    # ETP-13: Impactos Ambientais
    "impactos_ambientais": {
        "label": "Impactos Ambientais",
        "tipo": "B",
        "campo_ia": "impactos_ambientais",
        "descricao": "Medidas de sustentabilidade, logística reversa, critérios ambientais.",
        "placeholder": "Descreva os impactos e critérios ambientais..."
    },
    # ETP-14: Viabilidade da Contratação
    "viabilidade_contratacao": {
        "label": "Viabilidade da Contratação",
        "tipo": "B",
        "campo_ia": "viabilidade_contratacao",
        "descricao": "Declaração formal de viabilidade técnica e econômica.",
        "placeholder": "Declare a viabilidade da contratação..."
    },
    # ETP-15: Riscos Críticos (resumo do PGR)
    "riscos_criticos": {
        "label": "Riscos Críticos",
        "tipo": "B",
        "campo_ia": "riscos_criticos",
        "descricao": "Resumo dos riscos Alto/Extremo com mitigadoras (vinculado ao PGR).",
        "placeholder": "Liste os riscos críticos identificados..."
    },
}


# ========== TR - Termo de Referência ==========

TR_CAMPOS_CONFIG: Dict[str, Any] = {
    "definicao_objeto": {
        "label": "Definicao do Objeto",
        "tipo": "B",
        "campo_ia": "objeto",
        "descricao": "Descricao completa do objeto da contratacao, natureza e fundamentacao legal.",
        "placeholder": "Descreva o objeto da contratacao de forma detalhada..."
    },
    "justificativa": {
        "label": "Justificativa e Fundamentacao",
        "tipo": "B",
        "campo_ia": "justificativa",
        "descricao": "Fundamentacao legal, modalidade e justificativa da contratacao.",
        "placeholder": "Fundamente a modalidade e justifique a contratacao..."
    },
    "especificacao_tecnica": {
        "label": "Especificacao Tecnica",
        "tipo": "B",
        "campo_ia": "especificacao",
        "descricao": "Especificacoes tecnicas, requisitos de qualificacao e modelo de execucao.",
        "placeholder": "Detalhe as especificacoes tecnicas e requisitos..."
    },
    "obrigacoes": {
        "label": "Obrigacoes das Partes",
        "tipo": "B",
        "campo_ia": "obrigacoes",
        "descricao": "Obrigacoes do contratante e da contratada durante a execucao.",
        "placeholder": "Liste as obrigacoes de cada parte..."
    },
    "criterios_aceitacao": {
        "label": "Criterios de Aceitacao e Pagamento",
        "tipo": "B",
        "campo_ia": "aceitacao",
        "descricao": "Criterios de medicao, aceitacao e condicoes de pagamento.",
        "placeholder": "Defina os criterios de aceitacao e pagamento..."
    },
}


# ========== PGR/Riscos - Plano de Gerenciamento de Riscos ==========

RISCOS_CAMPOS_CONFIG: Dict[str, Any] = {
    # --- Identificação do PGR ---
    "identificacao_processo": {
        "label": "Identificação do Processo",
        "tipo": "B",
        "campo_ia": "identificacao_processo",
        "descricao": "Nome e descrição resumida do processo licitatório",
        "placeholder": "Ex: Aquisição de Servidor Web para TI - Edital nº 001/2026"
    },
    "valor_estimado_total": {
        "label": "Valor Estimado Total",
        "tipo": "A",
        "descricao": "Derivado das cotações/ETP. Define criticalidade da análise.",
        "readonly": True,
        "fonte": "cotacoes.valor_total"
    },
    
    # --- Metodologia ---
    "metodologia_adotada": {
        "label": "Metodologia de Análise",
        "tipo": "A",
        "descricao": "Método usado para avaliação de riscos",
        "placeholder": "Ex: Matriz 5x5, ISO 31000, MR-MPS"
    },
    
    # --- Itens de Risco (Nova Estrutura - A Carne do PGR) ---
    "lista_riscos_identificados": {
        "label": "Matriz de Riscos Estruturada",
        "tipo": "B",
        "campo_ia": "lista_riscos_identificados",
        "descricao": "Lista de riscos com evento, causa, probabilidade, impacto, tratamento e alocação",
        "input_type": "json",
        "descricao_detalhada": """
        Cada item contém:
        - evento: O que pode acontecer?
        - causa: Por quê? (IA extrai de DFD, Cotações, PAC)
        - consequencia: Qual o impacto?
        - origem: Enum(DFD, Cotacao, PAC, Externo)
        - fase_licitacao: Enum(Planejamento, Selecao_Fornecedor, Gestao_Contratual)
        - categoria: Enum(Tecnico, Administrativo, Juridico, Economico, Reputacional)
        - probabilidade: 1-5 (com justificativa)
        - impacto: 1-5 (com justificativa)
        - nivel_risco: 1-25 (calculado = prob × impacto)
        - tipo_tratamento: Enum(Mitigar, Transferir, Aceitar, Evitar)
        - acoes_preventivas: O fazer ANTES para evitar
        - acoes_contingencia: O que fazer SE OCORRER
        - alocacao_responsavel: Enum(Contratante, Contratada, Compartilhado) [Lei 14.133]
        - gatilho_monitoramento: Sinal de alerta
        - responsavel_monitoramento: Quem monitora?
        - frequencia_monitoramento: Enum(Semanal, Quinzenal, Mensal, Trimestral)
        """
    },
    
    # --- Consolidações por Fase ---
    "resumo_analise_planejamento": {
        "label": "Resumo de Riscos - Fase Planejamento",
        "tipo": "B",
        "campo_ia": "resumo_analise_planejamento",
        "descricao": "Sumarização gerada pela IA dos riscos da fase de planejamento (derive de lista_riscos_identificados)",
        "placeholder": "A IA gera automaticamente a partir dos itens de risco..."
    },
    "resumo_analise_selecao": {
        "label": "Resumo de Riscos - Fase Seleção",
        "tipo": "B",
        "campo_ia": "resumo_analise_selecao",
        "descricao": "Sumarização gerada pela IA dos riscos da fase de seleção",
        "placeholder": "A IA gera automaticamente a partir dos itens de risco..."
    },
    "resumo_analise_gestao": {
        "label": "Resumo de Riscos - Fase Gestão Contratual",
        "tipo": "B",
        "campo_ia": "resumo_analise_gestao",
        "descricao": "Sumarização gerada pela IA dos riscos da fase de gestão",
        "placeholder": "A IA gera automaticamente a partir dos itens de risco..."
    },
    
    # --- Matriz de Alocação (Lei 14.133) ---
    "matriz_alocacao_responsabilidades": {
        "label": "Matriz de Alocação de Responsabilidades",
        "tipo": "A",
        "descricao": "Agrupamento de riscos por quem assume: Contratante, Contratada ou Compartilhado",
        "input_type": "json",
        "readonly": True,
        "descricao_detalhada": """
        Estrutura JSON que agrupa itens de risco por alocacao_responsavel.
        Fundamental para Lei 14.133/21 e geração automática de cláusulas contratuais.
        """
    },
    
    # --- Planos de Ação ---
    "plano_mitigacao_preventivo": {
        "label": "Plano de Mitigação Preventiva",
        "tipo": "B",
        "campo_ia": "plano_mitigacao_preventivo",
        "descricao": "Resumo consolidado das ações preventivas (derive de lista_riscos_identificados)",
        "placeholder": "A IA gera a partir das acoes_preventivas dos itens..."
    },
    "plano_contingencia": {
        "label": "Plano de Contingência",
        "tipo": "B",
        "campo_ia": "plano_contingencia",
        "descricao": "Resumo consolidado do que fazer se riscos se materializarem",
        "placeholder": "A IA gera a partir das acoes_contingencia dos itens..."
    },
    
    # --- Comunicação ---
    "plano_comunicacao": {
        "label": "Plano de Comunicação de Riscos",
        "tipo": "B",
        "campo_ia": "plano_comunicacao",
        "descricao": "Como comunicar riscos? A quem? Com que frequência?",
        "input_type": "json",
        "descricao_detalhada": """
        JSON array de objetos:
        [{stakeholder, formato, frequencia, conteudo}, ...]
        Ex: {stakeholder: 'Fiscal', formato: 'Email', frequencia: 'Semanal', conteudo: 'Status de Riscos'}
        """
    },
    
    # --- Visualização ---
    "mapa_calor_riscos": {
        "label": "Mapa de Calor (Matriz 5x5)",
        "tipo": "A",
        "descricao": "Visualização de riscos por Probabilidade vs Impacto",
        "input_type": "json",
        "readonly": True,
        "descricao_detalhada": "Gerado automaticamente a partir de lista_riscos_identificados para renderizar matriz"
    },
}


# ========== Edital de Licitação ==========

EDITAL_CAMPOS_CONFIG: Dict[str, Any] = {
    "objeto": {
        "label": "Objeto da Licitacao",
        "tipo": "B",
        "campo_ia": "objeto",
        "descricao": "Preambulo, objeto, valor estimado e dotacao orcamentaria.",
        "placeholder": "Descreva o objeto e valor estimado da licitacao..."
    },
    "condicoes_participacao": {
        "label": "Condicoes de Participacao",
        "tipo": "B",
        "campo_ia": "participacao",
        "descricao": "Impedimentos, requisitos de habilitacao juridica, fiscal, economica e tecnica.",
        "placeholder": "Defina as condicoes e requisitos de participacao..."
    },
    "criterios_julgamento": {
        "label": "Criterios de Julgamento",
        "tipo": "B",
        "campo_ia": "julgamento",
        "descricao": "Requisitos da proposta, criterio de julgamento e modo de disputa.",
        "placeholder": "Estabeleca os criterios de julgamento das propostas..."
    },
    "fase_lances": {
        "label": "Sessao Publica e Recursos",
        "tipo": "B",
        "campo_ia": "lances",
        "descricao": "Fases da sessao, recursos, penalidades e disposicoes finais.",
        "placeholder": "Descreva as fases da sessao e prazo de recursos..."
    },
}


# ========== Pesquisa de Preços ==========

PESQUISA_PRECOS_CAMPOS_CONFIG: Dict[str, Any] = {
    "content_blocks": {
        "label": "Conteudo da Pesquisa de Precos",
        "tipo": "B",
        "campo_ia": "content_blocks",
        "descricao": "Estrutura JSON completa com identificacao, itens, fontes, cotacoes e analise.",
        "placeholder": "Estrutura JSON gerada pela IA...",
        "input_type": "json"
    },
}

# ========== PORTARIA DE DESIGNAÇÃO ==========
# Documento virtual - sem campos editáveis. PDF renderizado sob demanda do DFD.

PORTARIA_DESIGNACAO_CAMPOS_CONFIG: Dict[str, Any] = {
    # Portaria de Designação é um documento virtual - não possui campos de edição
    # Seu conteúdo é gerado automaticamente a partir do DFD aprovado
}


# ========== RDVE - Relatório de Demonstração de Vantagem Econômica ==========

RDVE_CAMPOS_CONFIG: Dict[str, Any] = {
    "comparativo_precos": {
        "label": "Comparativo de Preços",
        "tipo": "B",
        "campo_ia": "comparativo_precos",
        "descricao": "Análise de preços entre adesão à ata e contratação direta",
        "input_type": "json",
        "placeholder": "Fornecedor | Preço Ata | Preço Direto | Economia %"
    },
    "custo_processamento_adesao": {
        "label": "Custos de Processamento - Adesão",
        "tipo": "A",
        "descricao": "Custos administrativos da adesão (despacho, termo, etc)",
        "placeholder": "R$ 0,00"
    },
    "custo_processamento_direto": {
        "label": "Custos de Processamento - Contratação Direta",
        "tipo": "A",
        "descricao": "Custos administrativos de contratação direta",
        "placeholder": "R$ 0,00"
    },
    "conclusao_tecnica": {
        "label": "Conclusão Técnica",
        "tipo": "B",
        "campo_ia": "conclusao_tecnica",
        "descricao": "Conclusão sobre a vantagem econômica comprovada",
        "placeholder": "A adesão à ata apresenta vantagem de..."
    },
    "percentual_economia": {
        "label": "Percentual de Economia",
        "tipo": "A",
        "descricao": "Percentual economizado (%)",
        "placeholder": "0,00%"
    },
    "valor_economia_total": {
        "label": "Valor Total de Economia",
        "tipo": "A",
        "descricao": "Valor absoluto economizado (R$)",
        "placeholder": "R$ 0,00"
    },
}


# ========== JVA - Justificativa de Vantagem e Conveniência da Adesão ==========

JVA_CAMPOS_CONFIG: Dict[str, Any] = {
    "fundamentacao_legal": {
        "label": "Fundamentação Legal",
        "tipo": "B",
        "campo_ia": "fundamentacao_legal",
        "descricao": "Citação da Lei 14.133/21, Art. 37 e jurisprudência aplicável",
        "placeholder": "Art. 37 da Lei 14.133/2021 autoriza a adesão..."
    },
    "justificativa_conveniencia": {
        "label": "Justificativa de Conveniência",
        "tipo": "B",
        "campo_ia": "justificativa_conveniencia",
        "descricao": "Por que adesão é mais conveniente que contratação direta",
        "placeholder": "A adesão é mais conveniente porque..."
    },
    "declaracao_conformidade": {
        "label": "Declaração de Conformidade",
        "tipo": "B",
        "campo_ia": "declaracao_conformidade",
        "descricao": "Declara conformidade com Lei 14.133/21 e regulamentos internos",
        "placeholder": "Declaro conformidade com as normas aplicáveis..."
    },
}


# ========== TAFO - Termo de Aceite do Fornecedor pela Administração ==========

TAFO_CAMPOS_CONFIG: Dict[str, Any] = {
    "nome_fornecedor": {
        "label": "Nome do Fornecedor",
        "tipo": "A",
        "descricao": "Nome da empresa fornecedora",
        "placeholder": "Razão social do fornecedor..."
    },
    "cnpj_fornecedor": {
        "label": "CNPJ do Fornecedor",
        "tipo": "A",
        "descricao": "CNPJ da empresa",
        "placeholder": "00.000.000/0000-00"
    },
    "descricao_objeto_aceito": {
        "label": "Descrição do Objeto Aceito",
        "tipo": "B",
        "campo_ia": "descricao_objeto_aceito",
        "descricao": "Descrição detalhada do objeto aceito da ata",
        "placeholder": "Objeto: ..."
    },
    "preco_aceito": {
        "label": "Preço Aceito",
        "tipo": "A",
        "descricao": "Preço final aceito da ata",
        "placeholder": "R$ 0,00"
    },
    "documentos_anexados": {
        "label": "Documentos Anexados",
        "tipo": "A",
        "descricao": "Arquivos anexados (propostas, certidões, etc)",
        "input_type": "file_list"
    },
    "responsaveis_assinatura": {
        "label": "Responsáveis pela Assinatura",
        "tipo": "A",
        "descricao": "Nomes e cargos dos assinantes",
        "input_type": "json"
    },
    "observacoes": {
        "label": "Observações",
        "tipo": "A",
        "descricao": "Observações adicionais",
        "placeholder": "Observações..."
    },
}


# ========== TRS - Termo de Referência Simplificado ==========

TRS_CAMPOS_CONFIG: Dict[str, Any] = {
    "especificacao_objeto": {
        "label": "Especificação do Objeto",
        "tipo": "B",
        "campo_ia": "especificacao_objeto",
        "descricao": "Especificação técnica do objeto (versão simplificada)",
        "placeholder": "Especifique o objeto de forma concisa..."
    },
    "criterios_qualidade_simplificados": {
        "label": "Critérios de Qualidade",
        "tipo": "B",
        "campo_ia": "criterios_qualidade_simplificados",
        "descricao": "Critérios de qualidade reduzidos",
        "input_type": "json",
        "placeholder": "[{critério, descrição}, ...]"
    },
    "prazos_simplificados": {
        "label": "Prazos de Execução",
        "tipo": "A",
        "descricao": "Prazos resumidos de execução/entrega",
        "placeholder": "Prazo de entrega: XX dias"
    },
    "valor_referencia_dispensa": {
        "label": "Valor de Referência",
        "tipo": "A",
        "descricao": "Valor de referência para justificar dispensa",
        "placeholder": "R$ 0,00"
    },
    "justificativa_dispensa_valor": {
        "label": "Justificativa da Dispensa",
        "tipo": "B",
        "campo_ia": "justificativa_dispensa_valor",
        "descricao": "Por que valor baixo justifica esta dispensa",
        "placeholder": "O valor reduzido justifica a dispensa porque..."
    },
}


# ========== ADE - Aviso de Dispensa Eletrônica ==========

ADE_CAMPOS_CONFIG: Dict[str, Any] = {
    "numero_aviso": {
        "label": "Número do Aviso",
        "tipo": "A",
        "descricao": "Número do aviso atribuído pelo portal",
        "placeholder": "Número automático",
        "readonly": True
    },
    "data_publicacao": {
        "label": "Data de Publicação",
        "tipo": "A",
        "descricao": "Data de publicação no portal eletrônico",
        "placeholder": "DD/MM/AAAA"
    },
    "descricao_objeto_aviso": {
        "label": "Descrição do Objeto",
        "tipo": "B",
        "campo_ia": "descricao_objeto_aviso",
        "descricao": "Descrição do objeto publicado no aviso",
        "placeholder": "Descrição..."
    },
    "link_portal": {
        "label": "Link do Portal",
        "tipo": "A",
        "descricao": "URL do aviso no portal eletrônico",
        "placeholder": "https://..."
    },
    "protocolo_publicacao": {
        "label": "Protocolo de Publicação",
        "tipo": "A",
        "descricao": "Número de protocolo do aviso",
        "placeholder": "00000000000"
    },
}


# ========== JPEF - Justificativa de Preço e Escolha de Fornecedor ==========

JPEF_CAMPOS_CONFIG: Dict[str, Any] = {
    "justificativa_fornecedor": {
        "label": "Justificativa da Escolha do Fornecedor",
        "tipo": "B",
        "campo_ia": "justificativa_fornecedor",
        "descricao": "Motivos da escolha deste fornecedor específico",
        "placeholder": "O fornecedor foi escolhido porque..."
    },
    "analise_preco_praticado": {
        "label": "Análise do Preço",
        "tipo": "B",
        "campo_ia": "analise_preco_praticado",
        "descricao": "Análise do preço praticado vs mercado",
        "placeholder": "Análise comparativa de preços..."
    },
    "preco_final_contratacao": {
        "label": "Preço Final",
        "tipo": "A",
        "descricao": "Preço final negociado para a contratação",
        "placeholder": "R$ 0,00"
    },
}


# ========== CE - Certidão de Enquadramento ==========

CE_CAMPOS_CONFIG: Dict[str, Any] = {
    "limite_legal_aplicavel": {
        "label": "Limite Legal Aplicável",
        "tipo": "A",
        "descricao": "Limite legal para enquadramento",
        "placeholder": "R$ 8.800,00"
    },
    "valor_contratacao_analisada": {
        "label": "Valor da Contratação",
        "tipo": "A",
        "descricao": "Valor da contratação analisada",
        "placeholder": "R$ 0,00"
    },
    "conclusao_enquadramento": {
        "label": "Conclusão de Enquadramento",
        "tipo": "B",
        "campo_ia": "conclusao_enquadramento",
        "descricao": "Conclusão sobre o enquadramento legal",
        "placeholder": "A contratação enquadra-se em..."
    },
    "artigo_lei_aplicavel": {
        "label": "Artigo da Lei Aplicável",
        "tipo": "A",
        "descricao": "Artigo da Lei 14.133/21 aplicável",
        "placeholder": "Art. 75, I"
    },
    "responsavel_certificacao": {
        "label": "Responsável pela Certificação",
        "tipo": "A",
        "descricao": "Nome e cargo do responsável",
        "placeholder": "Nome do responsável..."
    },
    "data_certificacao": {
        "label": "Data da Certificação",
        "tipo": "A",
        "descricao": "Data da certificação",
        "placeholder": "DD/MM/AAAA"
    },
}


# ========== CHECKLIST_CONFORMIDADE - Checklist de Instrução (AGU/SEGES) ==========

CHECKLIST_CONFORMIDADE_CAMPOS_CONFIG: Dict[str, Any] = {
    "itens_verificacao": {
        "label": "Itens de Verificação",
        "tipo": "B",
        "campo_ia": "itens_verificacao",
        "descricao": "Lista estruturada de itens verificados",
        "placeholder": "JSON com itens: [{item, descricao, status, referencia_folhas}, ...]"
    },
    "dfd_presente": {
        "label": "DFD Presente",
        "tipo": "A",
        "descricao": "Verificação de presença do DFD",
        "placeholder": "sim/nao/nao_se_aplica"
    },
    "dfd_folhas": {
        "label": "Referência DFD (Folhas)",
        "tipo": "A",
        "descricao": "Número de páginas/ID no processo",
        "placeholder": "Fls. 10-25, ID: SEI-123456"
    },
    "etp_presente": {
        "label": "ETP Presente",
        "tipo": "A",
        "descricao": "Verificação de presença do ETP",
        "placeholder": "sim/nao/nao_se_aplica"
    },
    "etp_folhas": {
        "label": "Referência ETP (Folhas)",
        "tipo": "A",
        "descricao": "Número de páginas/ID no processo",
        "placeholder": "Fls. 26-60"
    },
    "tr_presente": {
        "label": "TR Presente",
        "tipo": "A",
        "descricao": "Verificação de presença do TR",
        "placeholder": "sim/nao/nao_se_aplica"
    },
    "tr_folhas": {
        "label": "Referência TR (Folhas)",
        "tipo": "A",
        "descricao": "Número de páginas/ID no processo",
        "placeholder": "Fls. 61-90"
    },
    "matriz_riscos_presente": {
        "label": "Matriz de Riscos Presente",
        "tipo": "A",
        "descricao": "Verificação de presença da Matriz de Riscos",
        "placeholder": "sim/nao/nao_se_aplica"
    },
    "matriz_riscos_folhas": {
        "label": "Referência Matriz de Riscos (Folhas)",
        "tipo": "A",
        "descricao": "Número de páginas/ID no processo",
        "placeholder": "Fls. 91-100"
    },
    "disponibilidade_orcamentaria_presente": {
        "label": "Disponibilidade Orçamentária Presente",
        "tipo": "A",
        "descricao": "Verificação de disponibilidade orçamentária",
        "placeholder": "sim/nao/nao_se_aplica"
    },
    "disponibilidade_orcamentaria_folhas": {
        "label": "Referência Disponibilidade Orçamentária (Folhas)",
        "tipo": "A",
        "descricao": "Número de páginas/ID no processo",
        "placeholder": "Fls. 101-105"
    },
    "parecer_juridico_presente": {
        "label": "Parecer Jurídico Presente",
        "tipo": "A",
        "descricao": "Verificação de presença do parecer jurídico",
        "placeholder": "sim/nao/nao_se_aplica"
    },
    "parecer_juridico_folhas": {
        "label": "Referência Parecer Jurídico (Folhas)",
        "tipo": "A",
        "descricao": "Número de páginas/ID no processo",
        "placeholder": "Fls. 106-120"
    },
    "validado_por": {
        "label": "Validado Por",
        "tipo": "A",
        "descricao": "Nome e cargo da autoridade que validou",
        "placeholder": "Nome Completo - Cargo"
    },
    "assinatura_eletronica": {
        "label": "Assinatura Eletrônica",
        "tipo": "A",
        "descricao": "Dados da assinatura eletrônica",
        "placeholder": "JSON: {nome, cargo, cpf, data, hash}"
    },
    "observacoes_gerais": {
        "label": "Observações Gerais",
        "tipo": "B",
        "campo_ia": "observacoes_gerais",
        "descricao": "Observações ou pendências identificadas",
        "placeholder": "Observações adicionais..."
    },
    "status_conformidade": {
        "label": "Status de Conformidade",
        "tipo": "A",
        "descricao": "Status geral de conformidade",
        "placeholder": "conforme/nao_conforme/conforme_com_ressalvas"
    },
}


# ========== MINUTA_CONTRATO - Minuta de Contrato ==========

MINUTA_CONTRATO_CAMPOS_CONFIG: Dict[str, Any] = {
    "obrigacoes_contratada": {
        "label": "Obrigações da Contratada",
        "tipo": "B",
        "campo_ia": "obrigacoes_contratada",
        "descricao": "Responsabilidades da contratada",
        "placeholder": "A contratada deverá..."
    },
    "obrigacoes_contratante": {
        "label": "Obrigações da Contratante",
        "tipo": "B",
        "campo_ia": "obrigacoes_contratante",
        "descricao": "Responsabilidades da contratante",
        "placeholder": "A contratante deverá..."
    },
    "obrigacoes_estruturadas": {
        "label": "Obrigações Estruturadas",
        "tipo": "B",
        "campo_ia": "obrigacoes_estruturadas",
        "descricao": "Estrutura JSON de obrigações",
        "placeholder": "JSON: {contratada: [...], contratante: [...]}"
    },
    "forma_pagamento": {
        "label": "Forma de Pagamento",
        "tipo": "B",
        "campo_ia": "forma_pagamento",
        "descricao": "Descrição da forma de pagamento",
        "placeholder": "Pagamento mediante..."
    },
    "prazo_pagamento": {
        "label": "Prazo de Pagamento",
        "tipo": "A",
        "descricao": "Prazo para pagamento",
        "placeholder": "30 dias após apresentação da nota fiscal"
    },
    "fluxo_liquidacao": {
        "label": "Fluxo de Liquidação",
        "tipo": "B",
        "campo_ia": "fluxo_liquidacao",
        "descricao": "Fluxo de liquidação e nota fiscal",
        "placeholder": "Descrição do fluxo..."
    },
    "data_inicio": {
        "label": "Data de Início",
        "tipo": "A",
        "descricao": "Data de início do contrato",
        "placeholder": "DD/MM/AAAA",
        "input_type": "date"
    },
    "data_termino": {
        "label": "Data de Término",
        "tipo": "A",
        "descricao": "Data de término do contrato",
        "placeholder": "DD/MM/AAAA",
        "input_type": "date"
    },
    "prazo_vigencia": {
        "label": "Prazo de Vigência",
        "tipo": "A",
        "descricao": "Prazo de vigência do contrato",
        "placeholder": "12 meses"
    },
    "possibilidade_prorrogacao": {
        "label": "Possibilidade de Prorrogação",
        "tipo": "A",
        "descricao": "Se permite prorrogação",
        "placeholder": "sim/nao"
    },
    "condicoes_prorrogacao": {
        "label": "Condições de Prorrogação",
        "tipo": "B",
        "campo_ia": "condicoes_prorrogacao",
        "descricao": "Condições para prorrogação",
        "placeholder": "A prorrogação poderá ocorrer..."
    },
    "prazo_maximo_prorrogacao": {
        "label": "Prazo Máximo de Prorrogação",
        "tipo": "A",
        "descricao": "Prazo máximo permitido",
        "placeholder": "Até 60 meses conforme Art. 107"
    },
    "exige_garantia": {
        "label": "Exige Garantia",
        "tipo": "A",
        "descricao": "Se exige garantia contratual",
        "placeholder": "sim/nao"
    },
    "tipo_garantia": {
        "label": "Tipo de Garantia",
        "tipo": "A",
        "descricao": "Tipos de garantia aceitos",
        "placeholder": "Seguro-garantia, caução, fiança bancária"
    },
    "percentual_garantia": {
        "label": "Percentual da Garantia",
        "tipo": "A",
        "descricao": "Percentual sobre o valor do contrato",
        "placeholder": "5%",
        "input_type": "number"
    },
    "valor_garantia": {
        "label": "Valor da Garantia",
        "tipo": "A",
        "descricao": "Valor da garantia em R$",
        "placeholder": "R$ 0,00",
        "input_type": "number"
    },
    "rescisao": {
        "label": "Condições de Rescisão",
        "tipo": "B",
        "campo_ia": "rescisao",
        "descricao": "Condições de rescisão do contrato",
        "placeholder": "O contrato poderá ser rescindido..."
    },
    "penalidades": {
        "label": "Penalidades",
        "tipo": "B",
        "campo_ia": "penalidades",
        "descricao": "Penalidades por descumprimento",
        "placeholder": "Em caso de descumprimento..."
    },
    "lei_aplicavel": {
        "label": "Lei Aplicável",
        "tipo": "B",
        "campo_ia": "lei_aplicavel",
        "descricao": "Lei e regulamentos aplicáveis",
        "placeholder": "Lei 14.133/2021 e demais normas..."
    },
    "foro_competente": {
        "label": "Foro Competente",
        "tipo": "A",
        "descricao": "Foro competente para dirimir conflitos",
        "placeholder": "Foro da Comarca de..."
    },
}


# ========== AVISO_PUBLICIDADE_DIRETA - Aviso de Dispensa de Licitação ==========

AVISO_PUBLICIDADE_DIRETA_CAMPOS_CONFIG: Dict[str, Any] = {
    "fundamento_legal": {
        "label": "Fundamento Legal",
        "tipo": "A",
        "descricao": "Inciso específico da Lei 14.133/21",
        "placeholder": "Art. 75, II"
    },
    "artigo_lei": {
        "label": "Artigo da Lei",
        "tipo": "A",
        "descricao": "Artigo específico da lei",
        "placeholder": "Art. 75, II ou Art. 74, I"
    },
    "justificativa_legal": {
        "label": "Justificativa Legal",
        "tipo": "B",
        "campo_ia": "justificativa_legal",
        "descricao": "Explicação do enquadramento",
        "placeholder": "A contratação enquadra-se na hipótese de dispensa..."
    },
    "valor_estimado": {
        "label": "Valor Estimado",
        "tipo": "A",
        "descricao": "Teto da administração",
        "placeholder": "R$ 0,00",
        "input_type": "number"
    },
    "metodologia_valor": {
        "label": "Metodologia do Valor",
        "tipo": "B",
        "campo_ia": "metodologia_valor",
        "descricao": "Como foi calculado o valor",
        "placeholder": "Valor calculado com base em..."
    },
    "prazo_manifestacao_dias": {
        "label": "Prazo de Manifestação (dias)",
        "tipo": "A",
        "descricao": "Dias úteis para manifestação (mínimo 3)",
        "placeholder": "3",
        "input_type": "number"
    },
    "data_inicio_prazo": {
        "label": "Data de Início do Prazo",
        "tipo": "A",
        "descricao": "Data de início do prazo",
        "placeholder": "DD/MM/AAAA",
        "input_type": "date"
    },
    "data_fim_prazo": {
        "label": "Data de Fim do Prazo",
        "tipo": "A",
        "descricao": "Data de término do prazo",
        "placeholder": "DD/MM/AAAA",
        "input_type": "date"
    },
    "data_publicacao_pncp": {
        "label": "Data de Publicação PNCP",
        "tipo": "A",
        "descricao": "Data de publicação no PNCP",
        "placeholder": "DD/MM/AAAA HH:MM"
    },
    "link_pncp": {
        "label": "Link PNCP",
        "tipo": "A",
        "descricao": "Link para o aviso no PNCP",
        "placeholder": "https://pncp.gov.br/..."
    },
    "data_publicacao_site_orgao": {
        "label": "Data de Publicação Site do Órgão",
        "tipo": "A",
        "descricao": "Data de publicação no site do órgão",
        "placeholder": "DD/MM/AAAA HH:MM"
    },
    "link_site_orgao": {
        "label": "Link Site do Órgão",
        "tipo": "A",
        "descricao": "Link para o aviso no site",
        "placeholder": "https://..."
    },
    "numero_aviso": {
        "label": "Número do Aviso",
        "tipo": "A",
        "descricao": "Número de identificação do aviso",
        "placeholder": "AVISO-001/2026"
    },
    "extrato_aviso": {
        "label": "Extrato do Aviso",
        "tipo": "B",
        "campo_ia": "extrato_aviso",
        "descricao": "Extrato resumido do aviso",
        "placeholder": "Aviso de Dispensa de Licitação..."
    },
}


# ========== JUSTIFICATIVA_FORNECEDOR_ESCOLHIDO - Justificativa do Fornecedor ==========

JUSTIFICATIVA_FORNECEDOR_CAMPOS_CONFIG: Dict[str, Any] = {
    "nome_fornecedor": {
        "label": "Nome do Fornecedor",
        "tipo": "A",
        "descricao": "Razão social do fornecedor",
        "placeholder": "Razão Social Ltda."
    },
    "cnpj_fornecedor": {
        "label": "CNPJ",
        "tipo": "A",
        "descricao": "CNPJ do fornecedor",
        "placeholder": "00.000.000/0000-00"
    },
    "endereco_fornecedor": {
        "label": "Endereço",
        "tipo": "A",
        "descricao": "Endereço completo",
        "placeholder": "Rua, Número, Bairro, Cidade-UF, CEP"
    },
    "qualificacao_tecnica": {
        "label": "Qualificação Técnica",
        "tipo": "B",
        "campo_ia": "qualificacao_tecnica",
        "descricao": "Provas de expertise única",
        "placeholder": "O fornecedor possui expertise comprovada em..."
    },
    "atestados_capacidade": {
        "label": "Atestados de Capacidade",
        "tipo": "A",
        "descricao": "Atestados de capacidade técnica",
        "placeholder": "JSON: [{tipo, descricao, data, orgao}, ...]"
    },
    "experiencia_comprovada": {
        "label": "Experiência Comprovada",
        "tipo": "B",
        "campo_ia": "experiencia_comprovada",
        "descricao": "Descrição da experiência",
        "placeholder": "Histórico de atuação..."
    },
    "certidao_federal": {
        "label": "Certidão Federal",
        "tipo": "A",
        "descricao": "Certidão Negativa Federal",
        "placeholder": "JSON: {numero, data, validade, situacao}"
    },
    "certidao_estadual": {
        "label": "Certidão Estadual",
        "tipo": "A",
        "descricao": "Certidão Negativa Estadual",
        "placeholder": "JSON: {numero, data, validade, situacao}"
    },
    "certidao_municipal": {
        "label": "Certidão Municipal",
        "tipo": "A",
        "descricao": "Certidão Negativa Municipal",
        "placeholder": "JSON: {numero, data, validade, situacao}"
    },
    "certidao_fgts": {
        "label": "Certidão FGTS",
        "tipo": "A",
        "descricao": "Certidão de Regularidade do FGTS",
        "placeholder": "JSON: {numero, data, validade, situacao}"
    },
    "certidao_trabalhista": {
        "label": "Certidão Trabalhista",
        "tipo": "A",
        "descricao": "Certidão Negativa Trabalhista",
        "placeholder": "JSON: {numero, data, validade, situacao}"
    },
    "certidoes_anexadas": {
        "label": "Certidões Anexadas",
        "tipo": "A",
        "descricao": "Conjunto completo de certidões",
        "placeholder": "JSON: [{tipo, arquivo, data_upload}, ...]"
    },
    "inviabilidade_competicao": {
        "label": "Inviabilidade de Competição",
        "tipo": "A",
        "descricao": "Se há inviabilidade de competir",
        "placeholder": "sim/nao"
    },
    "justificativa_inviabilidade": {
        "label": "Justificativa da Inviabilidade",
        "tipo": "B",
        "campo_ia": "justificativa_inviabilidade",
        "descricao": "Por que não é possível licitar",
        "placeholder": "A inviabilidade decorre de..."
    },
    "tipo_inviabilidade": {
        "label": "Tipo de Inviabilidade",
        "tipo": "A",
        "descricao": "Tipo específico",
        "placeholder": "Fornecedor Exclusivo / Notória Especialização"
    },
    "documentacao_exclusividade": {
        "label": "Documentação de Exclusividade",
        "tipo": "A",
        "descricao": "Documentos que comprovam exclusividade",
        "placeholder": "JSON: [{tipo, descricao, arquivo}, ...]"
    },
    "preco_proposto": {
        "label": "Preço Proposto",
        "tipo": "A",
        "descricao": "Preço proposto pelo fornecedor",
        "placeholder": "R$ 0,00",
        "input_type": "number"
    },
    "analise_compatibilidade_preco": {
        "label": "Análise de Compatibilidade de Preço",
        "tipo": "B",
        "campo_ia": "analise_compatibilidade_preco",
        "descricao": "Análise de compatibilidade com mercado",
        "placeholder": "O preço proposto é compatível com..."
    },
    "valores_referencia": {
        "label": "Valores de Referência",
        "tipo": "A",
        "descricao": "Valores de referência para comparação",
        "placeholder": "JSON: [{fonte, valor, data}, ...]"
    },
    "conclusao_justificativa": {
        "label": "Conclusão da Justificativa",
        "tipo": "B",
        "campo_ia": "conclusao_justificativa",
        "descricao": "Conclusão sobre adequação do fornecedor",
        "placeholder": "Conclui-se que o fornecedor..."
    },
}


# ========== JEP - Justificativa de Excepcionalidade ao Planejamento ==========

JEP_CAMPOS_CONFIG: Dict[str, Any] = {
    "motivo_inclusao": {
        "label": "Motivação da Extemporaneidade",
        "tipo": "B",
        "campo_ia": "motivo_inclusao",
        "descricao": "Explicação detalhada do porquê o item não foi incluído no PAC durante o período de planejamento. Ex: Surgimento de nova tecnologia, alteração legislativa, evento imprevisível.",
        "placeholder": "Descreva o motivo pelo qual esta contratação não foi prevista no PAC..."
    },
    "risco_adiamento": {
        "label": "Análise de Urgência/Prioridade",
        "tipo": "B",
        "campo_ia": "risco_adiamento",
        "descricao": "Demonstração de que a contratação não pode esperar o próximo ciclo de planejamento (próximo ano). Ex: Risco de interrupção de serviço essencial.",
        "placeholder": "Explique o que acontece se esta contratação for adiada para o próximo ciclo..."
    },
    "impacto_planejamento": {
        "label": "Impacto no Planejamento Existente",
        "tipo": "B",
        "campo_ia": "impacto_planejamento",
        "descricao": "Declaração de que a inclusão desta nova demanda não prejudicará a execução das demais contratações já previstas no PAC.",
        "placeholder": "Declare o impacto (ou ausência dele) nas contratações já planejadas..."
    },
    "alinhamento_estrategico": {
        "label": "Alinhamento Estratégico",
        "tipo": "B",
        "campo_ia": "alinhamento_estrategico",
        "descricao": "Justificativa de como esta contratação, mesmo fora do plano, contribui para os objetivos estratégicos do órgão.",
        "placeholder": "Justifique como esta contratação se alinha aos objetivos do órgão..."
    },
    "parecer_autoridade": {
        "label": "Parecer da Autoridade Competente",
        "tipo": "A",
        "descricao": "Decisão (Aprovo/Reprovo) do ordenador de despesas que autoriza a quebra do planejamento original.",
        "placeholder": "Parecer da autoridade competente..."
    },
    "autorizacao_especial": {
        "label": "Autorização da Autoridade",
        "tipo": "A",
        "descricao": "Validação formal da autoridade superior autorizando a contratação fora do PAC.",
        "input_type": "checkbox"
    },
    "tipo_excepcionalidade": {
        "label": "Classificação do Motivo",
        "tipo": "A",
        "descricao": "Tipo de excepcionalidade para fins de auditoria e estatísticas.",
        "input_type": "select",
        "options": [
            {"value": "emergencia", "label": "Emergência/Calamidade"},
            {"value": "alteracao_legislativa", "label": "Alteração Legislativa"},
            {"value": "tecnologia_superveniente", "label": "Tecnologia Superveniente"},
            {"value": "demanda_judicial", "label": "Demanda Judicial/Determinação TCU"},
            {"value": "outro", "label": "Outro"}
        ]
    },
}


# ========== Exportação centralizada ==========

__all__ = [
    "DFD_CAMPOS_CONFIG",
    "ETP_CAMPOS_CONFIG",
    "TR_CAMPOS_CONFIG",
    "RISCOS_CAMPOS_CONFIG",
    "EDITAL_CAMPOS_CONFIG",
    "PESQUISA_PRECOS_CAMPOS_CONFIG",
    "PORTARIA_DESIGNACAO_CAMPOS_CONFIG",
    "RDVE_CAMPOS_CONFIG",
    "JVA_CAMPOS_CONFIG",
    "TAFO_CAMPOS_CONFIG",
    "TRS_CAMPOS_CONFIG",
    "ADE_CAMPOS_CONFIG",
    "JPEF_CAMPOS_CONFIG",
    "CE_CAMPOS_CONFIG",
    "CHECKLIST_CONFORMIDADE_CAMPOS_CONFIG",
    "MINUTA_CONTRATO_CAMPOS_CONFIG",
    "AVISO_PUBLICIDADE_DIRETA_CAMPOS_CONFIG",
    "JUSTIFICATIVA_FORNECEDOR_CAMPOS_CONFIG",
    "JEP_CAMPOS_CONFIG",
]
