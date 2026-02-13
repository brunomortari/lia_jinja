"""
Schemas Pydantic para Artefatos (ETP, DFD, PGR, etc).

Este módulo define os contratos de dados (Schemas) utilizados pela API de Artefatos,
incluindo regras de validação rigorosas e sanitização de entrada para prevenir
injeção de código e garantir a integridade dos dados.

Nota: Funções de sanitização foram movidas para `app.utils.validation`.
"""
from pydantic import BaseModel, Field, field_validator, model_validator
from typing import Dict, Any, Optional, List
from datetime import date
import json

from app.utils.validation import (
    sanitize_text,
    sanitize_dict,
    validate_campo_name,
    MAX_FIELD_LENGTH,
    MAX_PROMPT_LENGTH,
    MAX_CAMPO_NAME_LENGTH,
)

# ========== SCHEMAS BASE ==========

class SalvarArtefatoRequest(BaseModel):
    """Schema da requisição para salvar um artefato.

    Attributes:
        projeto_id (int): O ID do projeto ao qual o artefato pertence.
        artefato_data (Dict): O conteúdo do artefato em formato JSON/Dict.
        prompt_adicional (Optional[str]): Prompt opcional usado na geração (para histórico).
    """
    projeto_id: int = Field(..., gt=0, description="ID do projeto (deve ser positivo)")
    artefato_data: Dict[str, Any] = Field(..., description="Dados do artefato")
    prompt_adicional: Optional[str] = Field("", max_length=MAX_PROMPT_LENGTH)

    @field_validator('artefato_data')
    @classmethod
    def validate_artefato_data(cls, v):
        """Valida e sanitiza os dados do artefato verificando tamanho e tipo."""
        if not isinstance(v, dict):
            raise ValueError("artefato_data deve ser um dicionário")
        if len(json.dumps(v)) > 500000:  # 500KB máximo
            raise ValueError("artefato_data excede o tamanho máximo permitido (500KB)")
        return sanitize_dict(v)

    @field_validator('prompt_adicional')
    @classmethod
    def validate_prompt(cls, v):
        """Sanitiza o prompt adicional."""
        if v:
            return sanitize_text(v, MAX_PROMPT_LENGTH)
        return ""


class EditarCampoArtefatoRequest(BaseModel):
    """Schema da requisição para editar um único campo de um artefato.

    Attributes:
        artefato_id (int): O ID do artefato a ser editado.
        campo (str): O nome do campo a ser modificado.
        valor (str): O novo valor do campo.
    """
    artefato_id: int = Field(..., gt=0, description="ID do artefato")
    campo: str = Field(..., min_length=1, max_length=MAX_CAMPO_NAME_LENGTH)
    valor: str = Field(..., max_length=MAX_FIELD_LENGTH)

    @field_validator('campo')
    @classmethod
    def validate_campo(cls, v):
        """Valida se o nome do campo é seguro."""
        if not validate_campo_name(v):
            raise ValueError("Nome de campo inválido. Use apenas letras, números e underscores.")
        return v

    @field_validator('valor')
    @classmethod
    def validate_valor(cls, v):
        """Sanitiza o valor do campo."""
        return sanitize_text(v)


class RegenerarCampoArtefatoRequest(BaseModel):
    """Schema da requisição para regenerar um campo via IA.

    Attributes:
        artefato_id (int): O ID do artefato.
        campo (str): O nome do campo a ser regenerado.
        prompt_adicional (Optional[str]): Instruções adicionais para a IA.
    """
    artefato_id: int = Field(..., gt=0, description="ID do artefato")
    campo: str = Field(..., min_length=1, max_length=MAX_CAMPO_NAME_LENGTH)
    prompt_adicional: Optional[str] = Field("", max_length=MAX_PROMPT_LENGTH)

    @field_validator('campo')
    @classmethod
    def validate_campo(cls, v):
        """Valida se o nome do campo é seguro."""
        if not validate_campo_name(v):
            raise ValueError("Nome de campo inválido. Use apenas letras, números e underscores.")
        return v

    @field_validator('prompt_adicional')
    @classmethod
    def validate_prompt(cls, v):
        """Sanitiza o prompt adicional."""
        if v:
            return sanitize_text(v, MAX_PROMPT_LENGTH)
        return ""


class AtualizarArtefatoRequest(BaseModel):
    """Schema da requisição para atualizar um artefato completo (PUT).

    Permite campos dinâmicos que serão validados e sanitizados.

    Attributes:
        status (Optional[str]): Novo status do artefato ('rascunho' ou 'aprovado').
    """
    status: Optional[str] = Field(None, pattern=r'^(rascunho|aprovado)$')

    class Config:
        extra = "allow"  # Permite campos dinamicos (ex: descricao_necessidade, etc)

    @model_validator(mode='after')
    def sanitize_all_fields(self):
        """Valida e sanitiza todos os campos extras dinâmicos."""
        for field_name in list(self.__dict__.keys()):
            if field_name == 'status':
                continue
            value = getattr(self, field_name)
            if isinstance(value, str):
                setattr(self, field_name, sanitize_text(value))
            elif isinstance(value, dict):
                setattr(self, field_name, sanitize_dict(value))
        return self


# ========== SCHEMAS ETP (Estudo Técnico Preliminar) ==========
# Baseado na Lei 14.133/2021, Art. 18, §1º e IN SEGES/ME nº 58/2022

class QuantidadeDetalhadaSchema(BaseModel):
    """Schema para item de quantidade detalhada."""
    item: str = Field(..., max_length=500, description="Descrição do item")
    qtd_solicitada: int = Field(..., gt=0, description="Quantidade solicitada")
    consumo_medio: Optional[float] = Field(None, description="Consumo médio mensal")
    justificativa: Optional[str] = Field(None, max_length=2000, description="Justificativa da quantidade")


class CenarioMercadoSchema(BaseModel):
    """Schema para cenário de levantamento de mercado."""
    cenario: str = Field(..., max_length=200, description="Nome do cenário (ex: Compra, Locação)")
    descricao: str = Field(..., max_length=5000, description="Descrição detalhada do cenário")
    pros: List[str] = Field(default_factory=list, description="Vantagens do cenário")
    contras: List[str] = Field(default_factory=list, description="Desvantagens do cenário")
    valor_estimado: Optional[float] = Field(None, description="Valor estimado para este cenário")


class ContratacaoCorrelataSchema(BaseModel):
    """Schema para contratação correlata/interdependente."""
    objeto: str = Field(..., max_length=500, description="Objeto da contratação correlata")
    justificativa: str = Field(..., max_length=2000, description="Justificativa da interdependência")
    processo_sei: Optional[str] = Field(None, max_length=50, description="Número do processo SEI")


class ProvidenciaPreviaSchema(BaseModel):
    """Schema para providência prévia."""
    providencia: str = Field(..., max_length=500, description="Descrição da providência")
    responsavel: Optional[str] = Field(None, max_length=200, description="Responsável pela execução")
    prazo: Optional[str] = Field(None, max_length=50, description="Prazo para execução")
    status: Optional[str] = Field("pendente", pattern=r'^(pendente|em_andamento|concluido)$')


class CriterioSustentabilidadeSchema(BaseModel):
    """Schema para critério de sustentabilidade."""
    criterio: str = Field(..., max_length=500, description="Descrição do critério")
    aplicavel: bool = Field(..., description="Se o critério é aplicável")
    justificativa: Optional[str] = Field(None, max_length=2000, description="Justificativa")


class RiscoCriticoSchema(BaseModel):
    """Schema para risco crítico resumido no ETP."""
    risco: str = Field(..., max_length=500, description="Descrição do risco")
    nivel: str = Field(..., pattern=r'^(alto|extremo)$', description="Nível: alto ou extremo")
    probabilidade: int = Field(..., ge=1, le=5, description="Probabilidade (1-5)")
    impacto: int = Field(..., ge=1, le=5, description="Impacto (1-5)")
    mitigacao: str = Field(..., max_length=2000, description="Ação mitigadora")


class ResponsavelETPSchema(BaseModel):
    """Schema para responsável pela elaboração do ETP."""
    nome: str = Field(..., max_length=200, description="Nome do responsável")
    cargo: str = Field(..., max_length=200, description="Cargo/função")
    data_assinatura: Optional[str] = Field(None, description="Data da assinatura (ISO format)")


class ChecklistConformidadeSchema(BaseModel):
    """Schema para checklist de conformidade automática."""
    valor_presente: bool = Field(False, description="Valor estimado está presente?")
    parcelamento_justificado: bool = Field(False, description="Parcelamento foi justificado?")
    riscos_citados: bool = Field(False, description="Riscos críticos foram citados?")
    pca_mencionado: bool = Field(False, description="Há menção ao PCA?")
    requisitos_definidos: bool = Field(False, description="Requisitos foram definidos?")
    solucao_escolhida: bool = Field(False, description="Solução foi escolhida e justificada?")


class ETPCreateSchema(BaseModel):
    """
    Schema para criação de ETP.
    
    Baseado na taxonomia da Lei 14.133/2021 e IN 58/2022.
    Campos organizados por ID (ETP-01 a ETP-15).
    """
    projeto_id: int = Field(..., gt=0, description="ID do projeto")
    
    # ETP-01: Descrição da Necessidade
    descricao_necessidade: Optional[str] = Field(None, max_length=MAX_FIELD_LENGTH,
        description="Art. 18, §1º, I - Caracterização do interesse público")
    
    # ETP-02: Área Requisitante
    area_requisitante: Optional[str] = Field(None, max_length=300,
        description="Unidade/Setor demandante")
    
    # ETP-03: Requisitos da Contratação
    requisitos_contratacao: Optional[str] = Field(None, max_length=MAX_FIELD_LENGTH,
        description="Art. 18, §1º, III - Requisitos técnicos, normas, certificações")
    
    # ETP-04: Estimativa de Quantidades
    estimativa_quantidades: Optional[str] = Field(None, max_length=MAX_FIELD_LENGTH,
        description="Art. 18, §1º, IV - Memória de cálculo")
    quantidades_detalhadas: Optional[List[QuantidadeDetalhadaSchema]] = Field(None)
    
    # ETP-05: Levantamento de Mercado
    levantamento_mercado: Optional[str] = Field(None, max_length=MAX_FIELD_LENGTH,
        description="Art. 18, §1º, II - Análise comparativa de soluções")
    cenarios_mercado: Optional[List[CenarioMercadoSchema]] = Field(None)
    
    # ETP-06: Estimativa do Valor
    estimativa_valor: Optional[str] = Field(None, max_length=MAX_FIELD_LENGTH,
        description="Art. 18, §1º, IV - Síntese financeira")
    valor_total_estimado: Optional[float] = Field(None, ge=0)
    metodologia_preco: Optional[str] = Field(None, pattern=r'^(media|mediana|menor_preco)$')
    data_base_preco: Optional[date] = Field(None)
    cotacao_id_referencia: Optional[int] = Field(None, gt=0)
    
    # ETP-07: Descrição da Solução
    descricao_solucao: Optional[str] = Field(None, max_length=MAX_FIELD_LENGTH,
        description="Art. 18, §1º, II - Objeto + solução escolhida")
    solucao_escolhida: Optional[str] = Field(None, max_length=200)
    
    # ETP-08: Parcelamento do Objeto
    justificativa_parcelamento: Optional[str] = Field(None, max_length=MAX_FIELD_LENGTH,
        description="Art. 18, §1º, VIII - Súmula 247 TCU")
    parcelamento_aplicavel: Optional[str] = Field(None, pattern=r'^(sim|nao|parcial)$')
    
    # ETP-09: Contratações Correlatas
    contratacoes_correlatas: Optional[str] = Field(None, max_length=MAX_FIELD_LENGTH,
        description="Art. 18, §1º, IX - Dependências")
    contratacoes_correlatas_lista: Optional[List[ContratacaoCorrelataSchema]] = Field(None)
    
    # ETP-10: Alinhamento ao PCA
    alinhamento_pca: Optional[str] = Field(None, max_length=MAX_FIELD_LENGTH,
        description="Art. 12, VII - Validação de governança")
    pca_ano: Optional[int] = Field(None, ge=2020, le=2100)
    pca_item_id: Optional[str] = Field(None, max_length=50)
    
    # ETP-11: Resultados Pretendidos
    resultados_pretendidos: Optional[str] = Field(None, max_length=MAX_FIELD_LENGTH,
        description="Art. 18, §1º, IX - Benefícios esperados")
    
    # ETP-12: Providências Prévias
    providencias_previas: Optional[str] = Field(None, max_length=MAX_FIELD_LENGTH,
        description="Art. 18, §1º, XI - Ações prévias necessárias")
    providencias_checklist: Optional[List[ProvidenciaPreviaSchema]] = Field(None)
    
    # ETP-13: Impactos Ambientais
    impactos_ambientais: Optional[str] = Field(None, max_length=MAX_FIELD_LENGTH,
        description="Art. 18, §1º, XII - Sustentabilidade")
    criterios_sustentabilidade: Optional[List[CriterioSustentabilidadeSchema]] = Field(None)
    
    # ETP-14: Análise de Riscos
    analise_riscos: Optional[str] = Field(None, max_length=MAX_FIELD_LENGTH,
        description="Art. 18, §1º, X - Riscos críticos")
    riscos_criticos: Optional[List[RiscoCriticoSchema]] = Field(None)
    pgr_id_referencia: Optional[int] = Field(None, gt=0)
    
    # ETP-15: Viabilidade da Contratação
    viabilidade_contratacao: Optional[str] = Field(None, max_length=MAX_FIELD_LENGTH,
        description="Art. 18, §1º, XIII - Parecer final")
    declaracao_viabilidade: Optional[str] = Field(None, 
        pattern=r'^(viavel|inviavel|viavel_com_ressalvas)$')
    
    # Metadados de Integração
    dfd_id_referencia: Optional[int] = Field(None, gt=0)
    responsaveis: Optional[List[ResponsavelETPSchema]] = Field(None)

    @field_validator('descricao_necessidade')
    @classmethod
    def validate_descricao_necessidade(cls, v):
        """
        Valida a descrição da necessidade.
        Regra de negócio: bloquear descrições com menos de 10 palavras.
        """
        if v:
            v = sanitize_text(v)
            words = v.split()
            if len(words) < 10:
                raise ValueError(
                    "A descrição da necessidade deve ter no mínimo 10 palavras. "
                    "Descreva o problema raiz e o interesse público envolvido."
                )
        return v


class ETPUpdateSchema(BaseModel):
    """
    Schema para atualização parcial de ETP.
    Todos os campos são opcionais.
    """
    # Campos de texto (ETP-01 a ETP-15)
    descricao_necessidade: Optional[str] = Field(None, max_length=MAX_FIELD_LENGTH)
    area_requisitante: Optional[str] = Field(None, max_length=300)
    requisitos_contratacao: Optional[str] = Field(None, max_length=MAX_FIELD_LENGTH)
    estimativa_quantidades: Optional[str] = Field(None, max_length=MAX_FIELD_LENGTH)
    quantidades_detalhadas: Optional[List[QuantidadeDetalhadaSchema]] = Field(None)
    levantamento_mercado: Optional[str] = Field(None, max_length=MAX_FIELD_LENGTH)
    cenarios_mercado: Optional[List[CenarioMercadoSchema]] = Field(None)
    estimativa_valor: Optional[str] = Field(None, max_length=MAX_FIELD_LENGTH)
    valor_total_estimado: Optional[float] = Field(None, ge=0)
    metodologia_preco: Optional[str] = Field(None, pattern=r'^(media|mediana|menor_preco)$')
    data_base_preco: Optional[date] = Field(None)
    cotacao_id_referencia: Optional[int] = Field(None, gt=0)
    descricao_solucao: Optional[str] = Field(None, max_length=MAX_FIELD_LENGTH)
    solucao_escolhida: Optional[str] = Field(None, max_length=200)
    justificativa_parcelamento: Optional[str] = Field(None, max_length=MAX_FIELD_LENGTH)
    parcelamento_aplicavel: Optional[str] = Field(None, pattern=r'^(sim|nao|parcial)$')
    contratacoes_correlatas: Optional[str] = Field(None, max_length=MAX_FIELD_LENGTH)
    contratacoes_correlatas_lista: Optional[List[ContratacaoCorrelataSchema]] = Field(None)
    alinhamento_pca: Optional[str] = Field(None, max_length=MAX_FIELD_LENGTH)
    pca_ano: Optional[int] = Field(None, ge=2020, le=2100)
    pca_item_id: Optional[str] = Field(None, max_length=50)
    resultados_pretendidos: Optional[str] = Field(None, max_length=MAX_FIELD_LENGTH)
    providencias_previas: Optional[str] = Field(None, max_length=MAX_FIELD_LENGTH)
    providencias_checklist: Optional[List[ProvidenciaPreviaSchema]] = Field(None)
    impactos_ambientais: Optional[str] = Field(None, max_length=MAX_FIELD_LENGTH)
    criterios_sustentabilidade: Optional[List[CriterioSustentabilidadeSchema]] = Field(None)
    analise_riscos: Optional[str] = Field(None, max_length=MAX_FIELD_LENGTH)
    riscos_criticos: Optional[List[RiscoCriticoSchema]] = Field(None)
    pgr_id_referencia: Optional[int] = Field(None, gt=0)
    viabilidade_contratacao: Optional[str] = Field(None, max_length=MAX_FIELD_LENGTH)
    declaracao_viabilidade: Optional[str] = Field(None, 
        pattern=r'^(viavel|inviavel|viavel_com_ressalvas)$')
    
    # Metadados
    status: Optional[str] = Field(None, pattern=r'^(rascunho|aprovado)$')
    dfd_id_referencia: Optional[int] = Field(None, gt=0)
    responsaveis: Optional[List[ResponsavelETPSchema]] = Field(None)
    checklist_conformidade: Optional[ChecklistConformidadeSchema] = Field(None)

    class Config:
        extra = "forbid"  # Não permite campos extras


class ETPResponseSchema(BaseModel):
    """Schema de resposta para ETP."""
    id: int
    projeto_id: int
    versao: int
    status: str
    
    # Campos principais (ETP-01 a ETP-15)
    descricao_necessidade: Optional[str] = None
    area_requisitante: Optional[str] = None
    requisitos_contratacao: Optional[str] = None
    estimativa_quantidades: Optional[str] = None
    quantidades_detalhadas: Optional[List[Dict[str, Any]]] = None
    levantamento_mercado: Optional[str] = None
    cenarios_mercado: Optional[List[Dict[str, Any]]] = None
    estimativa_valor: Optional[str] = None
    valor_total_estimado: Optional[float] = None
    metodologia_preco: Optional[str] = None
    data_base_preco: Optional[date] = None
    cotacao_id_referencia: Optional[int] = None
    descricao_solucao: Optional[str] = None
    solucao_escolhida: Optional[str] = None
    justificativa_parcelamento: Optional[str] = None
    parcelamento_aplicavel: Optional[str] = None
    contratacoes_correlatas: Optional[str] = None
    contratacoes_correlatas_lista: Optional[List[Dict[str, Any]]] = None
    alinhamento_pca: Optional[str] = None
    pca_ano: Optional[int] = None
    pca_item_id: Optional[str] = None
    resultados_pretendidos: Optional[str] = None
    providencias_previas: Optional[str] = None
    providencias_checklist: Optional[List[Dict[str, Any]]] = None
    impactos_ambientais: Optional[str] = None
    criterios_sustentabilidade: Optional[List[Dict[str, Any]]] = None
    analise_riscos: Optional[str] = None
    riscos_criticos: Optional[List[Dict[str, Any]]] = None
    pgr_id_referencia: Optional[int] = None
    viabilidade_contratacao: Optional[str] = None
    declaracao_viabilidade: Optional[str] = None
    
    # Metadados
    dfd_id_referencia: Optional[int] = None
    sincronizado: Optional[int] = None
    checklist_conformidade: Optional[Dict[str, bool]] = None
    responsaveis: Optional[List[Dict[str, Any]]] = None
    
    # IA
    gerado_por_ia: bool = False
    prompt_ia: Optional[str] = None
    campos_editados: Optional[Dict[str, Any]] = None
    campos_regenerados: Optional[Dict[str, Any]] = None
    
    # Timestamps
    data_criacao: Optional[str] = None
    data_atualizacao: Optional[str] = None
    
    # SEI
    protocolo_sei: Optional[Dict[str, Any]] = None

    class Config:
        from_attributes = True
