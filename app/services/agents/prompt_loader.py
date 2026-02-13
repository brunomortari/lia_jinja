"""
Prompt Loader - Carrega templates de prompts do banco de dados
"""
from typing import Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.models.prompt_template import PromptTemplate


class PromptLoader:
    """
    Classe para carregar templates de prompts do banco de dados.
    
    Uso:
        async with AsyncSessionLocal() as session:
            loader = PromptLoader(session)
            prompt = await loader.get_prompt("etp", "system")
    """
    
    def __init__(self, session: AsyncSession):
        """
        Args:
            session: Sessão assíncrona do SQLAlchemy
        """
        self.session = session
    
    async def get_prompt(
        self, 
        agent_type: str, 
        prompt_type: str = "system",
        default: Optional[str] = None
    ) -> str:
        """
        Busca um prompt ativo no banco.
        
        Args:
            agent_type: Tipo do agente (ex: "dfd", "etp", "pgr")
            prompt_type: Tipo do prompt ("system", "system_chat", "system_generate")
            default: Valor padrão se não encontrar (opcional)
        
        Returns:
            Conteúdo do prompt ou default se não encontrar
        
        Raises:
            ValueError: Se não encontrar prompt e default não for fornecido
        """
        stmt = select(PromptTemplate).where(
            PromptTemplate.agent_type == agent_type,
            PromptTemplate.prompt_type == prompt_type,
            PromptTemplate.ativa == True
        ).order_by(PromptTemplate.ordem.asc())
        
        result = await self.session.execute(stmt)
        prompt = result.scalar_one_or_none()
        
        if prompt:
            return prompt.conteudo
        
        if default is not None:
            return default
        
        raise ValueError(
            f"Prompt não encontrado: agent_type={agent_type}, "
            f"prompt_type={prompt_type}. Verifique se a tabela foi populada."
        )
    
    async def get_prompts_multiple(
        self, 
        agent_type: str, 
        prompt_types: list[str]
    ) -> dict[str, str]:
        """
        Busca múltiplos prompts de um mesmo agente.
        
        Args:
            agent_type: Tipo do agente
            prompt_types: Lista de tipos de prompt a buscar
        
        Returns:
            Dicionário {prompt_type: conteudo}
        """
        stmt = select(PromptTemplate).where(
            PromptTemplate.agent_type == agent_type,
            PromptTemplate.prompt_type.in_(prompt_types),
            PromptTemplate.ativa == True
        ).order_by(PromptTemplate.prompt_type, PromptTemplate.ordem.asc())
        
        result = await self.session.execute(stmt)
        prompts = result.scalars().all()
        
        return {p.prompt_type: p.conteudo for p in prompts}


# Cache global de prompts (opcional - para evitar queries repetidas)
_PROMPT_CACHE = {}


async def load_prompt_cached(
    session: AsyncSession,
    agent_type: str,
    prompt_type: str = "system",
    use_cache: bool = True
) -> str:
    """
    Versão com cache do carregamento de prompts.
    
    Args:
        session: Sessão do banco
        agent_type: Tipo do agente
        prompt_type: Tipo do prompt
        use_cache: Se deve usar cache (padrão True)
    
    Returns:
        Conteúdo do prompt
    """
    cache_key = f"{agent_type}:{prompt_type}"
    
    if use_cache and cache_key in _PROMPT_CACHE:
        return _PROMPT_CACHE[cache_key]
    
    loader = PromptLoader(session)
    prompt = await loader.get_prompt(agent_type, prompt_type)
    
    if use_cache:
        _PROMPT_CACHE[cache_key] = prompt
    
    return prompt


def clear_prompt_cache():
    """Limpa o cache de prompts. Útil após atualizar prompts no banco."""
    global _PROMPT_CACHE
    _PROMPT_CACHE.clear()
