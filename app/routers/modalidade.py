"""
Sistema LIA - Router de Decisão de Modalidade (F2)
===================================================
Endpoints para análise e definição da modalidade de contratação.

Fluxo condicional:
1. Adesão a Ata de Registro de Preços (Lei 14.133/2021, Art. 37)
2. Dispensa por Valor Baixo (Lei 14.133/2021, Art. 75)

Autor: Equipe TRE-GO
Data: Fevereiro 2026
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from datetime import datetime
import logging
from typing import Optional

from app.database import get_db
from app.models.projeto import Projeto
from app.models.user import User
from app.models.artefatos import ETP, ARTEFATO_MAP
from app.auth import current_active_user as auth_get_current_user
from app.schemas.ia_schemas import (
    DefinirModalidadeRequest,
    DefinirModalidadeResponse,
    ConfirmarModalidadeRequest,
    ConfirmarModalidadeResponse,
)

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/modalidade", tags=["Decisão de Modalidade"])


# ========== CONSTANTES E THRESHOLDS ==========

# Lei 14.133/2021, Art. 75: Limites para dispensa
LIMITE_DISPENSA_SIMPLES = 8_800.0  # Dispensa de licitação

# Lei 14.133/2021, Art. 37: Para adesão, regra geral é valor superior
# Mas adesão pode ser mais econômica que contratação direta mesmo com sobrecusto
LIMITE_ADESAO_RECOMENDADO = 192_800.0  # ~Valor proposto/limite administrativo

# Fatores de decisão
PESO_VALOR = 0.40
PESO_COMPLEXIDADE = 0.25
PESO_URGENCIA = 0.15
PESO_ATAS_DISPONIVEIS = 0.20


# ========== ENDPOINTS ==========

@router.post(
    "/analisar",
    response_model=DefinirModalidadeResponse,
    status_code=status.HTTP_200_OK,
    summary="Analisar e sugerir modalidade de contratação",
    tags=["Decisão de Modalidade"]
)
async def analisar_modalidade(
    payload: DefinirModalidadeRequest,
    current_user: User = Depends(auth_get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Analisa os critérios técnicos/legais e sugere a modalidade de contratação.
    
    **Critérios de análise:**
    - Valor estimado vs limites legais
    - Complexidade da contratação
    - Urgência
    - Disponibilidade de atas de registro
    
    **Modalidades sugeridas:**
    - **adesao_ata**: Recomendada para valores intermediários com atas disponíveis
    - **dispensa_valor_baixo**: Para valores baixos (até R$ 8.800)
    
    **Fluxo resultante:**
    - Adesão: RDVE → JVA → TAFO
    - Dispensa: TRS → ADE → JPEF → CE
    """
    
    try:
        # Validar projeto e ETP
        stmt_proj = select(Projeto).where(Projeto.id == payload.projeto_id)
        projeto = await db.scalar(stmt_proj)
        if not projeto:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Projeto {payload.projeto_id} não encontrado"
            )
        
        stmt_etp = select(ETP).where(ETP.id == payload.etp_id)
        etp = await db.scalar(stmt_etp)
        if not etp:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"ETP {payload.etp_id} não encontrada"
            )
        
        # Análise de critérios
        criterios = {}
        scores = {}
        
        # ========== CRITÉRIO 1: VALOR ==========
        valor = payload.valor_estimado
        criterios["valor_limite"] = LIMITE_ADESAO_RECOMENDADO
        criterios["valor_estimado"] = valor
        criterios["valor_abaixo_dispensa"] = valor <= LIMITE_DISPENSA_SIMPLES
        criterios["valor_compativel_adesao"] = valor <= LIMITE_ADESAO_RECOMENDADO
        
        # Score de valor: 0 se fora dos limites, 100 se bem dentro
        if valor <= LIMITE_DISPENSA_SIMPLES:
            scores["valor"] = 100  # Clearcase para dispensa
        elif valor <= LIMITE_ADESAO_RECOMENDADO:
            scores["valor"] = 80  # Bom para adesão
        else:
            scores["valor"] = 40  # Possível mas menos recomendável
        
        # ========== CRITÉRIO 2: COMPLEXIDADE ==========
        complexidade_map = {"simples": 100, "media": 60, "complexa": 20}
        complexidade_score = complexidade_map.get(payload.complexidade, 60)
        scores["complexidade"] = complexidade_score
        criterios["complexidade"] = payload.complexidade
        criterios["complexidade_baixa"] = payload.complexidade in ["simples", "media"]
        
        # Lógica: contratações simples preferem dispensa
        # Complexas preferem adesão (ata já tem requisitos definidos)
        if payload.complexidade == "complexa":
            scores["complexidade_adesao"] = 90
            scores["complexidade_dispensa"] = 30
        elif payload.complexidade == "media":
            scores["complexidade_adesao"] = 70
            scores["complexidade_dispensa"] = 70
        else:  # simples
            scores["complexidade_adesao"] = 50
            scores["complexidade_dispensa"] = 90
        
        # ========== CRITÉRIO 3: URGÊNCIA ==========
        # Urgência favorece dispensa (mais rápido)
        if payload.urgencia:
            scores["urgencia"] = 90
            scores["urgencia_adesao"] = 40
            scores["urgencia_dispensa"] = 90
            criterios["urgencia_indicada"] = True
        else:
            scores["urgencia"] = 50
            scores["urgencia_adesao"] = 70
            scores["urgencia_dispensa"] = 70
            criterios["urgencia_indicada"] = False
        
        # ========== CRITÉRIO 4: ATAS DISPONÍVEIS ==========
        atas_disponiveis = payload.adesao_atas_disponiveis or False
        criterios["atas_disponiveis"] = atas_disponiveis
        
        if atas_disponiveis:
            scores["atas"] = 95  # Adesão é muito viável
            scores["atas_adesao"] = 95
            scores["atas_dispensa"] = 50
        else:
            scores["atas"] = 10  # Sem atas, adesão não é opção
            scores["atas_adesao"] = 10
            scores["atas_dispensa"] = 100
        
        # ========== CÁLCULO DE SCORE FINAL ==========
        
        # Score para ADESÃO A ATA
        if atas_disponiveis:
            score_adesao = (
                scores.get("complexidade_adesao", 50) * 0.25 +
                scores.get("urgencia_adesao", 70) * 0.15 +
                scores.get("atas_adesao", 95) * 0.40 +
                (80 if valor <= LIMITE_ADESAO_RECOMENDADO else 40) * 0.20
            )
        else:
            score_adesao = 0  # Sem atas, adesão não é viável
        
        # Score para DISPENSA POR VALOR BAIXO
        if valor <= LIMITE_DISPENSA_SIMPLES:
            score_dispensa = (
                scores.get("complexidade_dispensa", 70) * 0.25 +
                scores.get("urgencia_dispensa", 70) * 0.15 +
                100 * 0.40 +  # Valor perfeitamente compatível
                100 * 0.20    # Critério legal atendido
            )
        elif valor <= LIMITE_ADESAO_RECOMENDADO:
            score_dispensa = (
                scores.get("complexidade_dispensa", 70) * 0.25 +
                scores.get("urgencia_dispensa", 70) * 0.15 +
                70 * 0.40 +  # Valor acima, menos ideal
                60 * 0.20
            )
        else:
            score_dispensa = 0  # Valor muito alto para dispensa
        
        # Score para LICITAÇÃO NORMAL (fallback quando não atende adesão nem dispensa)
        score_licitacao = 0
        if valor > LIMITE_DISPENSA_SIMPLES and not atas_disponiveis:
            score_licitacao = 80  # Caso padrão
        elif valor > LIMITE_ADESAO_RECOMENDADO:
            score_licitacao = 90  # Valor alto → licitação normal
        
        criterios["score_licitacao"] = score_licitacao
        
        # Decisão final
        if score_adesao >= score_dispensa and score_adesao >= score_licitacao and score_adesao > 0 and atas_disponiveis:
            modalidade_sugerida = "adesao_ata"
            score_final = score_adesao
            justificativa = (
                f"Valor compatível com limite de adesão (R$ {valor:,.2f}). "
                f"Atas de registro disponíveis permitem adesão mais econômica. "
                f"Fluxo: RDVE → JVA → TAFO"
            )
            artefatos_proximos = ["RDVE", "JVA", "TAFO"]
        elif score_dispensa >= score_licitacao and score_dispensa > 0 and valor <= LIMITE_DISPENSA_SIMPLES:
            modalidade_sugerida = "dispensa_valor_baixo"
            score_final = score_dispensa
            justificativa = (
                f"Valor abaixo do limite de dispensa (R$ {valor:,.2f} ≤ R$ {LIMITE_DISPENSA_SIMPLES:,.2f}). "
                f"Dispensa aplicável conforme Lei 14.133/2021, Art. 75. "
                f"Fluxo: TRS → ADE → JPEF → CE"
            )
            artefatos_proximos = ["TRS", "ADE", "JPEF", "CE"]
        else:
            modalidade_sugerida = "licitacao_normal"
            score_final = score_licitacao
            justificativa = (
                f"Valor estimado (R$ {valor:,.2f}) acima do limite de dispensa e sem atas disponíveis para adesão. "
                f"Recomenda-se licitação normal conforme Lei 14.133/2021. "
                f"Fluxo: PP → PGR → TR → Edital → Minuta de Contrato"
            )
            artefatos_proximos = ["PP", "PGR", "TR", "ED", "MC"]
        
        criterios["resultado_score"] = score_final
        criterios["score_adesao"] = score_adesao
        criterios["score_dispensa"] = score_dispensa
        
        return DefinirModalidadeResponse(
            projeto_id=payload.projeto_id,
            etp_id=payload.etp_id,
            modalidade_sugerida=modalidade_sugerida,
            score_analise=score_final,
            criterios_aplicados=criterios,
            justificativa_tecnica=justificativa,
            proximo_fluxo=" → ".join(artefatos_proximos)
        )
    
    except HTTPException:
        raise
    except Exception as e:
        logger.exception(f"Erro ao analisar modalidade: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erro ao analisar modalidade: {str(e)}"
        )


@router.post(
    "/confirmar",
    response_model=ConfirmarModalidadeResponse,
    status_code=status.HTTP_200_OK,
    summary="Confirmar escolha de modalidade",
    tags=["Decisão de Modalidade"]
)
async def confirmar_modalidade(
    payload: ConfirmarModalidadeRequest,
    current_user: User = Depends(auth_get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Confirma a escolha de modalidade feita pelo usuário e atualiza o ETP.
    
    Após confirmação, o sistema irá gerar os artefatos específicos da modalidade:
    - **Adesão a Ata**: RDVE, JVA, TAFO
    - **Dispensa por Valor Baixo**: TRS, ADE, JPEF, CE
    """
    
    try:
        # Validar modalidade
        if payload.modalidade_escolhida not in ["adesao_ata", "dispensa_valor_baixo", "licitacao_normal"]:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Modalidade inválida. Use 'adesao_ata', 'dispensa_valor_baixo' ou 'licitacao_normal'"
            )
        
        # Validar ETP existe
        stmt = select(ETP).where(ETP.id == payload.etp_id)
        etp = await db.scalar(stmt)
        if not etp:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"ETP {payload.etp_id} não encontrada"
            )
        
        # Validar projeto
        stmt_proj = select(Projeto).where(Projeto.id == payload.projeto_id)
        projeto = await db.scalar(stmt_proj)
        if not projeto:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Projeto {payload.projeto_id} não encontrado"
            )
        
        # Atualizar ETP com modalidade definida
        etp.modalidade_definida = payload.modalidade_escolhida
        etp.data_definicao_modalidade = datetime.utcnow()
        if payload.justificativa_usuario:
            etp.justificativa_modalidade = payload.justificativa_usuario
        
        db.add(etp)
        await db.commit()
        await db.refresh(etp)
        
        # Determinar próximos artefatos
        if payload.modalidade_escolhida == "adesao_ata":
            artefatos_proximos = ["RDVE", "JVA", "TAFO"]
            proxima_etapa = "Gerar Relatório de Vantagem Econômica (RDVE) para comprovar vantagem da adesão"
        elif payload.modalidade_escolhida == "dispensa_valor_baixo":
            artefatos_proximos = ["TRS", "ADE", "JPEF", "CE"]
            proxima_etapa = "Gerar Termo de Referência Simplificado (TRS) para dispensa por valor baixo"
        else:
            artefatos_proximos = ["PP", "PGR", "TR", "ED", "MC"]
            proxima_etapa = "Gerar Pesquisa de Preços (PP) e seguir o fluxo de licitação normal"
        
        logger.info(
            f"Modalidade definida: {payload.modalidade_escolhida} para ETP {payload.etp_id} (Projeto {payload.projeto_id})"
        )
        
        return ConfirmarModalidadeResponse(
            sucesso=True,
            projeto_id=payload.projeto_id,
            etp_id=payload.etp_id,
            modalidade_definida=payload.modalidade_escolhida,
            artefatos_proximos=artefatos_proximos,
            proxima_etapa=proxima_etapa
        )
    
    except HTTPException:
        raise
    except Exception as e:
        logger.exception(f"Erro ao confirmar modalidade: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erro ao confirmar modalidade: {str(e)}"
        )


@router.get(
    "/info/{etp_id}",
    response_model=dict,
    status_code=status.HTTP_200_OK,
    summary="Obter informações de modalidade do ETP",
    tags=["Decisão de Modalidade"]
)
async def obter_modalidade_etp(
    etp_id: int,
    current_user: User = Depends(auth_get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Retorna informações sobre a modalidade atual do ETP.
    
    Útil para verificar se já foi definida e qual foi a escolha.
    """
    
    try:
        stmt = select(ETP).where(ETP.id == etp_id)
        etp = await db.scalar(stmt)
        if not etp:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"ETP {etp_id} não encontrada"
            )
        
        return {
            "etp_id": etp.id,
            "modalidade_sugerida": etp.modalidade_sugerida,
            "modalidade_definida": etp.modalidade_definida,
            "data_definicao": etp.data_definicao_modalidade,
            "justificativa": etp.justificativa_modalidade,
            "criterios": etp.criterios_analise_modalidade,
            "pronta_para_decisao": etp.modalidade_sugerida is not None and etp.modalidade_definida is None
        }
    
    except HTTPException:
        raise
    except Exception as e:
        logger.exception(f"Erro ao obter modalidade: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erro ao obter modalidade: {str(e)}"
        )
