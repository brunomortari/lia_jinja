"""
Sistema LIA - Router de Skills (Habilidades)
=============================================
CRUD de skills do usuario e listagem de skills do sistema.

Autor: Equipe TRE-GO
Data: Fevereiro 2026
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, or_
from typing import List, Optional

from app.database import get_db
from app.models.skill import Skill
from app.models.user import User
from app.auth import current_active_user as get_current_user
from app.schemas.skills import SkillCreate, SkillUpdate, SkillResponse

router = APIRouter()


@router.get("", response_model=List[SkillResponse])
async def listar_skills(
    incluir_sistema: bool = True,
    tipo_artefato: Optional[str] = None,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Lista skills do sistema e/ou do usuario autenticado."""
    conditions = []

    if incluir_sistema:
        # Skills do sistema + skills do usuario
        conditions.append(Skill.escopo == "system")

    # Sempre incluir skills do proprio usuario
    conditions.append(Skill.usuario_id == current_user.id)

    query = select(Skill).filter(or_(*conditions))

    # Filtro por tipo de artefato removido
    # if tipo_artefato: ...

    query = query.order_by(Skill.escopo.desc(), Skill.nome)
    result = await db.execute(query)
    return result.scalars().all()


@router.post("", response_model=SkillResponse, status_code=status.HTTP_201_CREATED)
async def criar_skill(
    skill_data: SkillCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Cria uma nova skill do usuario."""
    nova_skill = Skill(
        nome=skill_data.nome,
        descricao=skill_data.descricao,
        instrucoes=skill_data.instrucoes,
        tools=skill_data.tools,
        textos_base=skill_data.textos_base,
        escopo="user",
        usuario_id=current_user.id,
    )
    db.add(nova_skill)
    await db.commit()
    await db.refresh(nova_skill)
    return nova_skill


@router.get("/{skill_id}", response_model=SkillResponse)
async def obter_skill(
    skill_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Obtem detalhes de uma skill."""
    result = await db.execute(select(Skill).filter(Skill.id == skill_id))
    skill = result.scalars().first()

    if not skill:
        raise HTTPException(status_code=404, detail="Skill nao encontrada")

    # Verificar acesso: system = publico, user = apenas dono
    if skill.escopo == "user" and skill.usuario_id != current_user.id:
        raise HTTPException(status_code=403, detail="Sem permissao para acessar esta skill")

    return skill


@router.put("/{skill_id}", response_model=SkillResponse)
async def atualizar_skill(
    skill_id: int,
    skill_data: SkillUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Atualiza uma skill do usuario. Skills do sistema nao podem ser editadas."""
    result = await db.execute(select(Skill).filter(Skill.id == skill_id))
    skill = result.scalars().first()

    if not skill:
        raise HTTPException(status_code=404, detail="Skill nao encontrada")

    if skill.escopo == "system":
        raise HTTPException(status_code=403, detail="Skills do sistema nao podem ser editadas")

    if skill.usuario_id != current_user.id:
        raise HTTPException(status_code=403, detail="Sem permissao para editar esta skill")

    # Atualizar campos fornecidos
    update_data = skill_data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(skill, field, value)

    await db.commit()
    await db.refresh(skill)
    return skill


@router.delete("/{skill_id}", status_code=status.HTTP_204_NO_CONTENT)
async def excluir_skill(
    skill_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Exclui uma skill do usuario. Skills do sistema nao podem ser excluidas."""
    result = await db.execute(select(Skill).filter(Skill.id == skill_id))
    skill = result.scalars().first()

    if not skill:
        raise HTTPException(status_code=404, detail="Skill nao encontrada")

    if skill.escopo == "system":
        raise HTTPException(status_code=403, detail="Skills do sistema nao podem ser excluidas")

    if skill.usuario_id != current_user.id:
        raise HTTPException(status_code=403, detail="Sem permissao para excluir esta skill")

    await db.delete(skill)
    await db.commit()
