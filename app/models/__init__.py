"""
Sistema LIA - Models Package 
=============================
Importa todos os modelos do sistema para facilitar uso
"""

from .user import User
from .pac import PAC
from .artefatos import (
    DFD, ETP, TR, Riscos, ItemRisco, Edital, PesquisaPrecos,
    PortariaDesignacao,
    RelatorioVantagemEconomica, JustificativaVantagemAdesao, TermoAceiteFornecedorOrgao,
    TRSimplificado, AvisoDispensaEletronica, JustificativaPrecoEscolhaFornecedor, CertidaoEnquadramento,
    ChecklistConformidade, MinutaContrato,
    AvisoPublicidadeDireta, JustificativaFornecedorEscolhido,
    ARTEFATO_MAP,
)
from .projeto import Projeto
from .skill import Skill
from .prompt_template import PromptTemplate

# Re-export field configs from config module for backwards compatibility
from app.config_fields.fields_config import (
    DFD_CAMPOS_CONFIG, ETP_CAMPOS_CONFIG, TR_CAMPOS_CONFIG, 
    RISCOS_CAMPOS_CONFIG, EDITAL_CAMPOS_CONFIG, PESQUISA_PRECOS_CAMPOS_CONFIG
)

__all__ = [
    "User",
    "PAC",
    "Projeto",
    "Skill",
    "PromptTemplate",
    "DFD",
    "ETP",
    "TR",
    "Riscos",
    "ItemRisco",
    "Edital",
    "PesquisaPrecos",
    "PortariaDesignacao",
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
    "ARTEFATO_MAP",
    # Field configs (for backwards compatibility)
    "DFD_CAMPOS_CONFIG",
    "ETP_CAMPOS_CONFIG", 
    "TR_CAMPOS_CONFIG",
    "RISCOS_CAMPOS_CONFIG",
    "EDITAL_CAMPOS_CONFIG",
    "PESQUISA_PRECOS_CAMPOS_CONFIG",
]
