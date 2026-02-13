""" 
Sistema LIA - Modelos ETP
=========================
Estudo Técnico Preliminar (ETP) - Lei 14.133/2021, Art. 18, §1º.

Autor: Equipe TRE-GO
Data: Fevereiro 2026
"""

from sqlalchemy import Column, Integer, String, Text, Float, Boolean, DateTime, Date, ForeignKey, JSON
from sqlalchemy.orm import relationship
from .base import ArtefatoBase


class ETP(ArtefatoBase):
    """
    Estudo Técnico Preliminar (ETP) - Lei 14.133/2021, Art. 18, §1º
    
    Estrutura baseada na IN SEGES/ME nº 58/2022 e taxonomia do sistema LIA.
    Cada campo possui fundamentação legal e estratégia de preenchimento via IA.
    """
    __tablename__ = "etps"

    projeto_id = Column(Integer, ForeignKey("projetos.id"), nullable=False)
    projeto = relationship("Projeto", back_populates="etps")

    # ========== ETP-01: Descrição da Necessidade ==========
    descricao_necessidade = Column(Text, nullable=True,
        comment="Fundamentação do interesse público e impacto da não-contratação")
    
    # ========== ETP-02: Área Requisitante ==========
    area_requisitante = Column(String(300), nullable=True,
        comment="Unidade/Setor que demanda a contratação")
    
    # ========== ETP-03: Requisitos da Contratação ==========
    requisitos_contratacao = Column(Text, nullable=True,
        comment="Requisitos técnicos, normas (ISO, ABNT), garantias, certificações")
    
    # ========== ETP-04: Estimativa de Quantidades ==========
    estimativa_quantidades = Column(Text, nullable=True,
        comment="Memória de cálculo: (Consumo Médio x 12) + Margem de Segurança")
    
    quantidades_detalhadas = Column(JSON, nullable=True,
        comment="JSON: [{item, qtd_solicitada, consumo_medio, justificativa}, ...]")
    
    # ========== ETP-05: Levantamento de Mercado ==========
    levantamento_mercado = Column(Text, nullable=True,
        comment="Análise comparativa de soluções: Compra vs Locação, SaaS vs Perpétua, etc")
    
    cenarios_mercado = Column(JSON, nullable=True,
        comment="JSON: [{cenario, descricao, pros, contras, valor_estimado}, ...]")
    
    # ========== ETP-06: Estimativa do Valor ==========
    estimativa_valor = Column(Text, nullable=True,
        comment="Valor global/unitário com descrição da metodologia (Média, Mediana, Menor)")
    
    valor_total_estimado = Column(Float, nullable=True, comment="Valor total em R$")
    metodologia_preco = Column(String(100), nullable=True, comment="Metodologia: media, mediana, menor_preco")
    data_base_preco = Column(Date, nullable=True, comment="Data base da pesquisa de preços")
    cotacao_id_referencia = Column(Integer, nullable=True, comment="ID da cotação vinculada")
    
    # ========== ETP-07: Descrição da Solução ==========
    descricao_solucao = Column(Text, nullable=True,
        comment="Definição do objeto com a solução escolhida do levantamento de mercado")
    
    solucao_escolhida = Column(String(200), nullable=True, comment="Nome/tipo da solução escolhida")
    
    # ========== ETP-08: Parcelamento do Objeto ==========
    justificativa_parcelamento = Column(Text, nullable=True,
        comment="Análise de divisibilidade: parcelamento ou justificativa para lote único")
    
    parcelamento_aplicavel = Column(String(20), nullable=True, comment="Enum: sim, nao, parcial")
    
    # ========== ETP-09: Contratações Correlatas ==========
    contratacoes_correlatas = Column(Text, nullable=True,
        comment="Contratações interdependentes")
    
    contratacoes_correlatas_lista = Column(JSON, nullable=True,
        comment="JSON: [{objeto, justificativa, processo_sei}, ...]")
    
    # ========== ETP-10: Alinhamento ao PCA ==========
    alinhamento_pca = Column(Text, nullable=True,
        comment="Verificação de constância no Plano de Contratações Anual")
    
    pca_ano = Column(Integer, nullable=True, comment="Ano do PCA")
    pca_item_id = Column(String(50), nullable=True, comment="ID do item no PCA")
    
    # ========== ETP-11: Resultados Pretendidos ==========
    resultados_pretendidos = Column(Text, nullable=True,
        comment="Benefícios esperados: economicidade, eficácia, eficiência")
    
    # ========== ETP-12: Providências Prévias ==========
    providencias_previas = Column(Text, nullable=True,
        comment="Ações prévias: adequação de espaço, capacitação, infraestrutura")
    
    providencias_checklist = Column(JSON, nullable=True,
        comment="JSON: [{providencia, responsavel, prazo, status}, ...]")
    
    # ========== ETP-13: Impactos Ambientais ==========
    impactos_ambientais = Column(Text, nullable=True,
        comment="Medidas de sustentabilidade, logística reversa, critérios ambientais")
    
    criterios_sustentabilidade = Column(JSON, nullable=True,
        comment="JSON: [{criterio, aplicavel, justificativa}, ...]")
    
    # ========== ETP-14: Análise de Riscos ==========
    analise_riscos = Column(Text, nullable=True,
        comment="Resumo dos riscos Alto/Extremo com mitigadoras")
    
    riscos_criticos = Column(JSON, nullable=True,
        comment="JSON: [{risco, nivel, probabilidade, impacto, mitigacao}, ...]")
    pgr_id_referencia = Column(Integer, nullable=True, comment="ID do PGR vinculado")
    
    # ========== ETP-15: Viabilidade da Contratação ==========
    viabilidade_contratacao = Column(Text, nullable=True,
        comment="Declaração formal de viabilidade técnica e econômica")
    
    declaracao_viabilidade = Column(String(50), nullable=True,
        comment="Enum: viavel, inviavel, viavel_com_ressalvas")
    
    # ========== METADADOS DE INTEGRAÇÃO ==========
    dfd_id_referencia = Column(Integer, nullable=True, comment="ID do DFD que originou este ETP")
    sincronizado = Column(Integer, default=1, comment="1=sincronizado, 0=módulo fonte alterado")
    checklist_conformidade = Column(JSON, nullable=True)
    
    # ========== ADESÃO DE ATA DE REGISTRO ==========
    adesao_ata_habilitada = Column(Boolean, default=False,
        comment="Usuário habilitou busca por adesão em ata de registro de preços")
    
    fase_adesao_ata = Column(String(50), nullable=True,
        comment="Enum: nao_iniciada, buscando_atas, ata_selecionada, deep_research_ativo, concluida")
    
    ata_selecionada = Column(JSON, nullable=True,
        comment="JSON com dados da ata selecionada")
    
    deep_research_ativado = Column(Boolean, default=False,
        comment="Flag para indicar que deep_research foi automaticamente ativado")
    
    responsaveis = Column(JSON, nullable=True,
        comment="JSON: [{nome, cargo, data_assinatura}, ...]")
    
    # ========== DECISÃO DE MODALIDADE ==========
    modalidade_sugerida = Column(String(50), nullable=True,
        comment="Enum: adesao_ata, dispensa_valor_baixo, licitacao_normal")
    
    modalidade_definida = Column(String(50), nullable=True,
        comment="Enum: adesao_ata, dispensa_valor_baixo, licitacao_normal, contratacao_direta")
    
    data_definicao_modalidade = Column(DateTime, nullable=True,
        comment="Data em que modalidade foi definida pelo usuário")
    
    justificativa_modalidade = Column(Text, nullable=True,
        comment="Justificativa técnica/legal para escolha da modalidade")
    
    criterios_analise_modalidade = Column(JSON, nullable=True,
        comment="JSON: {valor_limite: float, adesao_atas_disponiveis: bool, etc}")
