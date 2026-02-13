""" 
Sistema LIA - Modelos de Artefatos (Pacote Modular)
====================================================
Define a estrutura dos artefatos do processo de contratação.

Autor: Equipe TRE-GO
Data: Fevereiro 2026
"""

# Importar todas as classes dos módulos
from .base import ArtefatoBase, ArtefatoBloqueadoError
from .dfd import DFD
from .etp import ETP
from .tr import TR
from .edital import Edital
from .pp import PesquisaPrecos
from .pd import PortariaDesignacao
from .riscos import Riscos, ItemRisco
from .rdve import RelatorioVantagemEconomica
from .jva import JustificativaVantagemAdesao
from .tafo import TermoAceiteFornecedorOrgao
from .trs import TRSimplificado
from .ade import AvisoDispensaEletronica
from .jpef import JustificativaPrecoEscolhaFornecedor
from .ce import CertidaoEnquadramento
from .chk import ChecklistConformidade
from .mc import MinutaContrato
from .apd import AvisoPublicidadeDireta
from .jfe import JustificativaFornecedorEscolhido
from .jep import JustificativaExcepcionalidade

# Importar configurações de campos
from app.config_fields.fields_config import (
    DFD_CAMPOS_CONFIG,
    ETP_CAMPOS_CONFIG,
    TR_CAMPOS_CONFIG,
    RISCOS_CAMPOS_CONFIG,
    EDITAL_CAMPOS_CONFIG,
    PESQUISA_PRECOS_CAMPOS_CONFIG,
    PORTARIA_DESIGNACAO_CAMPOS_CONFIG,
    RDVE_CAMPOS_CONFIG,
    JVA_CAMPOS_CONFIG,
    TAFO_CAMPOS_CONFIG,
    TRS_CAMPOS_CONFIG,
    ADE_CAMPOS_CONFIG,
    JPEF_CAMPOS_CONFIG,
    CE_CAMPOS_CONFIG,
    CHECKLIST_CONFORMIDADE_CAMPOS_CONFIG,
    MINUTA_CONTRATO_CAMPOS_CONFIG,
    AVISO_PUBLICIDADE_DIRETA_CAMPOS_CONFIG,
    JUSTIFICATIVA_FORNECEDOR_CAMPOS_CONFIG,
    JEP_CAMPOS_CONFIG,
)

# ========== MAPEAMENTO CENTRALIZADO DE ARTEFATOS ==========
# Configuração única usada por export.py, ia.py, artefatos_service.py, common.py

ARTEFATO_MAP = {
    "jep": {
        "model": JustificativaExcepcionalidade,
        "config": JEP_CAMPOS_CONFIG,
        "titulo": "Justificativa de Contratação não Planejada",
        "sigla": "JEP",
        "icone": "alert-octagon",
        "cor": "#E53E3E",
        "relation": "justificativas_excepcionalidade",
        "requer": [],
        "ordem": 0,
        "condicional": "sem_pac"
    },
    "dfd": {
        "model": DFD,
        "config": DFD_CAMPOS_CONFIG,
        "titulo": "Documento de Formalização da Demanda",
        "sigla": "DFD",
        "icone": "file-text",
        "cor": "#3182CE",
        "relation": "dfds",
        "requer": [],
        "ordem": 1
    },
    "etp": {
        "model": ETP,
        "config": ETP_CAMPOS_CONFIG,
        "titulo": "Estudo Técnico Preliminar",
        "sigla": "ETP",
        "icone": "clipboard",
        "cor": "#38A169",
        "relation": "etps",
        "requer": ["dfd"],
        "ordem": 2
    },
    "pesquisa_precos": {
        "model": PesquisaPrecos,
        "config": PESQUISA_PRECOS_CAMPOS_CONFIG,
        "titulo": "Pesquisa de Preços",
        "sigla": "PP",
        "icone": "dollar-sign",
        "cor": "#319795",
        "relation": "pesquisas_precos",
        "requer": ["dfd"],
        "ordem": 3
    },
    "riscos": {
        "model": Riscos,
        "config": RISCOS_CAMPOS_CONFIG,
        "titulo": "Plano de Gerenciamento de Riscos",
        "sigla": "PGR",
        "icone": "alert-triangle",
        "cor": "#E53E3E",
        "relation": "riscos",
        "requer": ["dfd"],
        "ordem": 4
    },
    "tr": {
        "model": TR,
        "config": TR_CAMPOS_CONFIG,
        "titulo": "Termo de Referência",
        "sigla": "TR",
        "icone": "file-check",
        "cor": "#D69E2E",
        "relation": "trs",
        "requer": ["etp"],
        "ordem": 5
    },
    "edital": {
        "model": Edital,
        "config": EDITAL_CAMPOS_CONFIG,
        "titulo": "Edital de Licitação",
        "sigla": "ED",
        "icone": "file-signature",
        "cor": "#805AD5",
        "relation": "editais",
        "requer": ["tr"],
        "ordem": 6
    },
    # Alias para compatibilidade - "pgr" aponta para "riscos"
    "pgr": {
        "model": Riscos,
        "config": RISCOS_CAMPOS_CONFIG,
        "titulo": "Plano de Gerenciamento de Riscos",
        "sigla": "PGR",
        "icone": "alert-triangle",
        "cor": "#E53E3E",
        "relation": "riscos",
        "requer": ["dfd"],
        "ordem": 4
    },
    "portaria_designacao": {
        "model": PortariaDesignacao,
        "config": PORTARIA_DESIGNACAO_CAMPOS_CONFIG,
        "titulo": "Portaria de Designação",
        "sigla": "PD",
        "icone": "file-signature",
        "cor": "#7C3AED",
        "relation": "portarias_designacao",
        "requer": ["dfd"],
        "ordem": 1.5,
        "virtual": True
    },
    # ========== FLUXO DE ADESÃO A ATA DE REGISTRO DE PREÇOS ==========
    "rdve": {
        "model": RelatorioVantagemEconomica,
        "config": RDVE_CAMPOS_CONFIG,
        "titulo": "Relatório de Demonstração de Vantagem Econômica",
        "sigla": "RDVE",
        "icone": "trending-up",
        "cor": "#4299E1",
        "relation": "relatorios_vantagem_economica",
        "requer": ["etp"],
        "ordem": 2.1,
        "fluxo": "adesao_ata"
    },
    "jva": {
        "model": JustificativaVantagemAdesao,
        "config": JVA_CAMPOS_CONFIG,
        "titulo": "Justificativa de Vantagem e Conveniência da Adesão",
        "sigla": "JVA",
        "icone": "file-check",
        "cor": "#38B2AC",
        "relation": "justificativas_vantagem_adesao",
        "requer": ["rdve"],
        "ordem": 2.2,
        "fluxo": "adesao_ata"
    },
    "tafo": {
        "model": TermoAceiteFornecedorOrgao,
        "config": TAFO_CAMPOS_CONFIG,
        "titulo": "Termo de Aceite do Fornecedor pela Administração",
        "sigla": "TAFO",
        "icone": "file-signature",
        "cor": "#4A90E2",
        "relation": "termos_aceite_fornecedor",
        "requer": ["jva"],
        "ordem": 2.3,
        "fluxo": "adesao_ata"
    },
    # ========== FLUXO DE DISPENSA POR VALOR BAIXO ==========
    "trs": {
        "model": TRSimplificado,
        "config": TRS_CAMPOS_CONFIG,
        "titulo": "Termo de Referência Simplificado",
        "sigla": "TRS",
        "icone": "file-text",
        "cor": "#ED8936",
        "relation": "trs_simplificados",
        "requer": ["etp"],
        "ordem": 2.4,
        "fluxo": "dispensa_valor_baixo"
    },
    "ade": {
        "model": AvisoDispensaEletronica,
        "config": ADE_CAMPOS_CONFIG,
        "titulo": "Aviso de Dispensa Eletrônica",
        "sigla": "ADE",
        "icone": "alert-circle",
        "cor": "#F56565",
        "relation": "avisos_dispensa_eletronica",
        "requer": ["trs"],
        "ordem": 2.5,
        "fluxo": "dispensa_valor_baixo"
    },
    "jpef": {
        "model": JustificativaPrecoEscolhaFornecedor,
        "config": JPEF_CAMPOS_CONFIG,
        "titulo": "Justificativa de Preço e Escolha de Fornecedor",
        "sigla": "JPEF",
        "icone": "dollar-sign",
        "cor": "#ECC94B",
        "relation": "justificativas_preco_escolha",
        "requer": ["ade"],
        "ordem": 2.6,
        "fluxo": "dispensa_valor_baixo"
    },
    "ce": {
        "model": CertidaoEnquadramento,
        "config": CE_CAMPOS_CONFIG,
        "titulo": "Certidão de Enquadramento na Modalidade de Dispensa",
        "sigla": "CE",
        "icone": "check-circle",
        "cor": "#9AE6B4",
        "relation": "certidoes_enquadramento",
        "requer": ["jpef"],
        "ordem": 2.7,
        "fluxo": "dispensa_valor_baixo"
    },
    # ========== FLUXO DE LICITAÇÃO NORMAL ==========
    "checklist_conformidade": {
        "model": ChecklistConformidade,
        "config": CHECKLIST_CONFORMIDADE_CAMPOS_CONFIG,
        "titulo": "Checklist de Instrução (AGU/SEGES)",
        "sigla": "CHK",
        "icone": "clipboard-check",
        "cor": "#9F7AEA",
        "relation": "checklists_conformidade",
        "requer": ["tr"],
        "ordem": 5.5,
        "fluxo": "licitacao_normal"
    },
    "minuta_contrato": {
        "model": MinutaContrato,
        "config": MINUTA_CONTRATO_CAMPOS_CONFIG,
        "titulo": "Minuta de Contrato",
        "sigla": "MC",
        "icone": "file-contract",
        "cor": "#B794F4",
        "relation": "minutas_contrato",
        "requer": ["edital"],
        "ordem": 6.5,
        "fluxo": "licitacao_normal"
    },
    # ========== FLUXO DE CONTRATAÇÃO DIRETA (DISPENSA/INEXIGIBILIDADE) ==========
    "aviso_publicidade_direta": {
        "model": AvisoPublicidadeDireta,
        "config": AVISO_PUBLICIDADE_DIRETA_CAMPOS_CONFIG,
        "titulo": "Aviso de Dispensa de Licitação",
        "sigla": "APD",
        "icone": "megaphone",
        "cor": "#FC8181",
        "relation": "avisos_publicidade_direta",
        "requer": ["tr"],
        "ordem": 5.6,
        "fluxo": "contratacao_direta"
    },
    "justificativa_fornecedor_escolhido": {
        "model": JustificativaFornecedorEscolhido,
        "config": JUSTIFICATIVA_FORNECEDOR_CAMPOS_CONFIG,
        "titulo": "Justificativa do Fornecedor Escolhido",
        "sigla": "JFE",
        "icone": "user-check",
        "cor": "#F6AD55",
        "relation": "justificativas_fornecedor_escolhido",
        "requer": ["aviso_publicidade_direta"],
        "ordem": 5.7,
        "fluxo": "contratacao_direta"
    },
}

# Exportar tudo
__all__ = [
    # Base
    "ArtefatoBase",
    "ArtefatoBloqueadoError",
    # Models
    "DFD",
    "ETP",
    "TR",
    "Edital",
    "PesquisaPrecos",
    "PortariaDesignacao",
    "Riscos",
    "ItemRisco",
    "RelatorioVantagemEconomica",
    "JustificativaVantagemAdesao",
    "TermoAceiteFornecedorOrgao",
    "TRSimplificado",
    "AvisoDispensaEletronica",
    "JustificativaPrecoEscolhaFornecedor",
    "CertidaoEnquadramento",
    "ChecklistConformidade",
    "MinutaContrato",
    "AvisoPublicidadeDireta",
    "JustificativaFornecedorEscolhido",
    "JustificativaExcepcionalidade",
    # Map
    "ARTEFATO_MAP",
]
