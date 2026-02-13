""" 
Sistema LIA - Modelo do PAC
============================
Define a estrutura da tabela do Plano Anual de Contratações

Autor: Equipe TRE-GO
Data: Janeiro 2026
"""

from sqlalchemy import Column, Integer, String, Text, Float, Boolean
from app.database import Base


class PAC(Base):
    """
    Modelo do Plano Anual de Contratações (PAC)
    
    Armazena os itens planejados para contratação no ano.
    Os dados geralmente são importados de um CSV fornecido pela administração.
    """
    __tablename__ = "pac"
    
    # ========== IDENTIFICAÇÃO ==========
    
    id = Column(Integer, primary_key=True, index=True, comment="ID único do item do PAC")
    
    ano = Column(Integer, nullable=False, index=True, comment="Ano do planejamento (ex: 2025)")
    
    # ========== CLASSIFICAÇÃO ESTRATÉGICA ==========
    
    tipo_pac = Column(String(50), comment="Tipo: Ordinário, Extraordinário, etc")
    
    iniciativa = Column(Text, comment="Iniciativa estratégica do PEI")
    
    objetivo = Column(Text, comment="Objetivo estratégico do PEI")
    
    # ========== UNIDADES RESPONSÁVEIS ==========
    
    unidade_tecnica = Column(String(200), comment="Unidade técnica responsável")
    
    unidade_administrativa = Column(String(200), comment="Unidade administrativa responsável")
    
    # ========== DESCRIÇÃO DO OBJETO ==========
    
    detalhamento = Column(Text, nullable=False, comment="Descrição detalhada do objeto")
    
    descricao = Column(String(500), comment="Descrição resumida")
    
    # ========== QUANTIFICAÇÃO ==========
    
    quantidade = Column(Float, comment="Quantidade a ser contratada")
    
    unidade = Column(String(50), comment="Unidade de medida (kg, unidade, litro, etc)")
    
    frequencia = Column(String(50), comment="Frequência (ANUAL, MENSAL, etc)")
    
    # ========== VALORES ==========
    
    valor_previsto = Column(String(50), comment="Valor previsto (texto com R$)")
    
    # ========== JUSTIFICATIVA E PRIORIDADE ==========
    
    justificativa = Column(Text, comment="Justificativa da contratação")
    
    prioridade = Column(Integer, comment="Nível de prioridade (1-5)")
    
    # ========== PRAZOS ==========
    
    data_tr = Column(String(20), comment="Data de TR")
    
    disponibilidade_contratacao = Column(String(20), comment="Data de disponibilidade")
    
    # ========== CONTRATO VIGENTE ==========
    
    numero_contrato = Column(String(50), comment="Número do contrato vigente")
    
    ano_contrato = Column(String(10), comment="Ano do contrato")
    
    vencimento_contrato = Column(String(20), comment="Data de vencimento")
    
    prorrogacao_contrato = Column(String(10), comment="Número de prorrogações")
    
    contratacao_continuada = Column(String(10), comment="Se é contratação continuada (Sim/Não)")
    
    # ========== CLASSIFICAÇÃO ORÇAMENTÁRIA ==========
    
    catmat_catser = Column(String(50), comment="Código CATMAT/CATSER")
    
    despesa = Column(String(200), comment="Tipo de despesa")
    
    elemento_despesa = Column(String(200), comment="Elemento de despesa")
    
    natureza_despesa = Column(String(100), comment="Natureza da despesa")
    
    # ========== CONTROLE ==========
    
    inativo = Column(String(10), comment="Se o item está inativo (Sim/Não)")
    
    motivo_rejeicao = Column(Text, comment="Motivo da rejeição, se houver")
    
    motivo_ajuste = Column(Text, comment="Motivo do ajuste, se houver")
    
    # ========== PAD ==========
    
    numero_pad = Column(String(50), comment="Número do PAD")
    
    ano_pad = Column(String(10), comment="Ano do PAD")
    
    # ========== TIPO DE CONTRATAÇÃO ==========
    
    tipo_contratacao = Column(String(100), comment="Tipo: Serviços, Fornecimento, etc")
    
    # ========== FASE ==========

    fase = Column(String(50), comment="Fase atual do item (AJUSTES, etc)")

    # ========== PROPRIEDADES CALCULADAS ==========

    @property
    def valor_previsto_float(self) -> float:
        """Converte valor_previsto (string R$) para float"""
        if not self.valor_previsto:
            return 0.0
        try:
            # Remove "R$", pontos de milhar e converte vírgula para ponto
            clean = self.valor_previsto.replace('R$', '').replace(' ', '').replace('.', '').replace(',', '.')
            return float(clean)
        except (ValueError, AttributeError):
            return 0.0

    @property
    def valor_por_item(self) -> float:
        """Calcula valor unitário estimado (valor_previsto / quantidade)"""
        valor = self.valor_previsto_float
        qtd = self.quantidade or 1
        if qtd <= 0:
            qtd = 1
        return round(valor / qtd, 2)

    def __repr__(self):
        descricao_resumo = (self.descricao or '')[:50]
        return f"<PAC(id={self.id}, ano={self.ano}, descricao='{descricao_resumo}...')>"

    def to_dict(self):
        """Converte o objeto para dicionário"""
        return {
            "id": self.id,
            "ano": self.ano,
            "tipo_pac": self.tipo_pac,
            "iniciativa": self.iniciativa,
            "objetivo": self.objetivo,
            "unidade_tecnica": self.unidade_tecnica,
            "unidade_administrativa": self.unidade_administrativa,
            "detalhamento": self.detalhamento,
            "descricao": self.descricao,
            "quantidade": self.quantidade,
            "unidade": self.unidade,
            "frequencia": self.frequencia,
            "valor_previsto": self.valor_previsto,
            "valor_por_item": self.valor_por_item,
            "justificativa": self.justificativa,
            "prioridade": self.prioridade,
            "catmat_catser": self.catmat_catser,
            "tipo_contratacao": self.tipo_contratacao,
            "fase": self.fase,
        }
