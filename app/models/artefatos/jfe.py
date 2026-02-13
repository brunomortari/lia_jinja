""" 
Sistema LIA - Modelo JFE
=========================
Justificativa do Fornecedor Escolhido.

Autor: Equipe TRE-GO
Data: Fevereiro 2026
"""

from sqlalchemy import Column, Integer, String, Text, Float, ForeignKey, JSON
from sqlalchemy.orm import relationship
from .base import ArtefatoBase


class JustificativaFornecedorEscolhido(ArtefatoBase):
    """
    Justificativa do Fornecedor Escolhido
    
    Demonstração da adequação do fornecedor ao interesse público.
    Essencial para Inexigibilidade ou Dispensa por fornecedor único.
    Lei 14.133/2021. Fluxo: Contratação Direta.
    """
    __tablename__ = "justificativa_fornecedor_escolhido"
    
    projeto_id = Column(Integer, ForeignKey("projetos.id"), nullable=False)
    aviso_id = Column(Integer, ForeignKey("aviso_publicidade_direta.id"), nullable=True,
        comment="Aviso de dispensa vinculado")
    projeto = relationship("Projeto", foreign_keys=[projeto_id])
    aviso = relationship("AvisoPublicidadeDireta", foreign_keys=[aviso_id])
    
    # Identificação do Fornecedor
    nome_fornecedor = Column(String(300), nullable=True,
        comment="Razão social do fornecedor escolhido")
    
    cnpj_fornecedor = Column(String(20), nullable=True,
        comment="CNPJ do fornecedor")
    
    endereco_fornecedor = Column(Text, nullable=True,
        comment="Endereço completo do fornecedor")
    
    # Qualificação Técnica
    qualificacao_tecnica = Column(Text, nullable=True,
        comment="Provas de expertise única ou capacidade imediata")
    
    atestados_capacidade = Column(JSON, nullable=True,
        comment="JSON: [{tipo_atestado, descricao, data_emissao, orgao_emissor}, ...]")
    
    experiencia_comprovada = Column(Text, nullable=True,
        comment="Descrição da experiência comprovada do fornecedor")
    
    # Certidões Negativas (Regularidade)
    certidao_federal = Column(JSON, nullable=True,
        comment="JSON: {numero, data_emissao, validade, situacao}")
    
    certidao_estadual = Column(JSON, nullable=True,
        comment="JSON: {numero, data_emissao, validade, situacao}")
    
    certidao_municipal = Column(JSON, nullable=True,
        comment="JSON: {numero, data_emissao, validade, situacao}")
    
    certidao_fgts = Column(JSON, nullable=True,
        comment="JSON: {numero, data_emissao, validade, situacao}")
    
    certidao_trabalhista = Column(JSON, nullable=True,
        comment="JSON: {numero, data_emissao, validade, situacao}")
    
    certidoes_anexadas = Column(JSON, nullable=True,
        comment="JSON: [{tipo, arquivo, data_upload}, ...] - Conjunto completo de certidões")
    
    # Inviabilidade de Competição (se aplicável)
    inviabilidade_competicao = Column(String(20), nullable=True,
        comment="Enum: sim, nao")
    
    justificativa_inviabilidade = Column(Text, nullable=True,
        comment="Explicação de por que não é possível licitar (ex: fornecedor exclusivo, artista consagrado)")
    
    tipo_inviabilidade = Column(String(100), nullable=True,
        comment="Ex: 'Fornecedor Exclusivo', 'Notória Especialização', 'Artista Consagrado'")
    
    documentacao_exclusividade = Column(JSON, nullable=True,
        comment="JSON: [{tipo_documento, descricao, arquivo}, ...] - Documentos que comprovam exclusividade")
    
    # Análise de Preço
    preco_proposto = Column(Float, nullable=True,
        comment="Preço proposto pelo fornecedor escolhido")
    
    analise_compatibilidade_preco = Column(Text, nullable=True,
        comment="Análise de compatibilidade do preço com valores de mercado")
    
    valores_referencia = Column(JSON, nullable=True,
        comment="JSON: [{fonte, valor, data}, ...] - Valores de referência para comparação")
    
    # Conclusão
    conclusao_justificativa = Column(Text, nullable=True,
        comment="Conclusão sobre a adequação do fornecedor e a conformidade da escolha")
