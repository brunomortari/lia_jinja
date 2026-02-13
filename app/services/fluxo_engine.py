"""
Sistema LIA - Motor de Fluxo de Artefatos
==========================================
Arquivo único e centralizado com TODAS as regras de negócio do fluxo
de contratação. Determina quais artefatos estão disponíveis, bloqueados
ou ocultos com base no estado do projeto.

Regras de negócio (Lei 14.133/2021):
─────────────────────────────────────
Gateway Inicial:
  • intra_pac=True  → DFD direto
  • intra_pac=False → JE (obrigatório) → DFD

Gateway ETP (modalidade_definida):
  • adesao_ata           → RDVE → JVA → TAFO (FIM)
  • dispensa_valor_baixo → TRS → ADE → JPEF → CE (FIM)
  • licitacao_normal     → PP → PGR → TR → [Gateway TR]

Gateway TR (contratacao_direta):
  • True  → APD → JFE → ED → MC (FIM)
  • False → CHK → ED → MC (FIM)

Autor: Equipe TRE-GO
Data: Fevereiro 2026
"""

from __future__ import annotations
from typing import Optional
import logging

logger = logging.getLogger(__name__)


# ═══════════════════════════════════════════════════════════════════
#  DEFINIÇÃO DE ETAPAS — Ordem sequencial dentro de cada ramo
# ═══════════════════════════════════════════════════════════════════

ETAPAS_TRONCO = ["jep", "dfd", "etp"]

ETAPAS_ADESAO = ["rdve", "jva", "tafo"]
ETAPAS_DISPENSA = ["trs", "ade", "jpef", "ce"]
ETAPAS_LICITACAO_PRE_TR = ["pesquisa_precos", "riscos", "tr"]

ETAPAS_LICITACAO_NORMAL = ["checklist_conformidade", "edital", "minuta_contrato"]
ETAPAS_CONTRATACAO_DIRETA = ["aviso_publicidade_direta", "justificativa_fornecedor_escolhido", "edital", "minuta_contrato"]

TODOS_ARTEFATOS = [
    "jep", "dfd", "etp",
    "rdve", "jva", "tafo",
    "trs", "ade", "jpef", "ce",
    "pesquisa_precos", "riscos", "tr",
    "edital", "minuta_contrato",
    "checklist_conformidade",
    "aviso_publicidade_direta", "justificativa_fornecedor_escolhido",
]


# ═══════════════════════════════════════════════════════════════════
#  MAPEAMENTO: tipo → atributo do Projeto (relationship)
# ═══════════════════════════════════════════════════════════════════

TIPO_PARA_RELATION = {
    "jep": "justificativas_excepcionalidade",
    "dfd": "dfds",
    "etp": "etps",
    "pesquisa_precos": "pesquisas_precos",
    "riscos": "riscos",
    "tr": "trs",
    "edital": "editais",
    "minuta_contrato": "minutas_contrato",
    "rdve": "relatorios_vantagem_economica",
    "jva": "justificativas_vantagem_adesao",
    "tafo": "termos_aceite_fornecedor",
    "trs": "trs_simplificados",
    "ade": "avisos_dispensa_eletronica",
    "jpef": "justificativas_preco_escolha",
    "ce": "certidoes_enquadramento",
    "checklist_conformidade": "checklists_conformidade",
    "aviso_publicidade_direta": "avisos_publicidade_direta",
    "justificativa_fornecedor_escolhido": "justificativas_fornecedor_escolhido",
}

SIGLAS = {
    "jep": "JE", "dfd": "DFD", "etp": "ETP",
    "pesquisa_precos": "PP", "riscos": "PGR", "tr": "TR",
    "edital": "ED", "minuta_contrato": "MC",
    "rdve": "RDVE", "jva": "JVA", "tafo": "TAFO",
    "trs": "TRS", "ade": "ADE", "jpef": "JPEF", "ce": "CE",
    "checklist_conformidade": "CHK",
    "aviso_publicidade_direta": "APD",
    "justificativa_fornecedor_escolhido": "JFE",
}

TITULOS = {
    "jep": "Justificativa de Excepcionalidade",
    "dfd": "Documento de Formalização da Demanda",
    "etp": "Estudo Técnico Preliminar",
    "pesquisa_precos": "Pesquisa de Preços",
    "riscos": "Plano de Gerenciamento de Riscos",
    "tr": "Termo de Referência",
    "edital": "Edital de Licitação",
    "minuta_contrato": "Minuta de Contrato",
    "rdve": "Relatório de Demonstração de Vantagem Econômica",
    "jva": "Justificativa da Vantagem da Adesão",
    "tafo": "Termo de Aceite do Fornecedor e do Órgão Gerenciador",
    "trs": "Termo de Referência Simplificado",
    "ade": "Aviso de Dispensa Eletrônica",
    "jpef": "Justificativa de Preço e Escolha do Fornecedor",
    "ce": "Certidão de Enquadramento",
    "checklist_conformidade": "Checklist de Instrução (AGU/SEGES)",
    "aviso_publicidade_direta": "Aviso de Dispensa de Licitação",
    "justificativa_fornecedor_escolhido": "Justificativa do Fornecedor Escolhido",
}

BRANCH_ARTEFATOS = {
    "adesao":    ETAPAS_ADESAO,
    "dispensa":  ETAPAS_DISPENSA,
    "licitacao": ETAPAS_LICITACAO_PRE_TR + ETAPAS_LICITACAO_NORMAL,
    "direta":    ETAPAS_LICITACAO_PRE_TR + ETAPAS_CONTRATACAO_DIRETA,
}

BRANCH_CORES = {
    "adesao":    {"cor": "#10B981", "cor_bg": "#ECFDF5", "cor_text": "#065F46", "label": "Adesão a Ata de Registro de Preços"},
    "dispensa":  {"cor": "#F97316", "cor_bg": "#FFF7ED", "cor_text": "#9A3412", "label": "Dispensa por Valor Baixo"},
    "licitacao": {"cor": "#8B5CF6", "cor_bg": "#F5F3FF", "cor_text": "#5B21B6", "label": "Licitação Normal"},
    "direta":    {"cor": "#EC4899", "cor_bg": "#FDF2F8", "cor_text": "#9D174D", "label": "Contratação Direta"},
}


# ═══════════════════════════════════════════════════════════════════
#  FUNÇÕES AUXILIARES
# ═══════════════════════════════════════════════════════════════════

def _tem_artefato(projeto, tipo: str) -> bool:
    """Verifica se o projeto possui pelo menos um artefato do tipo."""
    relation = TIPO_PARA_RELATION.get(tipo)
    if not relation:
        return False
    items = getattr(projeto, relation, None)
    return bool(items and len(items) > 0)


def _artefato_concluido(projeto, tipo: str) -> bool:
    """Verifica se o artefato mais recente está aprovado/publicado."""
    relation = TIPO_PARA_RELATION.get(tipo)
    if not relation:
        return False
    items = getattr(projeto, relation, None)
    if not items or len(items) == 0:
        return False
    # Relationships são desc(data_criacao) → [0] = mais recente
    latest = items[0]
    is_published = hasattr(latest, 'protocolo_sei') and latest.protocolo_sei is not None
    is_approved = hasattr(latest, 'status') and latest.status in ('publicado', 'aprovado', 'concluido')
    return is_published or is_approved


def _obter_etp_mais_recente(projeto):
    """Retorna o ETP mais recente ou None."""
    etps = getattr(projeto, 'etps', None)
    if etps and len(etps) > 0:
        # Relationships são desc(data_criacao) → [0] = mais recente
        return etps[0]
    return None


def _obter_tr_mais_recente(projeto):
    """Retorna o TR mais recente ou None."""
    trs = getattr(projeto, 'trs', None)
    if trs and len(trs) > 0:
        # Relationships são desc(data_criacao) → [0] = mais recente
        return trs[0]
    return None


# ═══════════════════════════════════════════════════════════════════
#  DETECÇÃO DE BRANCH ATIVO
# ═══════════════════════════════════════════════════════════════════

def obter_branch_ativo(projeto) -> tuple[Optional[str], bool]:
    """
    Determina qual branch está ativo com base no ETP e TR.

    Returns:
        (branch_name, decision_resolved)
        branch_name: 'adesao' | 'dispensa' | 'licitacao' | 'direta' | None
    """
    etp = _obter_etp_mais_recente(projeto)
    if not etp:
        logger.info("[FLUXO] obter_branch_ativo: Nenhum ETP encontrado")
        return None, False

    logger.info(f"[FLUXO] obter_branch_ativo: ETP id={etp.id}, versao={etp.versao}, "
                f"modalidade_sugerida={getattr(etp, 'modalidade_sugerida', 'N/A')}, "
                f"modalidade_definida={getattr(etp, 'modalidade_definida', 'N/A')}")

    modalidade = getattr(etp, 'modalidade_definida', None)
    if not modalidade:
        logger.info("[FLUXO] obter_branch_ativo: modalidade_definida está VAZIA")
        # Fallback: tentar modalidade_sugerida
        modalidade = getattr(etp, 'modalidade_sugerida', None)
        if not modalidade:
            logger.info("[FLUXO] obter_branch_ativo: modalidade_sugerida também VAZIA")
            return None, False
        logger.info(f"[FLUXO] obter_branch_ativo: Usando modalidade_sugerida={modalidade}")

    modalidade = modalidade.lower().strip()
    logger.info(f"[FLUXO] obter_branch_ativo: modalidade normalizada='{modalidade}'")

    if modalidade == 'adesao_ata':
        return 'adesao', True
    elif modalidade == 'dispensa_valor_baixo':
        return 'dispensa', True
    elif modalidade == 'licitacao_normal':
        tr = _obter_tr_mais_recente(projeto)
        if tr and getattr(tr, 'contratacao_direta', False):
            return 'direta', True
        return 'licitacao', True

    logger.warning(f"[FLUXO] obter_branch_ativo: modalidade '{modalidade}' NÃO RECONHECIDA")
    return None, False


# ═══════════════════════════════════════════════════════════════════
#  VERIFICAÇÃO DE DEPENDÊNCIAS
# ═══════════════════════════════════════════════════════════════════

def verificar_dependencias(projeto, tipo: str) -> dict:
    """
    Verifica se as dependências de um artefato estão satisfeitas.
    Returns: {"liberado": bool, "faltando": ["SIGLA", ...]}
    """
    projeto_sem_pac = not bool(getattr(projeto, 'intra_pac', 1))
    faltando = []

    # ── TRONCO ──
    if tipo == "jep":
        return {"liberado": True, "faltando": []}

    if tipo == "dfd":
        if projeto_sem_pac and not _tem_artefato(projeto, "jep"):
            faltando.append("JE")
        return {"liberado": len(faltando) == 0, "faltando": faltando}

    if tipo == "etp":
        if not _tem_artefato(projeto, "dfd"):
            faltando.append("DFD")
        return {"liberado": len(faltando) == 0, "faltando": faltando}

    # ── ADESÃO A ATA ──
    if tipo == "rdve":
        if not _tem_artefato(projeto, "etp"):
            faltando.append("ETP")
    elif tipo == "jva":
        if not _tem_artefato(projeto, "rdve"):
            faltando.append("RDVE")
    elif tipo == "tafo":
        if not _tem_artefato(projeto, "jva"):
            faltando.append("JVA")

    # ── DISPENSA VALOR BAIXO ──
    elif tipo == "trs":
        if not _tem_artefato(projeto, "etp"):
            faltando.append("ETP")
    elif tipo == "ade":
        if not _tem_artefato(projeto, "trs"):
            faltando.append("TRS")
    elif tipo == "jpef":
        if not _tem_artefato(projeto, "ade"):
            faltando.append("ADE")
    elif tipo == "ce":
        if not _tem_artefato(projeto, "jpef"):
            faltando.append("JPEF")

    # ── LICITAÇÃO NORMAL (pré-TR) ──
    elif tipo in ("pesquisa_precos", "riscos", "tr"):
        if not _tem_artefato(projeto, "etp"):
            faltando.append("ETP")

    # ── PÓS-TR ──
    elif tipo == "checklist_conformidade":
        if not _tem_artefato(projeto, "tr"):
            faltando.append("TR")
    elif tipo == "aviso_publicidade_direta":
        if not _tem_artefato(projeto, "tr"):
            faltando.append("TR")
    elif tipo == "justificativa_fornecedor_escolhido":
        if not _tem_artefato(projeto, "aviso_publicidade_direta"):
            faltando.append("APD")
    elif tipo == "edital":
        if not _tem_artefato(projeto, "tr"):
            faltando.append("TR")
    elif tipo == "minuta_contrato":
        if not _tem_artefato(projeto, "edital"):
            faltando.append("ED")
    else:
        return {"liberado": False, "faltando": ["configuração inválida"]}

    return {"liberado": len(faltando) == 0, "faltando": faltando}


# ═══════════════════════════════════════════════════════════════════
#  CÁLCULO COMPLETO DO FLUXO
# ═══════════════════════════════════════════════════════════════════

def calcular_fluxo(projeto) -> dict:
    """
    Calcula o estado completo do fluxo para um projeto.
    Retorna tudo que a view e o template precisam.
    """
    projeto_sem_pac = not bool(getattr(projeto, 'intra_pac', 1))
    active_branch, decision_resolved = obter_branch_ativo(projeto)

    logger.info(f"[FLUXO] calcular_fluxo: projeto_id={getattr(projeto, 'id', '?')}, "
                f"sem_pac={projeto_sem_pac}, active_branch={active_branch}, "
                f"decision_resolved={decision_resolved}, "
                f"num_etps={len(getattr(projeto, 'etps', []))}, "
                f"num_dfds={len(getattr(projeto, 'dfds', []))}")

    sub_branch = None
    if active_branch in ('licitacao', 'direta'):
        sub_branch = active_branch

    etapas = []
    flow_state = {}
    artefatos_status = {}

    def _add_etapa(tipo, branch=None, is_gateway=False, gateway_label=None):
        deps = verificar_dependencias(projeto, tipo)
        artefatos_status[tipo] = deps

        if _artefato_concluido(projeto, tipo):
            estado = "completed"
        elif _tem_artefato(projeto, tipo):
            estado = "active"
        elif deps["liberado"]:
            estado = "active"
        else:
            estado = "locked"

        flow_state[tipo] = estado

        etapas.append({
            "tipo": tipo,
            "sigla": SIGLAS.get(tipo, tipo.upper()),
            "titulo": TITULOS.get(tipo, tipo),
            "estado": estado,
            "liberado": deps["liberado"],
            "faltando": deps["faltando"],
            "branch": branch,
            "is_gateway": is_gateway,
            "gateway_label": gateway_label,
        })

    # ── 1. TRONCO ──
    if projeto_sem_pac:
        _add_etapa("jep")
    _add_etapa("dfd")
    # ETP só aparece após DFD ser criado
    if _tem_artefato(projeto, "dfd"):
        _add_etapa("etp")

    # ── 2. BRANCH PÓS-ETP ──
    if active_branch == "adesao":
        for tipo in ETAPAS_ADESAO:
            _add_etapa(tipo, branch="adesao")

    elif active_branch == "dispensa":
        for tipo in ETAPAS_DISPENSA:
            _add_etapa(tipo, branch="dispensa")

    elif active_branch in ("licitacao", "direta"):
        # Sempre mostrar pré-TR (PP, PGR, TR)
        for tipo in ETAPAS_LICITACAO_PRE_TR:
            _add_etapa(tipo, branch="licitacao")

        # Só mostrar pós-TR se o TR foi criado
        # (gateway TR: contratacao_direta determina o sub-branch)
        if _tem_artefato(projeto, "tr"):
            if sub_branch == "direta":
                _add_etapa("aviso_publicidade_direta", branch="direta")
                _add_etapa("justificativa_fornecedor_escolhido", branch="direta")
                _add_etapa("edital", branch="direta")
                _add_etapa("minuta_contrato", branch="direta")
            else:
                _add_etapa("checklist_conformidade", branch="licitacao")
                _add_etapa("edital", branch="licitacao")
                _add_etapa("minuta_contrato", branch="licitacao")

    return {
        "projeto_sem_pac": projeto_sem_pac,
        "active_branch": active_branch,
        "decision_resolved": decision_resolved,
        "sub_branch": sub_branch,
        "etapas": etapas,
        "flow_state": flow_state,
        "artefatos_status": artefatos_status,
    }


# ═══════════════════════════════════════════════════════════════════
#  HELPERS PARA TEMPLATE
# ═══════════════════════════════════════════════════════════════════

def obter_cor_branch(branch: Optional[str]) -> dict:
    """Retorna cores do branch para uso na UI."""
    if not branch:
        return {"cor": "#3B82F6", "cor_bg": "#EFF6FF", "cor_text": "#1E40AF", "label": "Fluxo Principal"}
    return BRANCH_CORES.get(branch, BRANCH_CORES["licitacao"])
