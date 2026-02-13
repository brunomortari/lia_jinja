"""
Sistema LIA - Configuração do Banco de Dados
=============================================
Gerencia a conexão, sessão e base dos modelos SQLAlchemy

Autor: Equipe TRE-GO
Data: Janeiro 2026
"""

from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.orm import declarative_base
from typing import AsyncGenerator
from .config import settings

# ========== CONFIGURAÇÃO DO ENGINE ==========

# Converter URL sync para async se necessário
# Ex: postgresql:// -> postgresql+asyncpg://
# Ex: sqlite:// -> sqlite+aiosqlite://
database_url = settings.DATABASE_URL
if database_url.startswith("postgresql://"):
    database_url = database_url.replace("postgresql://", "postgresql+asyncpg://")
elif database_url.startswith("sqlite://") and "aiosqlite" not in database_url:
    database_url = database_url.replace("sqlite://", "sqlite+aiosqlite://")

# Detectar tipo de banco de dados
is_sqlite = "sqlite" in database_url

# Configurações do Engine
connect_args = {}
if is_sqlite:
    connect_args = {"check_same_thread": False}

# Criar Engine Assíncrona
# Configurações de pool apenas para Postgres (SQLite não suporta)
engine_kwargs = {
    "echo": settings.DEBUG,
    "connect_args": connect_args,
}

if not is_sqlite:
    engine_kwargs.update({
        "pool_pre_ping": True,
        "pool_size": 5,
        "max_overflow": 10,
    })

engine = create_async_engine(database_url, **engine_kwargs)


# ========== SESSÃO DO BANCO ==========

# Criar fábrica de sessões assíncronas
AsyncSessionLocal = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autoflush=False
)


# ========== BASE PARA MODELOS ==========

# Classe base para todos os modelos ORM
Base = declarative_base()


# ========== DEPENDÊNCIA DE SESSÃO ==========

async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """
    Cria e fornece uma sessão assíncrona do banco de dados para ser usada nas rotas.
    A sessão é automaticamente fechada após o uso.
    
    Uso em rotas FastAPI:
    ```python
    @app.get("/items")
    async def read_items(db: AsyncSession = Depends(get_db)):
        result = await db.execute(select(Item))
        items = result.scalars().all()
        return items
    ```
    
    Yields:
        AsyncSession: Sessão ativa do banco de dados
    """
    async with AsyncSessionLocal() as session:
        try:
            yield session
        finally:
            await session.close()
