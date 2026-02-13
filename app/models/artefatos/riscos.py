""" 
Sistema LIA - Modelos de Riscos
================================
Plano de Gerenciamento de Riscos (PGR).

Autor: Equipe TRE-GO
Data: Fevereiro 2026
"""

from sqlalchemy import Column, Integer, String, Text, Float, DateTime, ForeignKey, JSON
from sqlalchemy.orm import relationship
from .base import ArtefatoBase
from app.utils.datetime_utils import now_brasilia


class Riscos(ArtefatoBase):
    """Plano de Gerenciamento de Riscos (PGR) - INTELIGENTE
    
    Um PGR por Processo de Contratação (Lei 14.133/21).
    Vinculado a projeto_id (representa o processo licitatório).
    Contém múltiplos ItemRisco estruturados para análise e monitoramento.
    """
    __tablename__ = "riscos"

    projeto_id = Column(Integer, ForeignKey("projetos.id"), nullable=False)
    projeto = relationship("Projeto", back_populates="riscos")
    
    artefatos_base = Column(JSON, nullable=True, 
        comment="IDs dos artefatos usados na análise")

    identificacao_objeto = Column(Text, nullable=True, 
        comment="Resumo do que está sendo licitado")
    valor_estimado_total = Column(Float, nullable=True, 
        comment="Valor total da contratação (R$)")
    prazo_execucao = Column(String(100), nullable=True, 
        comment="Ex: '12 meses', '24 meses'")
    modalidade_contratacao = Column(String(50), nullable=True, 
        comment="Enum: Pregão, Concorrência, Dispensa, Inexigibilidade")
    
    estrategia_geral = Column(Text, nullable=True, 
        comment="Resumo da estratégia de gestão de riscos do processo")
    apetite_risco = Column(String(20), nullable=True, 
        comment="Enum: Conservador, Moderado, Agressivo. Define nível aceitável de risco")
    
    # Campos para formato novo do PGR (análise estruturada)
    metodologia_adotada = Column(String(100), nullable=True, 
        comment="Ex: 'Matriz 5x5', 'Análise Qualitativa', etc.")
    resumo_analise_planejamento = Column(Text, nullable=True, 
        comment="Resumo dos riscos na fase de planejamento")
    resumo_analise_selecao = Column(Text, nullable=True, 
        comment="Resumo dos riscos na fase de seleção de fornecedor")
    resumo_analise_gestao = Column(Text, nullable=True, 
        comment="Resumo dos riscos na fase de gestão contratual")
    
    responsavel_pgr = Column(String(200), nullable=True, 
        comment="Nome e cargo do responsável pelo PGR")
    data_elaboracao = Column(DateTime, default=now_brasilia, nullable=True)
    data_revisao = Column(DateTime, nullable=True)
    
    itens_risco = relationship("ItemRisco", back_populates="pgr", cascade="all, delete-orphan")


class ItemRisco(ArtefatoBase):
    """
    ItemRisco - Linha individual de risco no PGR.
    Um PGR pode ter dezenas de ItemRisco.
    """
    __tablename__ = "itens_risco"

    id = Column(Integer, primary_key=True, index=True)
    pgr_id = Column(Integer, ForeignKey("riscos.id", ondelete="CASCADE"), nullable=False)
    pgr = relationship("Riscos", back_populates="itens_risco")

    origem = Column(String(50), nullable=True, 
        comment="Enum: DFD, Cotacao, PAC, Externo")
    fase_licitacao = Column(String(50), nullable=True, 
        comment="Enum: Planejamento, Selecao_Fornecedor, Gestao_Contratual")
    categoria = Column(String(50), nullable=True, 
        comment="Enum: Tecnico, Administrativo, Juridico, Economico, Reputacional")

    evento = Column(Text, nullable=True, 
        comment="O QUÊ pode acontecer?")
    causa = Column(Text, nullable=True, 
        comment="POR QUÊ?")
    consequencia = Column(Text, nullable=True, 
        comment="QUAL IMPACTO?")

    probabilidade = Column(Integer, nullable=True, 
        comment="1-5: 1=Improvável, 5=Muito provável")
    impacto = Column(Integer, nullable=True, 
        comment="1-5: 1=Irrelevante, 5=Catastrófico")
    nivel_risco = Column(Integer, nullable=True, 
        comment="Calculado: probabilidade × impacto (1-25)")

    justificativa_probabilidade = Column(Text, nullable=True)
    justificativa_impacto = Column(Text, nullable=True)

    tipo_tratamento = Column(String(50), nullable=True, 
        comment="Enum: Mitigar, Transferir, Aceitar, Evitar")
    acoes_preventivas = Column(Text, nullable=True)
    acoes_contingencia = Column(Text, nullable=True)

    alocacao_responsavel = Column(String(50), nullable=True, 
        comment="Enum: Contratante, Contratada, Compartilhado")

    gatilho_monitoramento = Column(Text, nullable=True)
    responsavel_monitoramento = Column(String(100), nullable=True)
    frequencia_monitoramento = Column(String(50), nullable=True, 
        comment="Enum: Semanal, Quinzenal, Mensal, Trimestral")

    status_risco = Column(String(50), default="Identificado", nullable=False, 
        comment="Enum: Identificado, Monitorado, Ativado, Mitigado, Fechado")
    data_criacao = Column(DateTime, default=now_brasilia, nullable=False)
    data_atualizacao = Column(DateTime, default=now_brasilia, onupdate=now_brasilia, nullable=False)
    criado_por = Column(Integer, ForeignKey("usuarios.id"), nullable=True)
    notas = Column(Text, nullable=True)
