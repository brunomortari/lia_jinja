"""
Helper functions para renderização de PGR e ETP com contextos de DFD, 
Pesquisas de Preços e Riscos (PGR).
"""
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, or_
from sqlalchemy.orm import selectinload
from app.models.artefatos import DFD, PesquisaPrecos, Riscos


async def buscar_dfds_aprovados(projeto_id: int, db: AsyncSession):
    """
    Busca DFDs aprovados ou publicados para um projeto.
    Prioriza publicados (têm protocolo_sei), senão aprovados.
    Retorna apenas 1 por regra de negócio (só pode ter 1 aprovado).
    """
    # Primeiro busca publicado
    result = await db.execute(
        select(DFD).where(
            and_(
                DFD.projeto_id == projeto_id,
                DFD.protocolo_sei.isnot(None)
            )
        ).order_by(DFD.versao.desc()).limit(1)
    )
    dfd_publicado = result.scalars().first()
    if dfd_publicado:
        return [dfd_publicado]
    
    # Se não tem publicado explicitamente pelo protocolo_sei, busca 'aprovado' ou 'publicado' via status
    result = await db.execute(
        select(DFD).where(
            and_(DFD.projeto_id == projeto_id, DFD.status.in_(['aprovado', 'publicado']))
        ).order_by(DFD.versao.desc()).limit(1)
    )
    dfd_aprovado = result.scalars().first()
    return [dfd_aprovado] if dfd_aprovado else []


async def buscar_cotacoes_projeto(projeto_id: int, db: AsyncSession):
    """
    Busca pesquisas de preços (cotações) aprovadas ou publicadas.
    Retorna todas as publicadas/aprovadas para o projeto.
    """
    result = await db.execute(
        select(PesquisaPrecos).where(
            and_(
                PesquisaPrecos.projeto_id == projeto_id,
                or_(
                    PesquisaPrecos.status.in_(['aprovado', 'concluido', 'publicado']),
                    PesquisaPrecos.protocolo_sei.isnot(None)
                )
            )
        ).order_by(PesquisaPrecos.data_criacao.desc())
    )
    return result.scalars().all()


async def buscar_pgr_aprovado(projeto_id: int, db: AsyncSession):
    """
    Busca PGR (Riscos) aprovado ou publicado para um projeto.
    Prioriza publicado (protocolo_sei), senão aprovado.
    Retorna apenas 1 por regra de negócio.
    Usa selectinload para carregar itens_risco (evita lazy loading em async).
    """
    # Primeiro busca publicado
    result = await db.execute(
        select(Riscos)
        .options(selectinload(Riscos.itens_risco))
        .where(
            and_(
                Riscos.projeto_id == projeto_id,
                Riscos.protocolo_sei.isnot(None)
            )
        ).order_by(Riscos.versao.desc()).limit(1)
    )
    pgr_publicado = result.scalars().first()
    if pgr_publicado:
        return pgr_publicado
    
    # Se não tem publicado via protocolo, busca 'aprovado' ou 'publicado' via status
    result = await db.execute(
        select(Riscos)
        .options(selectinload(Riscos.itens_risco))
        .where(
            and_(Riscos.projeto_id == projeto_id, Riscos.status.in_(['aprovado', 'publicado']))
        ).order_by(Riscos.versao.desc()).limit(1)
    )
    return result.scalars().first()


def serializar_dfd_para_contexto(dfd) -> dict:
    """Serializa DFD para incluir no contexto do PGR/ETP."""
    return {
        "id": dfd.id,
        "numero": getattr(dfd, 'numero_dfd', f"DFD-{dfd.projeto_id:04d}-{dfd.versao:02d}"),
        "versao": dfd.versao,
        "status": dfd.status,
        "publicado": dfd.protocolo_sei is not None,
        "protocolo_sei": dfd.protocolo_sei,
        "descricao_objeto": getattr(dfd, 'descricao_objeto', ''),
        "justificativa": getattr(dfd, 'justificativa', ''),
        "alinhamento_estrategico": getattr(dfd, 'alinhamento_estrategico', ''),
        "valor_estimado": float(getattr(dfd, 'valor_estimado', 0) or 0),
        "setor_requisitante": getattr(dfd, 'setor_requisitante', ''),
    }


def serializar_cotacao_para_contexto(pesquisa_precos) -> dict:
    """Serializa PesquisaPrecos para incluir no contexto do PGR/ETP."""
    return {
        "id": pesquisa_precos.id,
        "status": pesquisa_precos.status,
        "publicado": pesquisa_precos.protocolo_sei is not None,
        "protocolo_sei": pesquisa_precos.protocolo_sei,
        "descricao": getattr(pesquisa_precos, 'item_descricao', ''),
        "valor_total": float(getattr(pesquisa_precos, 'valor_total_cotacao', 0) or 0),
        "quantidade_itens": getattr(pesquisa_precos, 'quantidade_itens_encontrados', 0),
        "preco_medio": float(getattr(pesquisa_precos, 'preco_medio', 0) or 0),
        "preco_minimo": float(getattr(pesquisa_precos, 'preco_minimo', 0) or 0),
        "preco_maximo": float(getattr(pesquisa_precos, 'preco_maximo', 0) or 0),
    }


def serializar_pgr_para_contexto(pgr) -> dict:
    """Serializa Riscos (PGR) para incluir no contexto do ETP."""
    if not pgr:
        return None
    
    # Contar itens de risco se existirem
    qtd_riscos = len(pgr.itens_risco) if pgr.itens_risco else 0
    
    return {
        "id": pgr.id,
        "versao": pgr.versao,
        "status": pgr.status,
        "publicado": pgr.protocolo_sei is not None,
        "protocolo_sei": pgr.protocolo_sei,
        "identificacao_objeto": getattr(pgr, 'identificacao_objeto', ''),
        "valor_estimado_total": float(getattr(pgr, 'valor_estimado_total', 0) or 0),
        "metodologia_adotada": getattr(pgr, 'metodologia_adotada', ''),
        "quantidade_riscos": qtd_riscos,
        "resumo_planejamento": getattr(pgr, 'resumo_analise_planejamento', ''),
        "resumo_selecao": getattr(pgr, 'resumo_analise_selecao', ''),
        "resumo_gestao": getattr(pgr, 'resumo_analise_gestao', ''),
    }


# ========== ETP HELPERS (para TR) ==========

from app.models.artefatos import ETP


async def buscar_etp_aprovado(projeto_id: int, db: AsyncSession):
    """
    Busca ETP aprovado ou publicado para um projeto.
    Prioriza publicado (protocolo_sei), senão aprovado.
    Retorna apenas 1 por regra de negócio.
    """
    # Primeiro busca publicado
    result = await db.execute(
        select(ETP).where(
            and_(
                ETP.projeto_id == projeto_id,
                ETP.protocolo_sei.isnot(None)
            )
        ).order_by(ETP.versao.desc()).limit(1)
    )
    etp_publicado = result.scalars().first()
    if etp_publicado:
        return etp_publicado
    
    # Se não tem publicado via protocolo, busca 'aprovado' ou 'publicado' via status
    result = await db.execute(
        select(ETP).where(
            and_(ETP.projeto_id == projeto_id, ETP.status.in_(['aprovado', 'publicado']))
        ).order_by(ETP.versao.desc()).limit(1)
    )
    return result.scalars().first()


def serializar_etp_para_contexto(etp) -> dict:
    """Serializa ETP para incluir no contexto do TR."""
    if not etp:
        return None
    
    return {
        "id": etp.id,
        "versao": etp.versao,
        "status": etp.status,
        "publicado": etp.protocolo_sei is not None,
        "protocolo_sei": etp.protocolo_sei,
        "descricao_necessidade": getattr(etp, 'descricao_necessidade', ''),
        "requisitos_contratacao": getattr(etp, 'requisitos_contratacao', ''),
        "estimativa_quantidades": getattr(etp, 'estimativa_quantidades', ''),
        "descricao_solucao": getattr(etp, 'descricao_solucao', ''),
        "justificativa_parcelamento": getattr(etp, 'justificativa_parcelamento', ''),
        "viabilidade_contratacao": getattr(etp, 'viabilidade_contratacao', ''),
    }

