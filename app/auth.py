"""
Sistema LIA - Auth SIMPLIFICADO com FastAPI-Users
==================================================
Todo o sistema de auth em ~50 linhas!

Autor: Equipe TRE-GO
Data: Janeiro 2026
"""

from typing import Optional
from fastapi import Depends, Request
from fastapi_users import FastAPIUsers, BaseUserManager, IntegerIDMixin
from fastapi_users.authentication import (
    AuthenticationBackend,
    CookieTransport,
    BearerTransport,
    JWTStrategy,
)
from fastapi_users.db import SQLAlchemyUserDatabase
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.user import User
from app.config import settings
from app.database import AsyncSessionLocal


# ========== ASYNC SESSION (necessário para fastapi-users) ==========

async def get_async_session():
    """Provedor de sessão assíncrona"""
    async with AsyncSessionLocal() as session:
        yield session


# ========== USER MANAGER ==========

class UserManager(IntegerIDMixin, BaseUserManager[User, int]):
    """Gerenciador de usuários customizado"""
    reset_password_token_secret = settings.SECRET_KEY
    verification_token_secret = settings.SECRET_KEY

    async def on_after_register(self, user: User, request: Optional[Request] = None):
        print(f"✅ Usuário {user.email} registrado!")

    async def on_after_forgot_password(
        self, user: User, token: str, request: Optional[Request] = None
    ):
        print(f"🔑 Reset de senha solicitado para {user.email}")



async def get_user_db(session: AsyncSession = Depends(get_async_session)):
    """Retorna o database adapter"""
    yield SQLAlchemyUserDatabase(session, User)


async def get_user_manager(user_db=Depends(get_user_db)):
    """Retorna o user manager"""
    yield UserManager(user_db)


# ========== AUTH BACKEND ==========

# Configurar para usar o mesmo nome de cookie que o views.py usa atualmente ("session_token"),
# ou mudar views.py para usar o padrão ("fastapiusersauth").
# Vamos usar o padrão do views.py para evitar quebrar clientes existentes agora?
# Não, o padrão é "fastapiusersauth" no framework. O views.py fez manual "session_token".
# Melhor padronizar para "session_token" se quisermos manter compatibilidade, 
# mas "fastapiusersauth" é mais claro que é do framework.
# Vamos mudar para "lia_session" para ser específico do app.
COOKIE_NAME = "lia_session"

cookie_transport = CookieTransport(
    cookie_name=COOKIE_NAME,
    cookie_max_age=3600 * 24 * 30  # 30 dias
)

bearer_transport = BearerTransport(tokenUrl="auth/jwt/login")

def get_jwt_strategy() -> JWTStrategy:
    return JWTStrategy(secret=settings.SECRET_KEY, lifetime_seconds=3600 * 24 * 30)


auth_backend = AuthenticationBackend(
    name="jwt",
    transport=cookie_transport,
    get_strategy=get_jwt_strategy,
)

auth_backend_bearer = AuthenticationBackend(
    name="jwt-bearer",
    transport=bearer_transport,
    get_strategy=get_jwt_strategy,
)


# ========== FASTAPI USERS INSTANCE ==========

fastapi_users = FastAPIUsers[User, int](
    get_user_manager,
    [auth_backend, auth_backend_bearer],
)

# Dependências prontas para usar:
current_active_user = fastapi_users.current_user(active=True)
optional_current_active_user = fastapi_users.current_user(active=True, optional=True)
current_superuser = fastapi_users.current_user(active=True, superuser=True)
