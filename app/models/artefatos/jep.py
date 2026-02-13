""" 
Sistema LIA - Modelo JEP
=========================
Justificativa de Excepcionalidade ao Planejamento (Contratação não prevista no PAC).

Lei 14.133/2021 - Quando uma contratação não está prevista no PAC (Plano de Contratações Anual),
é obrigatória a elaboração de justificativa formal antes do DFD.

A IA atua como "Auditor de Texto": transforma a explicação simples do usuário em
justificativa técnica e jurídica robusta para os tribunais de contas.

Autor: Equipe TRE-GO
Data: Fevereiro 2026
"""

from sqlalchemy import Column, Integer, Text, Boolean, ForeignKey, String
from sqlalchemy.orm import relationship
from .base import ArtefatoBase


class JustificativaExcepcionalidade(ArtefatoBase):
    """
    Justificativa de Contratação não Planejada (JEP)
    
    Documento obrigatório quando a licitação não está prevista no PAC.
    Deve ser assinado pela autoridade competente ANTES do DFD prosseguir.
    
    Lei 14.133/2021 - Art. 12, VII: O PAC é regra para contratações.
    Contratações fora do plano exigem justificativa formal de inclusão extemporânea.
    """
    __tablename__ = "justificativas_excepcionalidade"

    projeto_id = Column(Integer, ForeignKey("projetos.id"), nullable=False)
    projeto = relationship("Projeto", back_populates="justificativas_excepcionalidade")

    # Campo: Motivação da Extemporaneidade
    # Explicação detalhada de por que o item não foi incluído no PAC
    # Ex: Surgimento de nova tecnologia, alteração legislativa, evento imprevisível
    motivo_inclusao = Column(Text, nullable=True,
        comment="Justificativa da falha na previsão inicial do PAC")
    
    # Campo: Análise de Urgência/Prioridade
    # Demonstração de que a contratação não pode esperar o próximo ciclo
    # Ex: Risco de interrupção de serviço, perda de recursos orçamentários
    risco_adiamento = Column(Text, nullable=True,
        comment="O que acontece se a contratação for adiada para o próximo ciclo")
    
    # Campo: Impacto no Planejamento Existente
    # Declaração de que a inclusão não prejudica as contratações já previstas
    impacto_planejamento = Column(Text, nullable=True,
        comment="Análise do impacto da inclusão nas contratações já planejadas no PAC")
    
    # Campo: Alinhamento Estratégico
    # Justificativa de como a compra contribui para os objetivos do órgão
    alinhamento_estrategico = Column(Text, nullable=True,
        comment="Como a contratação contribui para os objetivos estratégicos do órgão")
    
    # Campo: Parecer da Autoridade Competente
    # Decisão (Aprovo/Reprovo) do ordenador de despesas
    parecer_autoridade = Column(Text, nullable=True,
        comment="Parecer e decisão da autoridade competente sobre a excepcionalidade")
    
    # Campo: Autorização Especial
    # Validação formal da autoridade superior
    autorizacao_especial = Column(Boolean, default=False,
        comment="Se a autoridade competente autorizou a quebra do planejamento original")
    
    # Campo: Classificação do motivo (para estatísticas/auditoria)
    tipo_excepcionalidade = Column(String(100), nullable=True,
        comment="Tipo: emergencia, alteracao_legislativa, tecnologia_superveniente, outro")
