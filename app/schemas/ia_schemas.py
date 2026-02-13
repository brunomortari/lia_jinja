"""
Sistema LIA - Schemas de IA e Artefatos
=========================================
Schemas Pydantic para endpoints de geracao de artefatos via IA.

Autor: Equipe TRE-GO
Data: Janeiro 2026
"""

from pydantic import BaseModel, field_validator, model_validator
from typing import Dict, Any, List, Optional, Union
import json
import logging

logger = logging.getLogger(__name__)


# ========== SCHEMAS DE GERACAO DE ARTEFATOS ==========

class GerarArtefatoRequest(BaseModel):
    """Schema para solicitar geracao de artefato via IA"""
    projeto_id: int
    prompt: str


class GerarArtefatoPayload(BaseModel):
    """Schema para payload completo de geracao de artefatos (DFD/ETP/TR/etc.) via IA"""
    projeto: Dict[str, Any]
    prompt_adicional: Optional[str] = ""
    timestamp: Optional[str] = None
    # Campos preenchidos pelo sistema (usuario, PAC, etc.)
    campos_sistema: Optional[Dict[str, Any]] = None
    # Campos preenchidos pelo usuario antes da geracao
    campos_usuario: Optional[Dict[str, Any]] = None
    # Contexto de artefatos aprovados (DFD, cotacoes, PGR) para ETP/TR
    contexto: Optional[Dict[str, Any]] = None
    # Contexto adicional para PGR e outros
    artefato_base_id: Optional[int] = None
    pesquisa_id: Optional[int] = None
    mode: Optional[str] = None



class SalvarArtefatoIARequest(BaseModel):
    """Schema para salvar artefato gerado via IA (DFD, ETP, TR, PGR, etc.)"""
    projeto_id: int
    artefato_data: Optional[Dict[str, Any]] = None
    pgr_data: Optional[Dict[str, Any]] = None
    etp_data: Optional[Dict[str, Any]] = None
    tr_data: Optional[Dict[str, Any]] = None
    edital_data: Optional[Dict[str, Any]] = None
    pesquisa_precos_data: Optional[Dict[str, Any]] = None
    prompt_adicional: Optional[str] = ""
    tipo_artefato: Optional[str] = "dfd"
    # Campos preenchidos pelo sistema (usuario, PAC, etc.)
    campos_sistema: Optional[Dict[str, Any]] = None
    # Campos preenchidos pelo usuario antes da geracao
    campos_usuario: Optional[Dict[str, Any]] = None
    status: Optional[str] = "rascunho"


class RegenerarCampoRequest(BaseModel):
    """Schema para regenerar um campo especifico"""
    projeto_id: int
    campo: str
    prompt_adicional: Optional[str] = ""


class LevantamentoSolucoesRequest(BaseModel):
    prompt: str
    projeto_id: Optional[int] = None
    contexto: Optional[Dict[str, Any]] = None  # Pode incluir itens do PAC, DFD, etc.


class IACallback(BaseModel):
    """Schema para callback de tarefas IA (uso interno)"""
    task_id: str
    status: str
    result: Dict[str, Any]


# ========== SCHEMAS DE COTACAO ==========

class GerarCotacaoRequest(BaseModel):
    """Schema para solicitar cotacao automatica"""
    projeto_id: int
    itens: Optional[List[str]] = []
    artefato_base_id: Optional[int] = None
    palavras_chave: Optional[str] = None
    codigo_catmat: Optional[int] = None
    tipo_catalogo: Optional[str] = None
    pesquisar_familia_pdm: Optional[bool] = False
    estado: Optional[str] = None
    incluir_detalhes_pncp: Optional[bool] = False

    @field_validator('artefato_base_id', mode='before')
    @classmethod
    def normalize_artefato_base_id(cls, v):
        """Normaliza valores vazios para None e converte strings para int"""
        if v is None or v == "" or v == "null" or v == "undefined":
            return None
        try:
            if isinstance(v, str) and v.strip() == "":
                return None
            return int(v)
        except (ValueError, TypeError):
            return None

    @field_validator('itens', mode='before')
    @classmethod
    def normalize_itens(cls, v):
        """Normaliza lista de itens, aceitando string vazia ou JSON"""
        if v is None or v == "" or v == "null" or v == "undefined":
            return None
        if isinstance(v, str):
            try:
                parsed = json.loads(v)
                if isinstance(parsed, list):
                    return parsed
                return [v]
            except Exception:
                return [v]
        return v

    @field_validator('projeto_id', mode='before')
    @classmethod
    def normalize_projeto_id(cls, v):
        """Garante que projeto_id seja int"""
        logger.info(f"DEBUG projeto_id recebido: '{v}' (tipo: {type(v)})")
        if v is None or v == "" or v == "null" or v == "undefined":
            raise ValueError("projeto_id invalido")
        return int(v)

    @field_validator('palavras_chave', mode='before')
    @classmethod
    def normalize_palavras_chave(cls, v):
        if v is None or v == "null" or v == "undefined":
            return None
        return str(v)

    class Config:
        extra = "allow"
        arbitrary_types_allowed = True


class SalvarPesquisaPrecosRequest(BaseModel):
    """Schema para salvar pesquisa de precos como artefato versionado"""
    projeto_id: int
    cotacao_data: Dict[str, Any]
    valor_total: Optional[float] = None
    artefato_base_id: Optional[int] = None


# ========== SCHEMAS DE EDICAO DE ARTEFATOS (DFD específico - DEPRECATED) ==========
# NOTA: Estes schemas são mantidos apenas para compatibilidade com o router dfd.py
# Use os schemas genéricos de app.schemas.artefatos para novos endpoints

class AtualizarDFDRequest(BaseModel):
    """Schema para atualizar um DFD completo.
    
    DEPRECATED: Use AtualizarArtefatoRequest de app.schemas.artefatos
    """
    descricao_objeto: Optional[str] = None
    justificativa: Optional[str] = None
    alinhamento_estrategico: Optional[str] = None
    grau_prioridade: Optional[str] = None
    valor_estimado: Optional[Union[float, str, None]] = None
    cronograma: Optional[str] = None
    data_pretendida: Optional[str] = None
    responsavel_requisitante: Optional[str] = None
    responsavel_gestor: Optional[str] = None
    responsavel_fiscal: Optional[str] = None
    status: Optional[str] = None

    @field_validator('valor_estimado', mode='before')
    @classmethod
    def parse_valor_estimado(cls, v):
        if v is None or v == '':
            return None
        if isinstance(v, str):
            try:
                clean_v = v.replace('R$', '').strip().replace('.', '').replace(',', '.')
                return float(clean_v)
            except (ValueError, TypeError):
                return None
        return v


class EditarCampoRequest(BaseModel):
    """Schema para editar um campo do DFD manualmente.
    
    DEPRECATED: Use EditarCampoArtefatoRequest de app.schemas.artefatos
    """
    artefato_id: int  # Renamed from dfd_id
    campo: str
    valor: str
    criar_versao: bool = False


class RegenerarCampoIARequest(BaseModel):
    """Schema para regenerar um campo via IA.
    
    DEPRECATED: Use RegenerarCampoArtefatoRequest de app.schemas.artefatos
    """
    artefato_id: int  # Renamed from dfd_id
    campo: str
    prompt_adicional: Optional[str] = ""
    criar_versao: bool = False

# ========== SCHEMAS DE ITEM RISCO (PGR Inteligente) ==========

class ItemRiscoCreate(BaseModel):
    """Schema para criar um novo Item de Risco"""
    pgr_id: int
    
    # Classificação
    origem: str  # Enum: DFD, Cotacao, PAC, Externo
    fase_licitacao: str  # Enum: Planejamento, Selecao_Fornecedor, Gestao_Contratual
    categoria: str  # Enum: Tecnico, Administrativo, Juridico, Economico, Reputacional
    
    # Descrição
    evento: str
    causa: str
    consequencia: str
    
    # Avaliação
    probabilidade: int  # 1-5
    impacto: int  # 1-5
    justificativa_probabilidade: Optional[str] = None
    justificativa_impacto: Optional[str] = None
    
    # Resposta
    tipo_tratamento: str  # Enum: Mitigar, Transferir, Aceitar, Evitar
    acoes_preventivas: Optional[str] = None
    acoes_contingencia: Optional[str] = None
    
    # Lei 14.133/21
    alocacao_responsavel: str  # Enum: Contratante, Contratada, Compartilhado
    
    # Monitoramento
    gatilho_monitoramento: Optional[str] = None
    responsavel_monitoramento: Optional[str] = None
    frequencia_monitoramento: Optional[str] = None  # Enum: Semanal, Quinzenal, Mensal, Trimestral
    
    # Auditoria
    criado_por: Optional[int] = None
    notas: Optional[str] = None
    
    @field_validator('probabilidade', 'impacto')
    @classmethod
    def validar_escala(cls, v):
        if not (1 <= v <= 5):
            raise ValueError('Probabilidade e Impacto devem estar entre 1 e 5')
        return v
    
    @field_validator('origem')
    @classmethod
    def validar_origem(cls, v):
        if v not in ['DFD', 'Cotacao', 'PAC', 'Externo']:
            raise ValueError('Origem deve ser uma de: DFD, Cotacao, PAC, Externo')
        return v
    
    @field_validator('fase_licitacao')
    @classmethod
    def validar_fase(cls, v):
        if v not in ['Planejamento', 'Selecao_Fornecedor', 'Gestao_Contratual']:
            raise ValueError('Fase deve ser uma de: Planejamento, Selecao_Fornecedor, Gestao_Contratual')
        return v
    
    @field_validator('categoria')
    @classmethod
    def validar_categoria(cls, v):
        if v not in ['Tecnico', 'Administrativo', 'Juridico', 'Economico', 'Reputacional']:
            raise ValueError('Categoria deve ser uma de: Tecnico, Administrativo, Juridico, Economico, Reputacional')
        return v
    
    @field_validator('tipo_tratamento')
    @classmethod
    def validar_tipo_tratamento(cls, v):
        if v not in ['Mitigar', 'Transferir', 'Aceitar', 'Evitar']:
            raise ValueError('Tipo de tratamento deve ser uma de: Mitigar, Transferir, Aceitar, Evitar')
        return v
    
    @field_validator('alocacao_responsavel')
    @classmethod
    def validar_alocacao(cls, v):
        if v not in ['Contratante', 'Contratada', 'Compartilhado']:
            raise ValueError('Alocação deve ser uma de: Contratante, Contratada, Compartilhado')
        return v


class ItemRiscoUpdate(BaseModel):
    """Schema para atualizar um Item de Risco"""
    # Todos os campos opcionais para PATCH
    origem: Optional[str] = None
    fase_licitacao: Optional[str] = None
    categoria: Optional[str] = None
    evento: Optional[str] = None
    causa: Optional[str] = None
    consequencia: Optional[str] = None
    probabilidade: Optional[int] = None
    impacto: Optional[int] = None
    justificativa_probabilidade: Optional[str] = None
    justificativa_impacto: Optional[str] = None
    tipo_tratamento: Optional[str] = None
    acoes_preventivas: Optional[str] = None
    acoes_contingencia: Optional[str] = None
    alocacao_responsavel: Optional[str] = None
    gatilho_monitoramento: Optional[str] = None
    responsavel_monitoramento: Optional[str] = None
    frequencia_monitoramento: Optional[str] = None
    status_risco: Optional[str] = None  # Identificado, Monitorado, Ativado, Mitigado, Fechado
    notas: Optional[str] = None
    
    @field_validator('probabilidade', 'impacto')
    @classmethod
    def validar_escala(cls, v):
        if v is not None and not (1 <= v <= 5):
            raise ValueError('Probabilidade e Impacto devem estar entre 1 e 5')
        return v


class ItemRiscoResponse(BaseModel):
    """Schema para responder com um Item de Risco (GET)"""
    id: int
    pgr_id: int
    origem: Optional[str] = None
    fase_licitacao: Optional[str] = None
    categoria: Optional[str] = None
    evento: Optional[str] = None
    causa: Optional[str] = None
    consequencia: Optional[str] = None
    probabilidade: Optional[int] = None
    impacto: Optional[int] = None
    nivel_risco: Optional[int] = None  # Calculado
    justificativa_probabilidade: Optional[str] = None
    justificativa_impacto: Optional[str] = None
    tipo_tratamento: Optional[str] = None
    acoes_preventivas: Optional[str] = None
    acoes_contingencia: Optional[str] = None
    alocacao_responsavel: Optional[str] = None
    gatilho_monitoramento: Optional[str] = None
    responsavel_monitoramento: Optional[str] = None
    frequencia_monitoramento: Optional[str] = None
    status_risco: str
    data_criacao: str
    data_atualizacao: str
    criado_por: Optional[int] = None
    notas: Optional[str] = None
    
    class Config:
        from_attributes = True


class GerarPGRPayload(BaseModel):
    """Schema para payload de geração de PGR (análise de riscos estruturada)"""
    projeto_id: int
    projeto: Dict[str, Any]
    
    # Contexto obrigatório
    artefatos_base: Dict[str, Any]  # {dfd_id: [1,2,3], etp_id: 5, cotacao_id: 7}
    
    # Configuração da análise
    metodologia_adotada: Optional[str] = "Matriz 5x5"
    prompt_adicional: Optional[str] = ""
    
    # Dados já extraídos pela IA (para evitar reprocessamento)
    cotacoes_analise: Optional[Dict[str, Any]] = None
    dfd_resumo: Optional[Dict[str, Any]] = None
    pac_info: Optional[Dict[str, Any]] = None


class GerarPGRRequest(BaseModel):
    """Schema para solicitar geração de PGR completo"""
    projeto_id: int
    prompt_adicional: Optional[str] = ""
    artefatos_base: Dict[str, Any]  # {dfd_id: [...], etp_id: ..., cotacao_id: ...}


class PGRResponse(BaseModel):
    """Schema para responder com PGR gerado (com itens de risco)"""
    pgr_id: int
    projeto_id: int
    identificacao_objeto: Optional[str] = None
    valor_estimado_total: Optional[float] = None
    metodologia_adotada: Optional[str] = None
    gerado_por_ia: bool
    artefatos_base: Optional[Dict[str, Any]] = None
    itens_risco: List[ItemRiscoResponse]
    resumo_analise_planejamento: Optional[str] = None
    resumo_analise_selecao: Optional[str] = None
    resumo_analise_gestao: Optional[str] = None
    matriz_alocacao: Optional[Dict[str, Any]] = None
    plano_comunicacao: Optional[List[Dict[str, str]]] = None


# ========== SCHEMAS DE ADESÃO DE ATA ==========

class AtaRegistro(BaseModel):
    """Modelo de Ata de Registro de Preços"""
    id: str
    numero: str
    descricao: str
    categoria: str
    valor: float
    validade: str
    fornecedor: str
    link_sei: Optional[str] = None
    data_vigencia: Optional[str] = None
    itens: Optional[List[Dict[str, Any]]] = None


class AdesaoAtaRequest(BaseModel):
    """Schema para requisição de adesão a uma ata"""
    projeto_id: int
    habilitar_adesao: bool
    descricao_item: Optional[str] = None


class AdesaoAtaResponse(BaseModel):
    """Schema para resposta de adesão a ata"""
    projeto_id: int
    adesao_habilitada: bool
    fase: str  # nao_iniciada, buscando_atas, ata_selecionada, deep_research_ativo, concluida
    atas_disponiveis: Optional[List[AtaRegistro]] = None
    ata_selecionada: Optional[AtaRegistro] = None
    deep_research_ativado: bool = False


class SelecionarAtaRequest(BaseModel):
    """Schema para seleção de uma ata específica"""
    projeto_id: int
    ata_id: str
    ata_dados: Dict[str, Any]  # Dados completos da ata selecionada


class SelecionarAtaResponse(BaseModel):
    """Schema para resposta de seleção de ata"""
    sucesso: bool
    mensagem: str
    projeto_id: int
    ata_selecionada: AtaRegistro
    deep_research_ativado: bool
    proxima_fase: str


# ========== SCHEMAS DE DECISÃO DE MODALIDADE (F2: Lógica de Decisão) ==========

class DefinirModalidadeRequest(BaseModel):
    """Schema para solicitar análise e definição de modalidade de contratação"""
    projeto_id: int
    etp_id: int
    # Valores técnicos para análise
    valor_estimado: float  # Valor estimado da contratação (R$)
    complexidade: str = "media"  # Enum: simples, media, complexa
    urgencia: bool = False  # Urgência da contratação?
    adesao_atas_disponiveis: Optional[bool] = None  # User input: há atas disponíveis?
    
    class Config:
        json_schema_extra = {
            "example": {
                "projeto_id": 1,
                "etp_id": 1,
                "valor_estimado": 150000.00,
                "complexidade": "media",
                "urgencia": False,
                "adesao_atas_disponiveis": True
            }
        }


class DefinirModalidadeResponse(BaseModel):
    """Schema para resposta de análise de modalidade"""
    projeto_id: int
    etp_id: int
    modalidade_sugerida: str  # Enum: adesao_ata, dispensa_valor_baixo
    score_analise: float  # Score de confiança da análise (0-100)
    criterios_aplicados: Dict[str, Any]  # Critérios técnicos/legais aplicados
    justificativa_tecnica: str  # Fundamentação legal/técnica
    proximo_fluxo: str  # Artefatos próximos a serem gerados
    
    class Config:
        json_schema_extra = {
            "example": {
                "projeto_id": 1,
                "etp_id": 1,
                "modalidade_sugerida": "adesao_ata",
                "score_analise": 87.5,
                "criterios_aplicados": {
                    "valor_limite": 192800.0,
                    "valor_estimado": 150000.0,
                    "cumprimento_limite": True,
                    "complexidade_baixa": False,
                    "atas_disponiveis": True
                },
                "justificativa_tecnica": "Valor abaixo do limite permitido por adesão. Adesão mais econômica que contratação direta.",
                "proximo_fluxo": "rdve (Relatório de Vantagem Econômica)"
            }
        }


class ConfirmarModalidadeRequest(BaseModel):
    """Schema para confirmar escolha de modalidade após análise"""
    projeto_id: int
    etp_id: int
    modalidade_escolhida: str  # Enum: adesao_ata, dispensa_valor_baixo
    justificativa_usuario: Optional[str] = None  # Justificativa adicional do usuário
    
    class Config:
        json_schema_extra = {
            "example": {
                "projeto_id": 1,
                "etp_id": 1,
                "modalidade_escolhida": "adesao_ata",
                "justificativa_usuario": "Preferência por ata já existente com fornecedor aprovado"
            }
        }


class ConfirmarModalidadeResponse(BaseModel):
    """Schema para resposta de confirmação de modalidade"""
    sucesso: bool
    projeto_id: int
    etp_id: int
    modalidade_definida: str
    artefatos_proximos: List[str]  # Siglas dos artefatos a serem gerados
    proxima_etapa: str  # Descrição da próxima etapa
    
    class Config:
        json_schema_extra = {
            "example": {
                "sucesso": True,
                "projeto_id": 1,
                "etp_id": 1,
                "modalidade_definida": "adesao_ata",
                "artefatos_proximos": ["RDVE", "JVA", "TAFO"],
                "proxima_etapa": "Gerar Relatório de Vantagem Econômica (RDVE)"
            }
        }

# ========== GENERIC CHAT SCHEMAS (for all artefacts) ==========

class ChatMessageInput(BaseModel):
    """Generic input for chat message to any artefact"""
    content: str
    history: List[Dict[str, str]] = []  # Previous messages: [{"role": "user"/"assistant", "content": "..."}, ...]
    model: Optional[str] = None
    attachments: Optional[List[Dict[str, Any]]] = []
    
    # Artefact-specific optional fields (used by various handlers)
    gestor: Optional[str] = None  # For ETP, TR, Edital
    fiscal: Optional[str] = None  # For ETP, TR, Edital
    data_limite: Optional[str] = None  # For ETP, TR
    categoria_risco: Optional[str] = None  # For PGR risk categories
    campo: Optional[str] = None  # For field regeneration
    valor_atual: Optional[str] = None  # Current value for field regen


class ChatGenerateInput(BaseModel):
    """Generic input for generation from chat history"""
    history: List[Dict[str, str]]
    model: Optional[str] = None
    attachments: Optional[List[Dict[str, Any]]] = []
    skills: Optional[List[str]] = []  # Active skill IDs
    deep_research_context: Optional[str] = None
    
    # Artefact-specific optional fields
    gestor: Optional[str] = None
    fiscal: Optional[str] = None
    data_limite: Optional[str] = None
    categoria_risco: Optional[str] = None
    prompt_adicional: Optional[str] = None


class ChatInitResponse(BaseModel):
    """Generic response for chat init endpoint"""
    projeto_id: int
    projeto_titulo: str
    setor_usuario: str
    welcome_message: str
    initial_fields: List[Dict[str, Any]]  # Fields to show in UI
    skills_ativas: List[Dict[str, Any]] = []


class RegenerarCampoInput(BaseModel):
    """Generic input for field regeneration"""
    campo: str
    valor_atual: Optional[str] = None
    prompt_adicional: Optional[str] = None
    model: Optional[str] = None
    categoria_risco: Optional[str] = None  # For PGR


class DeepResearchRequest(BaseModel):
    """Schema for deep research request"""
    topic: str
    context: str = ""


class Message(BaseModel):
    """Represents a message in chat history"""
    role: str  # "user" or "assistant"
    content: str
    metadata: Optional[Dict[str, Any]] = None
    attachments: Optional[List[Dict[str, Any]]] = None