"""
Sistema LIA - Router de Projetos
=================================
Endpoints para CRUD de projetos de contratação

Autor: Equipe TRE-GO
Data: Janeiro 2026
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload
from typing import List, Optional
from datetime import datetime, timezone
from pydantic import BaseModel, Field
from app.database import get_db
from app.models.projeto import Projeto
from app.models.user import User
from app.auth import current_active_user as get_current_user
from app.config import ProjetoStatus

# ========== SCHEMAS ==========

class ItemPacProjeto(BaseModel):
    """Schema para item PAC vinculado ao projeto com quantidade específica"""
    id: int
    quantidade: Optional[float] = None  # Quantidade específica para este projeto (None = usa quantidade do PAC)

class ProjetoCreate(BaseModel):
    """Schema para criação de projeto"""
    titulo: str = Field(..., max_length=300)
    descricao: Optional[str] = None
    prompt_inicial: str
    itens_pac: List[ItemPacProjeto]  # Agora aceita objetos com id e quantidade
    intra_pac: Optional[bool] = True  # True = intra-PAC, False = extra-PAC (default True)

class ProjetoUpdate(BaseModel):
    """Schema para atualização de projeto"""
    titulo: Optional[str] = Field(None, max_length=300)
    descricao: Optional[str] = None
    status: Optional[str] = None
    intra_pac: Optional[bool] = None  # Permite atualizar se é intra ou extra PAC

class ProjetoResponse(BaseModel):
    """Schema de resposta de projeto com todos os 18 artefatos"""
    id: int
    titulo: str
    descricao: Optional[str]
    usuario_id: int
    prompt_inicial: Optional[str]
    itens_pac: Optional[List]
    intra_pac: bool = True  # True = intra-PAC, False = extra-PAC
    status: str
    data_criacao: datetime
    data_atualizacao: datetime
    
    # Fluxo Principal (7 artefatos)
    tem_dfd: bool = False
    tem_etp: bool = False
    tem_pp: bool = False
    tem_pgr: bool = False
    tem_tr: bool = False
    tem_edital: bool = False
    tem_pd: bool = False
    
    # Adesão a Ata (3 artefatos)
    tem_rdve: bool = False
    tem_jva: bool = False
    tem_tafo: bool = False
    
    # Dispensa Valor Baixo (4 artefatos)
    tem_trs: bool = False
    tem_ade: bool = False
    tem_jpef: bool = False
    tem_ce: bool = False
    
    # Licitação Normal (2 artefatos)
    tem_chk: bool = False
    tem_mc: bool = False
    
    # Contratação Direta (2 artefatos)
    tem_apd: bool = False
    tem_jfe: bool = False
    
    class Config:
        from_attributes = True

# ========== ROUTER ==========

router = APIRouter()

# ========== ENDPOINTS ==========

@router.get("", response_model=List[ProjetoResponse])
async def listar_projetos(
    status: Optional[str] = None,
    limit: int = 50,
    offset: int = 0,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Lista projetos do usuário autenticado"""
    query = select(Projeto).filter(Projeto.usuario_id == current_user.id)

    if status:
        query = query.filter(Projeto.status == status)

    # Carregar relacionamentos necessários para as propriedades tem_*
    query = query.options(
        selectinload(Projeto.dfds),
        selectinload(Projeto.riscos),
        selectinload(Projeto.pesquisas_precos),
        selectinload(Projeto.etps),
        selectinload(Projeto.trs),
        selectinload(Projeto.editais)
    )

    query = query.order_by(Projeto.data_criacao.desc()).offset(offset).limit(limit)
    
    result = await db.execute(query)
    projetos = result.scalars().all()

    # Construir lista de respostas com flags de artefatos
    # Agora que usamos selectinload, as propriedades como p.tem_dfd funcionarão
    result_list = []
    for p in projetos:
        result_list.append(ProjetoResponse(
            id=p.id,
            titulo=p.titulo,
            descricao=p.descricao,
            usuario_id=p.usuario_id,
            prompt_inicial=p.prompt_inicial,
            itens_pac=p.itens_pac,
            intra_pac=bool(p.intra_pac),  # Converter 1/0 para True/False
            status=p.status,
            data_criacao=p.data_criacao,
            data_atualizacao=p.data_atualizacao,
            tem_dfd=p.tem_dfd,
            tem_pgr=p.tem_pgr,
            tem_pp=p.tem_pp,
            tem_etp=p.tem_etp,
            tem_tr=p.tem_tr,
            tem_edital=p.tem_edital
        ))

    return result_list

@router.post("", response_model=ProjetoResponse, status_code=status.HTTP_201_CREATED)
async def criar_projeto(
    projeto_data: ProjetoCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Cria um novo projeto de contratação"""
    # Converter itens_pac para formato JSON (lista de dicts)
    itens_pac_json = [item.model_dump() for item in projeto_data.itens_pac]
    
    # Determinar se é intra-PAC ou extra-PAC
    # Se houver itens_pac preenchidos, é intra-PAC (True). Caso contrário, usa o valor fornecido
    intra_pac = bool(itens_pac_json) if projeto_data.intra_pac is None else projeto_data.intra_pac

    novo_projeto = Projeto(
        titulo=projeto_data.titulo,
        descricao=projeto_data.descricao,
        usuario_id=current_user.id,
        prompt_inicial=projeto_data.prompt_inicial,
        itens_pac=itens_pac_json,  # Agora armazena [{"id": 8, "quantidade": 100}, ...]
        intra_pac=1 if intra_pac else 0,  # Armazena como 1 (True) ou 0 (False)
        status=ProjetoStatus.RASCUNHO,
        data_criacao=datetime.now(timezone.utc),
        data_atualizacao=datetime.now(timezone.utc)
    )
    
    db.add(novo_projeto)
    await db.commit()
    await db.refresh(novo_projeto)
    
    # É um projeto novo, então não tem artefatos. Não precisamos de eager loading aqui
    # pois as listas de relação estarão vazias ou não inicializadas, mas as propriedades
    # devem tratar isso (len(self.dfds) vai falhar se não estiver carregado).
    # O ideal é recarregar com opções ou inicializar listas vazias.
    # Vamos fazer um refresh com loading para garantir.
    
    query = select(Projeto).where(Projeto.id == novo_projeto.id).options(
        selectinload(Projeto.dfds),
        selectinload(Projeto.riscos),
        selectinload(Projeto.pesquisas_precos),
        selectinload(Projeto.etps),
        selectinload(Projeto.trs),
        selectinload(Projeto.editais)
    )
    result = await db.execute(query)
    novo_projeto = result.scalars().first()
    
    return novo_projeto

@router.get("/{projeto_id}", response_model=ProjetoResponse)
async def obter_projeto(
    projeto_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Obtém detalhes de um projeto específico"""
    query = select(Projeto).filter(
        Projeto.id == projeto_id,
        Projeto.usuario_id == current_user.id
    ).options(
        selectinload(Projeto.dfds),
        selectinload(Projeto.riscos),
        selectinload(Projeto.pesquisas_precos),
        selectinload(Projeto.etps),
        selectinload(Projeto.trs),
        selectinload(Projeto.editais)
    )
    
    result = await db.execute(query)
    projeto = result.scalars().first()

    if not projeto:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Projeto não encontrado"
        )

    # Retornar resposta com flags de artefatos usando as propriedades do modelo
    return ProjetoResponse(
        id=projeto.id,
        titulo=projeto.titulo,
        descricao=projeto.descricao,
        usuario_id=projeto.usuario_id,
        prompt_inicial=projeto.prompt_inicial,
        itens_pac=projeto.itens_pac,
        intra_pac=bool(projeto.intra_pac),  # Converter 1/0 para True/False
        status=projeto.status,
        data_criacao=projeto.data_criacao,
        data_atualizacao=projeto.data_atualizacao,
        # Fluxo Principal
        tem_dfd=projeto.tem_dfd,
        tem_etp=projeto.tem_etp,
        tem_pp=projeto.tem_pp,
        tem_pgr=projeto.tem_pgr,
        tem_tr=projeto.tem_tr,
        tem_edital=projeto.tem_edital,
        tem_pd=projeto.tem_pd,
        # Adesão a Ata
        tem_rdve=projeto.tem_rdve,
        tem_jva=projeto.tem_jva,
        tem_tafo=projeto.tem_tafo,
        # Dispensa Valor Baixo
        tem_trs=projeto.tem_trs,
        tem_ade=projeto.tem_ade,
        tem_jpef=projeto.tem_jpef,
        tem_ce=projeto.tem_ce,
        # Licitação Normal
        tem_chk=projeto.tem_chk,
        tem_mc=projeto.tem_mc,
        # Contratação Direta
        tem_apd=projeto.tem_apd,
        tem_jfe=projeto.tem_jfe
    )

@router.put("/{projeto_id}", response_model=ProjetoResponse)
async def atualizar_projeto(
    projeto_id: int,
    projeto_data: ProjetoUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Atualiza um projeto existente"""
    # Precisamos carregar opções também aqui para o retorno
    query = select(Projeto).filter(
        Projeto.id == projeto_id,
        Projeto.usuario_id == current_user.id
    ).options(
        selectinload(Projeto.dfds),
        selectinload(Projeto.riscos),
        selectinload(Projeto.pesquisas_precos),
        selectinload(Projeto.etps),
        selectinload(Projeto.trs),
        selectinload(Projeto.editais)
    )
    
    result = await db.execute(query)
    projeto = result.scalars().first()
    
    if not projeto:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Projeto não encontrado"
        )
    
    # Atualizar campos fornecidos
    if projeto_data.titulo is not None:
        projeto.titulo = projeto_data.titulo
    if projeto_data.descricao is not None:
        projeto.descricao = projeto_data.descricao
    if projeto_data.status is not None:
        projeto.status = projeto_data.status
    if projeto_data.intra_pac is not None:
        projeto.intra_pac = 1 if projeto_data.intra_pac else 0  # Armazena como 1 (True) ou 0 (False)
    
    projeto.data_atualizacao = datetime.now(timezone.utc)
    
    await db.commit()
    await db.refresh(projeto)
    
    return projeto

@router.delete("/{projeto_id}")
async def excluir_projeto(
    projeto_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Exclui um projeto"""
    result = await db.execute(select(Projeto).filter(
        Projeto.id == projeto_id,
        Projeto.usuario_id == current_user.id
    ))
    projeto = result.scalars().first()
    
    if not projeto:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Projeto não encontrado"
        )
    
    await db.delete(projeto)
    await db.commit()
    
    return {"message": "Projeto excluído com sucesso", "id": projeto_id}
