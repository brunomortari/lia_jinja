"""
Sistema LIA - Router de Artefatos (ETP, TR, Riscos, Edital, Cotacao)
====================================================================
End-points para geração, edição e gerenciamento de artefatos.
Refatorado para Lean API.

Autor: Equipe TRE-GO
Data: Janeiro 2026
"""

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import HTMLResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from sqlalchemy.orm import selectinload
from datetime import datetime, timezone
import json

from app.database import get_db
from app.models.projeto import Projeto
from app.models.user import User
from app.models.artefatos import ArtefatoBloqueadoError
from app.config import settings
from app.services.pac_service import pac_service
from app.auth import current_active_user as auth_get_current_user

# Import Schemas
from app.schemas.artefatos import (
    SalvarArtefatoRequest,
    AtualizarArtefatoRequest,
    EditarCampoArtefatoRequest
)

# Import schemas de ItemRisco
from app.schemas.ia_schemas import (
    ItemRiscoCreate,
    ItemRiscoUpdate,
    ItemRiscoResponse,
)

# Import Validation Utilities
from app.utils.validation import (
    sanitize_dict,
    MAX_PROMPT_LENGTH,
    MAX_CAMPO_NAME_LENGTH,
)

# Import Services and Logic
from app.services.artefatos_service import (
    ARTEFATO_MAP,
    mapear_campos_artefato
)

# ========== HELPERS ==========

async def _get_projeto(projeto_id: int, db: AsyncSession) -> Projeto:
    """Busca um projeto pelo ID.

    Args:
        projeto_id (int): O ID do projeto.
        db (AsyncSession): Sessão do banco.

    Returns:
        Projeto: O objeto Projeto se encontrado.

    Raises:
        HTTPException: Se o projeto não existir (404).
    """
    result = await db.execute(select(Projeto).filter(Projeto.id == projeto_id))
    projeto = result.scalars().first()
    if not projeto:
        raise HTTPException(status_code=404, detail="Projeto nao encontrado")
    return projeto

async def _get_artefato(model, artefato_id: int, db: AsyncSession):
    """Busca um artefato genérico pelo ID.

    Args:
        model: A classe do modelo SQLAlchemy (ex: ETP, TR).
        artefato_id (int): O ID do artefato.
        db (AsyncSession): Sessão do banco.

    Returns:
        O objeto artefato encontrado.

    Raises:
        HTTPException: Se o artefato não existe (404).
    """
    result = await db.execute(select(model).filter(model.id == artefato_id))
    artefato = result.scalars().first()
    if not artefato:
        raise HTTPException(status_code=404, detail="Artefato nao encontrado")
    return artefato


async def _tem_versao_publicada(model, projeto_id: int, db: AsyncSession) -> bool:
    """Verifica se já existe uma versão publicada (SEI) do artefato no projeto.

    Args:
        model: A classe do modelo SQLAlchemy (ex: ETP, TR).
        projeto_id (int): O ID do projeto.
        db (AsyncSession): Sessão do banco.

    Returns:
        bool: True se já existe versão publicada.
    """
    result = await db.execute(
        select(model).filter(
            model.projeto_id == projeto_id,
            model.protocolo_sei.isnot(None)
        )
    )
    return result.scalars().first() is not None

# ========== FACTORY DE ROUTERS ==========

def criar_router_artefato(tipo: str):
    """Cria um APIRouter padronizado para um tipo de artefato.

    Gera endpoints de CRUD (Salvar, Obter, Atualizar, Deletar) e operações
    específicas (Editar Campo, Regenerar IA, Criar Versão, Aprovar) dinamicamente.

    Args:
        tipo (str): O identificador do tipo de artefato (ex: 'etp', 'tr').

    Returns:
        APIRouter: O router configurado com todos os endpoints.
    """

    config_map = ARTEFATO_MAP[tipo]
    Model = config_map["model"]
    campos_config = config_map["config"]

    router = APIRouter()

    @router.post("/salvar", summary=f"Salvar {config_map['titulo']}")
    async def salvar_artefato(
        request: SalvarArtefatoRequest,
        db: AsyncSession = Depends(get_db),
        current_user: User = Depends(auth_get_current_user)
    ):
        """Salva artefato gerado pela IA (Rascunho)"""
        projeto = await _get_projeto(request.projeto_id, db)

        # Contar versão
        result = await db.execute(select(func.count()).filter(Model.projeto_id == request.projeto_id))
        count = result.scalar() or 0
        proxima_versao = count + 1

        # Mapear e preparar dados
        content = request.artefato_data.get('content_blocks', request.artefato_data)
        audit = request.artefato_data.get('audit_metadata', {})

        model_data = mapear_campos_artefato(tipo, content)
        model_data.update({
            "projeto_id": request.projeto_id,
            "versao": proxima_versao,
            "status": "rascunho"
        })

        artefato = Model(**model_data)
        artefato.registrar_geracao_ia(prompt=request.prompt_adicional, metadata=audit)
        db.add(artefato)
        await db.commit()
        await db.refresh(artefato)

        return {
            "message": f"{config_map['titulo']} salvo com sucesso",
            f"{tipo}_id": artefato.id,
            "versao": artefato.versao
        }

    @router.get("/{artefato_id}", summary=f"Obter {config_map['titulo']}")
    async def obter_artefato(
        artefato_id: int,
        db: AsyncSession = Depends(get_db),
        current_user: User = Depends(auth_get_current_user)
    ):
        """Retorna os dados completos do artefato e histórico de versões"""
        artefato = await _get_artefato(Model, artefato_id, db)

        # Histórico
        result = await db.execute(select(Model).filter(Model.projeto_id == artefato.projeto_id).order_by(Model.versao.desc()))
        todas_versoes = result.scalars().all()

        return {
            "artefato": artefato.to_dict(),
            "campos_config": campos_config,
            "versoes": [
                {"versao": v.versao, "data": v.data_criacao.isoformat() if v.data_criacao else None, "id": v.id}
                for v in todas_versoes
            ]
        }

    @router.put("/{artefato_id}", summary=f"Atualizar {config_map['titulo']}")
    async def atualizar_artefato_completo(
        artefato_id: int,
        request: AtualizarArtefatoRequest,
        db: AsyncSession = Depends(get_db),
        current_user: User = Depends(auth_get_current_user)
    ):
        """Atualiza artefato (Edição ou Aprovação).
        
        Regras de negócio:
        - Rascunho: pode editar
        - Aprovado: pode editar
        - Publicado (SEI): NÃO pode editar
        """
        artefato = await _get_artefato(Model, artefato_id, db)

        # Validar se pode editar (bloqueia se publicado no SEI)
        artefato.validar_edicao()

        # Update dinâmico usando campos extras do Pydantic
        update_data = request.model_dump(exclude_unset=True)
        
        for field, value in update_data.items():
            if hasattr(artefato, field):
                setattr(artefato, field, value)
        
        artefato.data_atualizacao = datetime.now(timezone.utc)
        
        # Se está aprovando, verificar se já existe outro aprovado
        if update_data.get("status") == "aprovado" and artefato.status != "aprovado":
            if await Model.tem_versao_aprovada(artefato.projeto_id, db, excluir_id=artefato.id):
                raise HTTPException(
                    status_code=400, 
                    detail="Já existe uma versão aprovada deste artefato."
                )
            artefato.data_aprovacao = datetime.now(timezone.utc)

        await db.commit()
        await db.refresh(artefato)

        return {
            "message": f"{config_map['titulo']} atualizado com sucesso!",
            "artefato": artefato.to_dict()
        }

    @router.post("/editar-campo", summary="Editar Campo Único")
    async def editar_campo(
        request: EditarCampoArtefatoRequest,
        db: AsyncSession = Depends(get_db),
        current_user: User = Depends(auth_get_current_user)
    ):
        """Edita um único campo do artefato"""
        artefato = await _get_artefato(Model, request.artefato_id, db)

        if request.campo not in campos_config:
            raise HTTPException(status_code=400, detail=f"Campo '{request.campo}' não existe")

        artefato.validar_edicao()

        setattr(artefato, request.campo, request.valor)
        artefato.registrar_edicao_campo(request.campo)

        await db.commit()
        return {
            "message": f"Campo '{request.campo}' atualizado",
            "campo": request.campo,
            "valor": getattr(artefato, request.campo)
        }

    # NOTE: Endpoint regenerar-campo-ia foi removido (dependia de n8n)
    # TODO: Reimplementar usando ia_native quando necessário

    @router.post("/{artefato_id}/nova-versao", summary="Criar Nova Versão")
    async def criar_nova_versao(
        artefato_id: int,
        db: AsyncSession = Depends(get_db),
        current_user: User = Depends(auth_get_current_user)
    ):
        """Duplica artefato existente criando uma nova versão rascunho.
        
        Regra de negócio: Não pode criar nova versão se já existe uma aprovada.
        """
        artefato = await _get_artefato(Model, artefato_id, db)

        artefato.validar_edicao()

        # Verificar se já existe versão aprovada (bloqueia novas versões)
        if await Model.tem_versao_aprovada(artefato.projeto_id, db):
            raise HTTPException(
                status_code=400, 
                detail="Já existe uma versão aprovada deste artefato. Não é possível criar novas versões."
            )

        # Próxima versão
        nova_versao_num = await Model.proxima_versao(artefato.projeto_id, db)
        novo_artefato = artefato.clonar_para_nova_versao(nova_versao_num)
        
        db.add(novo_artefato)
        await db.commit()
        await db.refresh(novo_artefato)

        return {
            "message": "Nova versão criada",
            "versao_anterior": artefato.versao,
            "versao_atual": novo_artefato.versao,
            "id": novo_artefato.id
        }

    @router.post("/{artefato_id}/aprovar", summary="Aprovar Artefato")
    async def aprovar_artefato(
        artefato_id: int,
        db: AsyncSession = Depends(get_db),
        current_user: User = Depends(auth_get_current_user)
    ):
        """Marca o artefato como aprovado.
        
        Regras de negócio:
        - Só pode ter uma versão aprovada por tipo de artefato no projeto
        - Artefato publicado no SEI não pode ser aprovado novamente
        - Artefato já aprovado retorna mensagem informativa
        """
        artefato = await _get_artefato(Model, artefato_id, db)
        
        # Verificar se já está publicado
        artefato.validar_edicao()
        
        # Verificar se já está aprovado
        if artefato.esta_aprovado:
            return {"message": "Artefato já está aprovado", "status": "aprovado"}
        
        # Verificar se já existe OUTRA versão aprovada
        if await Model.tem_versao_aprovada(artefato.projeto_id, db, excluir_id=artefato.id):
            raise HTTPException(
                status_code=400, 
                detail="Já existe uma versão aprovada deste artefato. Apenas uma versão pode ser aprovada."
            )
        
        artefato.aprovar()
        await db.commit()
        return {"message": "Artefato aprovado", "status": "aprovado"}

    @router.delete("/{artefato_id}", summary="Deletar Artefato")
    async def deletar_artefato(
        artefato_id: int,
        db: AsyncSession = Depends(get_db),
        current_user: User = Depends(auth_get_current_user)
    ):
        """Remove permanentemente o artefato.
        
        Regra de negócio: Artefato publicado no SEI não pode ser excluído.
        """
        artefato = await _get_artefato(Model, artefato_id, db)
        
        artefato.validar_edicao()
        
        await db.delete(artefato)
        await db.commit()
        return {"message": "Artefato removido permanentemente"}

    @router.get("/{artefato_id}/pdf", response_class=HTMLResponse, summary="Gerar PDF (HTML)")
    async def gerar_pdf_artefato(
        artefato_id: int,
        db: AsyncSession = Depends(get_db),
        current_user: User = Depends(auth_get_current_user)
    ):
        """Gera view de impressão"""
        result = await db.execute(select(Model).filter(Model.id == artefato_id).options(selectinload(Model.projeto)))
        artefato = result.scalars().first()
        if not artefato:
            raise HTTPException(status_code=404, detail="Artefato nao encontrado")

        # HTML generation logic is kept here for now as it's presentation, but could be moved to templates
        # Using a simple string interpolation for now to match previous logic
        # Ideally this should use Jinja2 templates, but refactoring that now might be too risky given the strict prompt to "refactor backend" first.
        # I will keep the string logic but clean it up slightly.
        
        projeto = artefato.projeto
        campos_html = ""
        for campo_nome, campo_cfg in campos_config.items():
            valor = getattr(artefato, campo_nome, None)
            if valor:
                if isinstance(valor, (dict, list)):
                    valor = json.dumps(valor, ensure_ascii=False, indent=2)
                campos_html += f'''
                <div class="campo">
                    <h3>{campo_cfg.get('label', campo_nome)}</h3>
                    <div class="valor">{valor}</div>
                </div>
                '''

        html_content = f"""
        <!DOCTYPE html>
        <html lang="pt-BR">
        <head>
            <meta charset="UTF-8">
            <title>{config_map['titulo']} - {projeto.titulo if projeto else 'Projeto'}</title>
            <style>
                body {{ font-family: 'Segoe UI', sans-serif; max-width: 800px; margin: 0 auto; padding: 40px; color: #333; }}
                h1 {{ color: #2C7A7B; border-bottom: 2px solid #2C7A7B; padding-bottom: 10px; }}
                .meta {{ background: #f7fafc; padding: 15px; border-radius: 8px; margin-bottom: 30px; }}
                .campo {{ margin-bottom: 25px; page-break-inside: avoid; }}
                .campo h3 {{ color: #2C7A7B; margin-bottom: 5px; }}
                .campo .valor {{ background: #f9f9f9; padding: 15px; border-left: 3px solid #2C7A7B; white-space: pre-wrap; }}
                @media print {{ .no-print {{ display: none; }} body {{ padding: 0; }} }}
            </style>
        </head>
        <body>
            <h1>{config_map['titulo']}</h1>
            <div class="meta">
                <strong>Projeto:</strong> {projeto.titulo if projeto else 'N/A'} <br>
                <strong>Versão:</strong> {artefato.versao} | <strong>Status:</strong> {artefato.status}
            </div>
            {campos_html}
            <div class="no-print" style="text-align: center; margin-top: 40px;">
                <button onclick="window.print()" style="padding: 10px 20px; background: #2C7A7B; color: white; border: none; cursor: pointer;">Imprimir / Salvar PDF</button>
            </div>
        </body>
        </html>
        """
        return HTMLResponse(content=html_content)

    return router


# ========== DEFINIÇÃO DOS ROUTERS ==========

dfd_router = criar_router_artefato("dfd")
etp_router = criar_router_artefato("etp")
tr_router = criar_router_artefato("tr")
riscos_router = criar_router_artefato("riscos")
edital_router = criar_router_artefato("edital")
pesquisa_precos_router = criar_router_artefato("pesquisa_precos")

# ========== NOVOS ROUTERS: FLUXO DE LICITAÇÃO E CONTRATAÇÃO DIRETA ==========
checklist_conformidade_router = criar_router_artefato("checklist_conformidade")
minuta_contrato_router = criar_router_artefato("minuta_contrato")
aviso_publicidade_direta_router = criar_router_artefato("aviso_publicidade_direta")
justificativa_fornecedor_escolhido_router = criar_router_artefato("justificativa_fornecedor_escolhido")

# ========== NOVOS ROUTERS: FLUXO DE ADESÃO A ATA ==========
rdve_router = criar_router_artefato("rdve")
jva_router = criar_router_artefato("jva")
tafo_router = criar_router_artefato("tafo")

# ========== NOVOS ROUTERS: FLUXO DE DISPENSA POR VALOR BAIXO ==========
trs_router = criar_router_artefato("trs")
ade_router = criar_router_artefato("ade")
jpef_router = criar_router_artefato("jpef")
ce_router = criar_router_artefato("ce")


# ========== ENDPOINTS CRUD DE ITEMRISCO ==========
# (Movidos de ia_pgr.py - não dependem de n8n, são CRUD puro)

from app.models.artefatos import Riscos, ItemRisco

item_risco_router = APIRouter()


@item_risco_router.post("/pgr/{pgr_id}/itens-risco")
async def criar_item_risco(
    pgr_id: int,
    payload: ItemRiscoCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(auth_get_current_user)
):
    """
    Cria um novo ItemRisco dentro de um PGR.
    
    Valida:
    - Probabilidade (1-5)
    - Impacto (1-5)
    - Calcula automaticamente nível_risco (probabilidade × impacto)
    - Alocação de responsabilidade (Lei 14.133/21)
    """
    # Validar que PGR existe
    result = await db.execute(
        select(Riscos).filter(Riscos.id == pgr_id)
    )
    pgr = result.scalars().first()
    if not pgr:
        raise HTTPException(status_code=404, detail="PGR não encontrado")

    # Calcular nível de risco (1-5 × 1-5 = 1-25)
    nivel_risco = payload.probabilidade * payload.impacto

    # Criar ItemRisco
    item_risco = ItemRisco(
        pgr_id=pgr_id,
        origem=payload.origem,
        fase_licitacao=payload.fase_licitacao,
        categoria=payload.categoria,
        evento=payload.evento,
        causa=payload.causa,
        consequencia=payload.consequencia,
        probabilidade=payload.probabilidade,
        impacto=payload.impacto,
        nivel_risco=nivel_risco,
        justificativa_probabilidade=payload.justificativa_probabilidade,
        justificativa_impacto=payload.justificativa_impacto,
        tipo_tratamento=payload.tipo_tratamento,
        acoes_preventivas=payload.acoes_preventivas,
        acoes_contingencia=payload.acoes_contingencia,
        alocacao_responsavel=payload.alocacao_responsavel,
        gatilho_monitoramento=payload.gatilho_monitoramento,
        responsavel_monitoramento=payload.responsavel_monitoramento,
        frequencia_monitoramento=payload.frequencia_monitoramento,
        status_risco="Identificado",
        notas=payload.notas,
    )

    db.add(item_risco)
    await db.commit()
    await db.refresh(item_risco)

    return ItemRiscoResponse.from_orm(item_risco)


@item_risco_router.get("/pgr/{pgr_id}/itens-risco")
async def listar_itens_risco(
    pgr_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(auth_get_current_user)
):
    """
    Lista todos os itens de risco de um PGR.
    """
    result = await db.execute(
        select(ItemRisco).filter(ItemRisco.pgr_id == pgr_id).order_by(ItemRisco.id)
    )
    itens = result.scalars().all()

    return [ItemRiscoResponse.from_orm(item) for item in itens]


@item_risco_router.get("/pgr/{pgr_id}/itens-risco/{item_id}")
async def obter_item_risco(
    pgr_id: int,
    item_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(auth_get_current_user)
):
    """
    Obtém um item de risco específico.
    """
    result = await db.execute(
        select(ItemRisco).filter(
            ItemRisco.pgr_id == pgr_id,
            ItemRisco.id == item_id
        )
    )
    item = result.scalars().first()

    if not item:
        raise HTTPException(status_code=404, detail="Item de risco não encontrado")

    return ItemRiscoResponse.from_orm(item)


@item_risco_router.patch("/pgr/{pgr_id}/itens-risco/{item_id}")
async def atualizar_item_risco(
    pgr_id: int,
    item_id: int,
    payload: ItemRiscoUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(auth_get_current_user)
):
    """
    Atualiza um item de risco (PATCH - campos parciais).
    
    Recalcula nível_risco se probabilidade ou impacto forem atualizados.
    """
    result = await db.execute(
        select(ItemRisco).filter(
            ItemRisco.pgr_id == pgr_id,
            ItemRisco.id == item_id
        )
    )
    item = result.scalars().first()

    if not item:
        raise HTTPException(status_code=404, detail="Item de risco não encontrado")

    # Atualizar campos fornecidos
    update_data = payload.dict(exclude_unset=True)
    
    for key, value in update_data.items():
        setattr(item, key, value)

    # Recalcular nível se probabilidade ou impacto mudaram
    if 'probabilidade' in update_data or 'impacto' in update_data:
        item.nivel_risco = item.probabilidade * item.impacto

    await db.commit()
    await db.refresh(item)

    return ItemRiscoResponse.from_orm(item)


@item_risco_router.delete("/pgr/{pgr_id}/itens-risco/{item_id}")
async def deletar_item_risco(
    pgr_id: int,
    item_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(auth_get_current_user)
):
    """
    Deleta um item de risco.
    """
    result = await db.execute(
        select(ItemRisco).filter(
            ItemRisco.pgr_id == pgr_id,
            ItemRisco.id == item_id
        )
    )
    item = result.scalars().first()

    if not item:
        raise HTTPException(status_code=404, detail="Item de risco não encontrado")

    await db.delete(item)
    await db.commit()

    return {"success": True, "message": "Item de risco deletado"}
