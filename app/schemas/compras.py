"""
Schemas Pydantic para o serviço CATMAT/CATSERV
Versão 2.0 - Com suporte a outliers e PNCP

Nota: Migrado de app/models/compras.py para app/schemas/compras.py
pois são schemas Pydantic (API), não modelos SQLAlchemy (ORM).
"""
from pydantic import BaseModel, Field, ConfigDict, field_validator
from typing import Optional, List
from datetime import datetime, date
from enum import Enum


class TipoCatalogo(str, Enum):
    """Tipo de catálogo: Material (CATMAT) ou Serviço (CATSERV)"""
    MATERIAL = "material"
    SERVICO = "servico"


class ItemPreco(BaseModel):
    """Modelo para um item de preço individual"""
    model_config = ConfigDict(populate_by_name=True, ser_json_by_alias=True)
    
    id_compra: Optional[str] = Field(None, alias="idCompra", serialization_alias="idCompra")
    id_item_compra: Optional[int] = Field(None, alias="idItemCompra", serialization_alias="idItemCompra")
    forma: Optional[str] = None
    modalidade: Optional[int] = None
    criterio_julgamento: Optional[str] = Field(None, alias="criterioJulgamento", serialization_alias="criterioJulgamento")
    numero_item_compra: Optional[int] = Field(None, alias="numeroItemCompra", serialization_alias="numeroItemCompra")
    descricao_item: Optional[str] = Field(None, alias="descricaoItem", serialization_alias="descricaoItem")
    codigo_item_catalogo: Optional[int] = Field(None, alias="codigoItemCatalogo", serialization_alias="codigoItemCatalogo")
    nome_unidade_medida: Optional[str] = Field(None, alias="nomeUnidadeMedida", serialization_alias="nomeUnidadeMedida")
    sigla_unidade_medida: Optional[str] = Field(None, alias="siglaUnidadeMedida", serialization_alias="siglaUnidadeMedida")
    nome_unidade_fornecimento: Optional[str] = Field(None, alias="nomeUnidadeFornecimento", serialization_alias="nomeUnidadeFornecimento")
    sigla_unidade_fornecimento: Optional[str] = Field(None, alias="siglaUnidadeFornecimento", serialization_alias="siglaUnidadeFornecimento")
    capacidade_unidade_fornecimento: Optional[float] = Field(None, alias="capacidadeUnidadeFornecimento", serialization_alias="capacidadeUnidadeFornecimento")
    quantidade: Optional[float] = None
    preco_unitario: Optional[float] = Field(None, alias="precoUnitario", serialization_alias="precoUnitario")
    percentual_maior_desconto: Optional[float] = Field(None, alias="percentualMaiorDesconto", serialization_alias="percentualMaiorDesconto")
    ni_fornecedor: Optional[str] = Field(None, alias="niFornecedor", serialization_alias="niFornecedor")
    nome_fornecedor: Optional[str] = Field(None, alias="nomeFornecedor", serialization_alias="nomeFornecedor")
    marca: Optional[str] = None
    codigo_uasg: Optional[str] = Field(None, alias="codigoUasg", serialization_alias="codigoUasg")
    nome_uasg: Optional[str] = Field(None, alias="nomeUasg", serialization_alias="nomeUasg")
    codigo_municipio: Optional[int] = Field(None, alias="codigoMunicipio", serialization_alias="codigoMunicipio")
    municipio: Optional[str] = None
    estado: Optional[str] = None
    codigo_orgao: Optional[int] = Field(None, alias="codigoOrgao", serialization_alias="codigoOrgao")
    nome_orgao: Optional[str] = Field(None, alias="nomeOrgao", serialization_alias="nomeOrgao")
    poder: Optional[str] = None
    esfera: Optional[str] = None
    data_compra: Optional[datetime] = Field(None, alias="dataCompra", serialization_alias="dataCompra")
    data_resultado: Optional[datetime] = Field(None, alias="dataResultado", serialization_alias="dataResultado")

    @field_validator('data_compra', 'data_resultado', mode='before')
    @classmethod
    def parse_date_or_datetime(cls, v):
        """Aceita tanto formato date (YYYY-MM-DD) quanto datetime"""
        if v is None:
            return None
        if isinstance(v, datetime):
            return v
        if isinstance(v, date):
            return datetime.combine(v, datetime.min.time())
        if isinstance(v, str):
            # Tenta parsear como datetime completo primeiro
            try:
                return datetime.fromisoformat(v)
            except ValueError:
                pass
            # Se falhar, tenta como data apenas (adiciona hora 00:00:00)
            try:
                return datetime.fromisoformat(f"{v}T00:00:00")
            except ValueError:
                pass
        return v
    codigo_classe: Optional[int] = Field(None, alias="codigoClasse", serialization_alias="codigoClasse")
    nome_classe: Optional[str] = Field(None, alias="nomeClasse", serialization_alias="nomeClasse")

    # Campo para marcar outliers
    is_outlier: bool = Field(False, alias="isOutlier", serialization_alias="isOutlier")

    # Detalhes enriquecidos do PNCP (opcional, preenchido quando solicitado)
    detalhes_pncp: Optional["DetalheItemPNCP"] = Field(None, alias="detalhesPncp", serialization_alias="detalhesPncp")


class ItemCatalogo(BaseModel):
    """Modelo para um item do catálogo de materiais"""
    model_config = ConfigDict(populate_by_name=True, ser_json_by_alias=True)
    
    codigo_item: Optional[int] = Field(None, alias="codigoItem", serialization_alias="codigoItem")
    codigo_grupo: Optional[int] = Field(None, alias="codigoGrupo", serialization_alias="codigoGrupo")
    nome_grupo: Optional[str] = Field(None, alias="nomeGrupo", serialization_alias="nomeGrupo")
    codigo_classe: Optional[int] = Field(None, alias="codigoClasse", serialization_alias="codigoClasse")
    nome_classe: Optional[str] = Field(None, alias="nomeClasse", serialization_alias="nomeClasse")
    codigo_pdm: Optional[int] = Field(None, alias="codigoPdm", serialization_alias="codigoPdm")
    nome_pdm: Optional[str] = Field(None, alias="nomePdm", serialization_alias="nomePdm")
    descricao_item: Optional[str] = Field(None, alias="descricaoItem", serialization_alias="descricaoItem")
    status_item: Optional[bool] = Field(None, alias="statusItem", serialization_alias="statusItem")


class PdmMaterial(BaseModel):
    """Modelo para PDM (Padrão Descritivo de Material)"""
    model_config = ConfigDict(populate_by_name=True, ser_json_by_alias=True)
    
    codigo_pdm: Optional[int] = Field(None, alias="codigoPdm", serialization_alias="codigoPdm")
    nome_pdm: Optional[str] = Field(None, alias="nomePdm", serialization_alias="nomePdm")
    codigo_grupo: Optional[int] = Field(None, alias="codigoGrupo", serialization_alias="codigoGrupo")
    nome_grupo: Optional[str] = Field(None, alias="nomeGrupo", serialization_alias="nomeGrupo")
    codigo_classe: Optional[int] = Field(None, alias="codigoClasse", serialization_alias="codigoClasse")
    nome_classe: Optional[str] = Field(None, alias="nomeClasse", serialization_alias="nomeClasse")
    status_pdm: Optional[bool] = Field(None, alias="statusPdm", serialization_alias="statusPdm")


class EstatisticasPreco(BaseModel):
    """Modelo com estatísticas de preços - inclui análise de outliers"""
    quantidade_registros: int = Field(description="Total de registros encontrados")
    preco_minimo: Optional[float] = Field(None, description="Menor preço unitário")
    preco_maximo: Optional[float] = Field(None, description="Maior preço unitário")
    preco_medio: Optional[float] = Field(None, description="Média aritmética dos preços")
    preco_mediana: Optional[float] = Field(None, description="Mediana dos preços")
    desvio_padrao: Optional[float] = Field(None, description="Desvio padrão dos preços")
    coeficiente_variacao: Optional[float] = Field(None, description="Coeficiente de variação (CV) em %")
    
    # Novos campos para análise de outliers
    q1: Optional[float] = Field(None, description="Primeiro quartil (25%)")
    q3: Optional[float] = Field(None, description="Terceiro quartil (75%)")
    iqr: Optional[float] = Field(None, description="Intervalo interquartil (IQR)")
    limite_inferior: Optional[float] = Field(None, description="Limite inferior para outliers")
    limite_superior: Optional[float] = Field(None, description="Limite superior para outliers")
    quantidade_outliers: int = Field(0, description="Quantidade de outliers detectados")


class RespostaPrecos(BaseModel):
    """Modelo de resposta completa com preços e estatísticas"""
    codigo_catmat: int = Field(description="Código CATMAT pesquisado")
    tipo_catalogo: TipoCatalogo = Field(description="Tipo de catálogo")
    descricao_item: Optional[str] = Field(None, description="Descrição do item")
    pesquisa_familia_pdm: bool = Field(False, description="Se pesquisou toda família PDM")
    codigo_pdm: Optional[int] = Field(None, description="Código PDM (se aplicável)")
    nome_pdm: Optional[str] = Field(None, description="Nome do PDM (se aplicável)")
    
    # Estatísticas com todos os dados
    estatisticas: EstatisticasPreco = Field(description="Estatísticas dos preços (todos os dados)")
    
    # Estatísticas sem outliers
    estatisticas_sem_outliers: Optional[EstatisticasPreco] = Field(
        None, description="Estatísticas excluindo outliers"
    )
    
    itens: List[ItemPreco] = Field(default_factory=list, description="Lista de itens com preços")
    total_registros: int = Field(description="Total de registros na API")
    total_paginas: int = Field(description="Total de páginas")
    data_consulta: datetime = Field(description="Data/hora da consulta")


class RespostaPdmFamilia(BaseModel):
    """Modelo para resposta da família PDM"""
    codigo_pdm: int
    nome_pdm: str
    itens_catalogo: List[ItemCatalogo] = Field(default_factory=list)
    total_itens: int = 0


class ParametrosPesquisa(BaseModel):
    """Parâmetros para pesquisa de preços"""
    codigo_catmat: int = Field(..., description="Código CATMAT ou CATSERV", ge=1)
    tipo_catalogo: TipoCatalogo = Field(TipoCatalogo.MATERIAL, description="Tipo: material ou servico")
    pesquisar_familia_pdm: bool = Field(False, description="Pesquisar toda família PDM")
    estado: Optional[str] = Field(None, description="Filtro por estado (UF)", max_length=2)
    pagina: int = Field(1, description="Página da pesquisa", ge=1)
    tamanho_pagina: int = Field(100, description="Tamanho da página", ge=1, le=500)


# ============================================================
# Modelos PNCP - Portal Nacional de Contratações Públicas
# ============================================================

class ContratacaoPNCP(BaseModel):
    """Modelo para dados de contratação do PNCP"""
    model_config = ConfigDict(populate_by_name=True, ser_json_by_alias=True)
    
    # Identificação
    id_compra: Optional[str] = Field(None, alias="idCompra", serialization_alias="idCompra")
    numero_compra: Optional[str] = Field(None, alias="numeroCompra", serialization_alias="numeroCompra")
    numero_processo: Optional[str] = Field(None, alias="numeroProcesso", serialization_alias="numeroProcesso")
    ano_compra: Optional[int] = Field(None, alias="anoCompra", serialization_alias="anoCompra")
    
    # Modalidade e tipo
    modalidade_nome: Optional[str] = Field(None, alias="modalidadeNome", serialization_alias="modalidadeNome")
    modalidade_id: Optional[int] = Field(None, alias="modalidadeId", serialization_alias="modalidadeId")
    modo_disputa_nome: Optional[str] = Field(None, alias="modoDisputaNome", serialization_alias="modoDisputaNome")
    situacao_compra_nome: Optional[str] = Field(None, alias="situacaoCompraNome", serialization_alias="situacaoCompraNome")
    situacao_compra_id: Optional[int] = Field(None, alias="situacaoCompraId", serialization_alias="situacaoCompraId")
    
    # Órgão/UASG
    codigo_uasg: Optional[str] = Field(None, alias="codigoUasg", serialization_alias="codigoUasg")
    nome_uasg: Optional[str] = Field(None, alias="nomeUasg", serialization_alias="nomeUasg")
    codigo_orgao: Optional[int] = Field(None, alias="codigoOrgao", serialization_alias="codigoOrgao")
    nome_orgao: Optional[str] = Field(None, alias="nomeOrgao", serialization_alias="nomeOrgao")
    cnpj_orgao: Optional[str] = Field(None, alias="cnpjOrgao", serialization_alias="cnpjOrgao")
    
    # Objeto
    objeto_compra: Optional[str] = Field(None, alias="objetoCompra", serialization_alias="objetoCompra")
    informacao_complementar: Optional[str] = Field(None, alias="informacaoComplementar", serialization_alias="informacaoComplementar")
    
    # Datas
    data_publicacao_pncp: Optional[datetime] = Field(None, alias="dataPublicacaoPncp", serialization_alias="dataPublicacaoPncp")
    data_abertura_proposta: Optional[datetime] = Field(None, alias="dataAberturaProposta", serialization_alias="dataAberturaProposta")
    data_encerramento_proposta: Optional[datetime] = Field(None, alias="dataEncerramentoProposta", serialization_alias="dataEncerramentoProposta")
    data_inicio_vigencia: Optional[datetime] = Field(None, alias="dataInicioVigencia", serialization_alias="dataInicioVigencia")
    data_fim_vigencia: Optional[datetime] = Field(None, alias="dataFimVigencia", serialization_alias="dataFimVigencia")
    
    # Valores
    valor_total_estimado: Optional[float] = Field(None, alias="valorTotalEstimado", serialization_alias="valorTotalEstimado")
    valor_total_homologado: Optional[float] = Field(None, alias="valorTotalHomologado", serialization_alias="valorTotalHomologado")
    
    # Links
    link_sistema_origem: Optional[str] = Field(None, alias="linkSistemaOrigem", serialization_alias="linkSistemaOrigem")
    link_pncp: Optional[str] = Field(None, alias="linkPncp", serialization_alias="linkPncp")
    uri_pncp: Optional[str] = Field(None, alias="uriPncp", serialization_alias="uriPncp")

    # Campos para construir URL PNCP: https://pncp.gov.br/app/contratos/{cnpj}/{ano}/{sequencial}
    orgao_entidade_cnpj: Optional[str] = Field(None, alias="orgaoEntidadeCnpj", serialization_alias="orgaoEntidadeCnpj")
    ano_compra_pncp: Optional[int] = Field(None, alias="anoCompraPncp", serialization_alias="anoCompraPncp")
    sequencial_compra_pncp: Optional[int] = Field(None, alias="sequencialCompraPncp", serialization_alias="sequencialCompraPncp")
    numero_controle_pncp: Optional[str] = Field(None, alias="numeroControlePNCP", serialization_alias="numeroControlePNCP")

    # Localização
    uf: Optional[str] = None
    municipio: Optional[str] = None

    # Outros
    srp: Optional[bool] = Field(None, description="Sistema de Registro de Preços")
    tipo_instrumento_convocatorio: Optional[str] = Field(None, alias="tipoInstrumentoConvocatorio", serialization_alias="tipoInstrumentoConvocatorio")
    criterio_julgamento: Optional[str] = Field(None, alias="criterioJulgamento", serialization_alias="criterioJulgamento")

    @property
    def url_pncp_construida(self) -> Optional[str]:
        """Constrói a URL do PNCP a partir dos campos disponíveis"""
        # Tenta construir a URL do PNCP usando os campos disponíveis
        # Formato: https://pncp.gov.br/app/editais/{cnpj}/{ano}/{sequencial}
        if self.orgao_entidade_cnpj and self.ano_compra_pncp and self.sequencial_compra_pncp:
            return f"https://pncp.gov.br/app/editais/{self.orgao_entidade_cnpj}/{self.ano_compra_pncp}/{self.sequencial_compra_pncp}"
        # Ou usando o cnpjOrgao e anoCompra
        if self.cnpj_orgao and self.ano_compra and self.numero_compra:
            cnpj_limpo = self.cnpj_orgao.replace('.', '').replace('/', '').replace('-', '')
            return f"https://pncp.gov.br/app/editais/{cnpj_limpo}/{self.ano_compra}/{self.numero_compra}"
        # Fallback para link direto se disponível
        if self.link_pncp:
            return self.link_pncp
        if self.uri_pncp:
            return f"https://pncp.gov.br{self.uri_pncp}"
        return None


class ItemContratacao(BaseModel):
    """Modelo para itens da contratação PNCP"""
    model_config = ConfigDict(populate_by_name=True, ser_json_by_alias=True)

    numero_item: Optional[int] = Field(None, alias="numeroItem", serialization_alias="numeroItem")
    descricao: Optional[str] = None
    quantidade: Optional[float] = None
    unidade_medida: Optional[str] = Field(None, alias="unidadeMedida", serialization_alias="unidadeMedida")
    valor_unitario_estimado: Optional[float] = Field(None, alias="valorUnitarioEstimado", serialization_alias="valorUnitarioEstimado")
    valor_total_estimado: Optional[float] = Field(None, alias="valorTotalEstimado", serialization_alias="valorTotalEstimado")
    codigo_item_catalogo: Optional[int] = Field(None, alias="codigoItemCatalogo", serialization_alias="codigoItemCatalogo")
    tipo_item: Optional[str] = Field(None, alias="tipoItem", serialization_alias="tipoItem")
    situacao_item: Optional[str] = Field(None, alias="situacaoItem", serialization_alias="situacaoItem")

    # Campos adicionais para análise
    material_ou_servico: Optional[str] = Field(None, alias="materialOuServico", serialization_alias="materialOuServico")
    tem_resultado: Optional[bool] = Field(None, alias="temResultado", serialization_alias="temResultado")
    codigo_ncm: Optional[str] = Field(None, alias="codigoNCM", serialization_alias="codigoNCM")
    criterio_julgamento: Optional[str] = Field(None, alias="criterioJulgamento", serialization_alias="criterioJulgamento")

    # Identificadores
    id_compra_item: Optional[int] = Field(None, alias="idCompraItem", serialization_alias="idCompraItem")


class ResultadoItemContratacao(BaseModel):
    """Modelo para resultados/vencedores de itens da contratação"""
    model_config = ConfigDict(populate_by_name=True, ser_json_by_alias=True)

    numero_item: Optional[int] = Field(None, alias="numeroItem", serialization_alias="numeroItem")
    descricao_item: Optional[str] = Field(None, alias="descricaoItem", serialization_alias="descricaoItem")

    # Fornecedor vencedor
    nome_fornecedor: Optional[str] = Field(None, alias="nomeFornecedor", serialization_alias="nomeFornecedor")
    ni_fornecedor: Optional[str] = Field(None, alias="niFornecedor", serialization_alias="niFornecedor")
    tipo_fornecedor: Optional[str] = Field(None, alias="tipoFornecedor", serialization_alias="tipoFornecedor")

    # Porte e natureza jurídica do fornecedor
    porte_fornecedor_id: Optional[int] = Field(None, alias="porteFornecedorId", serialization_alias="porteFornecedorId")
    porte_fornecedor_nome: Optional[str] = Field(None, alias="porteFornecedorNome", serialization_alias="porteFornecedorNome")
    natureza_juridica_id: Optional[int] = Field(None, alias="naturezaJuridicaId", serialization_alias="naturezaJuridicaId")
    natureza_juridica_nome: Optional[str] = Field(None, alias="naturezaJuridicaNome", serialization_alias="naturezaJuridicaNome")

    # Valores homologados
    quantidade_homologada: Optional[float] = Field(None, alias="quantidadeHomologada", serialization_alias="quantidadeHomologada")
    valor_unitario_homologado: Optional[float] = Field(None, alias="valorUnitarioHomologado", serialization_alias="valorUnitarioHomologado")
    valor_total_homologado: Optional[float] = Field(None, alias="valorTotalHomologado", serialization_alias="valorTotalHomologado")

    # Detalhes do produto
    percentual_desconto: Optional[float] = Field(None, alias="percentualDesconto", serialization_alias="percentualDesconto")
    data_homologacao: Optional[datetime] = Field(None, alias="dataHomologacao", serialization_alias="dataHomologacao")
    marca: Optional[str] = None
    modelo: Optional[str] = None
    fabricante: Optional[str] = None

    # Benefícios e critérios aplicados (importantes para análise de preço)
    aplicacao_margem_preferencia: Optional[bool] = Field(None, alias="aplicacaoMargemPreferencia", serialization_alias="aplicacaoMargemPreferencia")
    aplicacao_beneficio_meepp: Optional[bool] = Field(None, alias="aplicacaoBeneficioMeepp", serialization_alias="aplicacaoBeneficioMeepp")
    aplicacao_criterio_desempate: Optional[bool] = Field(None, alias="aplicacaoCriterioDesempate", serialization_alias="aplicacaoCriterioDesempate")

    # Situação do resultado
    situacao_resultado_id: Optional[int] = Field(None, alias="situacaoCompraItemResultadoId", serialization_alias="situacaoCompraItemResultadoId")
    situacao_resultado_nome: Optional[str] = Field(None, alias="situacaoCompraItemResultadoNome", serialization_alias="situacaoCompraItemResultadoNome")


class DetalhesContratacao(BaseModel):
    """Modelo consolidado com todos os detalhes da contratação"""
    encontrado: bool = Field(True, description="Se encontrou dados da contratação")
    mensagem: Optional[str] = Field(None, description="Mensagem de erro ou aviso")

    # Identificação para debug/investigação
    id_compra: Optional[str] = Field(None, alias="idCompra", serialization_alias="idCompra", description="ID da compra consultado")
    url_pncp: Optional[str] = Field(None, alias="urlPncp", serialization_alias="urlPncp", description="URL construída do PNCP")

    contratacao: Optional[ContratacaoPNCP] = Field(None, description="Dados gerais da contratação")
    itens: List[ItemContratacao] = Field(default_factory=list, description="Itens da contratação")
    resultados: List[ResultadoItemContratacao] = Field(default_factory=list, description="Resultados/vencedores")


class DetalheItemPNCP(BaseModel):
    """Detalhes do item específico obtidos do PNCP - para enriquecer ItemPreco"""
    model_config = ConfigDict(populate_by_name=True, ser_json_by_alias=True)

    # Dados da contratação
    modalidade_nome: Optional[str] = Field(None, alias="modalidadeNome", serialization_alias="modalidadeNome")
    situacao_compra: Optional[str] = Field(None, alias="situacaoCompraNome", serialization_alias="situacaoCompraNome")
    objeto_compra: Optional[str] = Field(None, alias="objetoCompra", serialization_alias="objetoCompra")
    srp: Optional[bool] = Field(None, description="Sistema de Registro de Preços")

    # Valores estimados (referência) - importantes para análise de preço
    quantidade_licitada: Optional[float] = Field(None, alias="quantidadeLicitada", serialization_alias="quantidadeLicitada")
    valor_unitario_estimado: Optional[float] = Field(None, alias="valorUnitarioEstimado", serialization_alias="valorUnitarioEstimado")
    valor_total_estimado: Optional[float] = Field(None, alias="valorTotalEstimado", serialization_alias="valorTotalEstimado")

    # Detalhes do produto vencedor
    marca: Optional[str] = None
    modelo: Optional[str] = None
    fabricante: Optional[str] = None

    # Benefícios aplicados
    aplicacao_margem_preferencia: Optional[bool] = Field(None, alias="aplicacaoMargemPreferencia", serialization_alias="aplicacaoMargemPreferencia")
    aplicacao_beneficio_meepp: Optional[bool] = Field(None, alias="aplicacaoBeneficioMeepp", serialization_alias="aplicacaoBeneficioMeepp")

    # Porte do fornecedor
    porte_fornecedor: Optional[str] = Field(None, alias="porteFornecedorNome", serialization_alias="porteFornecedorNome")

    # Links
    url_pncp: Optional[str] = Field(None, alias="urlPncp", serialization_alias="urlPncp", description="URL construída do PNCP")
    link_sistema_origem: Optional[str] = Field(None, alias="linkSistemaOrigem", serialization_alias="linkSistemaOrigem")


# Resolver forward reference
ItemPreco.model_rebuild()
