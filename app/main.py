"""
Sistema LIA - Aplicacao Principal SIMPLIFICADA
==============================================
FastAPI application com Auth e Admin automáticos!

Autor: Equipe TRE-GO
Data: Janeiro 2026
"""

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.responses import JSONResponse
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
from slowapi.middleware import SlowAPIMiddleware
from .config import settings
from .database import engine, Base
import logging
import os
from pathlib import Path
from contextlib import asynccontextmanager

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

# Reduzir verbosidade de bibliotecas externas
logging.getLogger('sqlalchemy.engine').setLevel(logging.WARNING)
logging.getLogger('sqlalchemy').setLevel(logging.WARNING)
logging.getLogger('alembic').setLevel(logging.WARNING)
logging.getLogger('uvicorn.access').setLevel(logging.WARNING)

logger = logging.getLogger(__name__)


# ========== RATE LIMITING ==========

def get_real_client_ip(request: Request) -> str:
    """
    Obtém o IP real do cliente, considerando proxies.
    Verifica X-Forwarded-For e X-Real-IP antes de usar o IP direto.
    """
    # Verificar header X-Forwarded-For (comum em proxies/load balancers)
    forwarded = request.headers.get("X-Forwarded-For")
    if forwarded:
        # Pegar o primeiro IP (cliente original)
        return forwarded.split(",")[0].strip()

    # Verificar X-Real-IP (usado por alguns proxies como Nginx)
    real_ip = request.headers.get("X-Real-IP")
    if real_ip:
        return real_ip

    # Fallback para IP direto
    return get_remote_address(request)


# Configurar limiter com função customizada para obter IP
limiter = Limiter(
    key_func=get_real_client_ip,
    default_limits=["200/minute"],  # Limite padrão: 200 requests por minuto
    storage_uri=settings.REDIS_URL,  # Redis para persistência e escalabilidade
    strategy="fixed-window"
)


# ========== LIFESPAN (INICIALIZAÇÃO E ENCERRAMENTO) ==========

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Gerencia o ciclo de vida da aplicação (startup e shutdown)"""
    # --- STARTUP ---
    # Criar tabelas do banco de dados (Async)
    from .init_data import criar_tabelas, criar_usuario_admin, importar_pac_csv, criar_skills_sistema
    await criar_tabelas()
    
    # Inicialização de dados (Auto-Seed)
    from .database import AsyncSessionLocal
    
    async with AsyncSessionLocal() as db:
        try:
            await criar_usuario_admin(db)
            await importar_pac_csv(db)
            await criar_skills_sistema(db)
        finally:
            await db.close()
    
    yield
    
    # --- SHUTDOWN ---


# ========== CRIAR APLICAÇÃO FASTAPI ==========

app = FastAPI(
    title=settings.APP_NAME,
    description=settings.APP_DESCRIPTION,
    version=settings.APP_VERSION,
    docs_url="/api/docs" if settings.DEBUG else None,  # Swagger apenas em debug
    redoc_url="/api/redoc" if settings.DEBUG else None,  # ReDoc apenas em debug
    lifespan=lifespan
)

# Configurar rate limiting
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)
app.add_middleware(SlowAPIMiddleware)

# ========== MIDDLEWARES DE PERFORMANCE ==========
from fastapi.middleware.gzip import GZipMiddleware
app.add_middleware(GZipMiddleware, minimum_size=1000)



# ========== CONFIGURAR CORS ==========

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],  # Permite todos os métodos (GET, POST, PUT, DELETE, etc)
    allow_headers=["*"],  # Permite todos os headers
)


# ========== ROTAS DE SAUDE ==========

@app.get("/health")
async def health_check():
    """Health check para monitoramento"""
    return {
        "status": "healthy",
        "app": settings.APP_NAME,
        "version": settings.APP_VERSION
    }


# ========== ARQUIVOS ESTATICOS ==========

# Montar pasta static para servir CSS, JS, imagens
static_path = Path(__file__).parent / "static"
if not static_path.exists():
    static_path.mkdir(parents=True, exist_ok=True)

app.mount("/static", StaticFiles(directory=str(static_path)), name="static")


# ========== IMPORTAR E REGISTRAR ROUTERS ==========

from .routers import projetos, pac, ia, ia_pgr, export, artefatos, dfd, cotacao
from .routers.views import router as views_router

# Registrar router de views (paginas HTML) - SEM prefixo
app.include_router(views_router, tags=["Views"])


# ========== AUTH SIMPLIFICADO (FastAPI-Users) ==========

from .auth import fastapi_users, auth_backend
from .schemas import UserRead, UserCreate, UserUpdate

# Auth Routes - Login, Registro, Reset Senha (TUDO AUTOMÁTICO!)
app.include_router(
    fastapi_users.get_auth_router(auth_backend),
    prefix="/auth/jwt",
    tags=["🔐 Auth - Login/Logout"],
)

app.include_router(
    fastapi_users.get_register_router(UserRead, UserCreate),
    prefix="/auth",
    tags=["🔐 Auth - Registro"],
)

app.include_router(
    fastapi_users.get_reset_password_router(),
    prefix="/auth",
    tags=["🔐 Auth - Reset Senha"],
)

app.include_router(
    fastapi_users.get_users_router(UserRead, UserUpdate),
    prefix="/users",
    tags=["👤 Usuários"],
)

logger.info("✅ Auth routes configured")


# ========== API ROUTERS ==========

# Registrar routers de API com prefixo /api
app.include_router(projetos.router, prefix="/api/projetos", tags=["📁 Projetos"])
app.include_router(pac.router, prefix="/api/pac", tags=["🛒 PAC"])

app.include_router(ia.router, prefix="/api/ia", tags=["🤖 Integração IA - Artefatos"])
app.include_router(ia_pgr.router, prefix="/api/pgr", tags=["⚠️ PGR Inteligente"])

# IA Nativa (Python + OpenRouter) 
from .routers import ia_native, ia_models, ia_upload
app.include_router(ia_native.router, prefix="/api/ia-native", tags=["🧠 IA Nativa"])
app.include_router(ia_models.router, tags=["🎯 Modelos IA"])
app.include_router(ia_upload.router)

app.include_router(export.router, prefix="/api/export", tags=["📄 Exportação"])

# Routers de Artefatos
app.include_router(dfd.router, prefix="/api/dfd", tags=["📋 DFD"])
app.include_router(cotacao.router, prefix="/api/cotacao", tags=["💰 Cotação"])
app.include_router(artefatos.etp_router, prefix="/api/etp", tags=["📋 ETP"])
app.include_router(artefatos.tr_router, prefix="/api/tr", tags=["📋 TR"])
app.include_router(artefatos.riscos_router, prefix="/api/riscos", tags=["⚠️ Riscos"])
app.include_router(artefatos.item_risco_router, prefix="/api", tags=["⚠️ Itens de Risco"])
app.include_router(artefatos.edital_router, prefix="/api/edital", tags=["📜 Edital"])
app.include_router(artefatos.pesquisa_precos_router, prefix="/api/pesquisa_precos", tags=["💰 Pesquisa Preços"])

# Routers de Licitação Normal e Contratação Direta
app.include_router(artefatos.checklist_conformidade_router, prefix="/api/checklist_conformidade", tags=["✅ Checklist Conformidade"])
app.include_router(artefatos.minuta_contrato_router, prefix="/api/minuta_contrato", tags=["📜 Minuta de Contrato"])
app.include_router(artefatos.aviso_publicidade_direta_router, prefix="/api/aviso_publicidade_direta", tags=["📢 Aviso Dispensa"])
app.include_router(artefatos.justificativa_fornecedor_escolhido_router, prefix="/api/justificativa_fornecedor_escolhido", tags=["👤 Justificativa Fornecedor"])

# Routers de Adesão a Ata
app.include_router(artefatos.rdve_router, prefix="/api/rdve", tags=["📊 RDVE - Relatório Vantagem Econômica"])
app.include_router(artefatos.jva_router, prefix="/api/jva", tags=["📋 JVA - Justificativa Vantagem Adesão"])
app.include_router(artefatos.tafo_router, prefix="/api/tafo", tags=["✅ TAFO - Termo Aceite Fornecedor"])

# Routers de Dispensa por Valor Baixo
app.include_router(artefatos.trs_router, prefix="/api/trs", tags=["📄 TRS - Termo Referência Simplificado"])
app.include_router(artefatos.ade_router, prefix="/api/ade", tags=["📢 ADE - Aviso Dispensa Eletrônica"])
app.include_router(artefatos.jpef_router, prefix="/api/jpef", tags=["💵 JPEF - Justificativa Preço/Fornecedor"])
app.include_router(artefatos.ce_router, prefix="/api/ce", tags=["✅ CE - Certidão Enquadramento"])

# Router de Portaria de Designação
from .routers import portaria_designacao
app.include_router(portaria_designacao.router, prefix="/api/portaria-designacao", tags=["📋 Portaria de Designação"])

# Router de ETP com Adesão de Ata
from .routers import ia_etp_adesao
app.include_router(ia_etp_adesao.router, prefix="/api/etp", tags=["📋 ETP - Adesão de Ata"])

# Router de Decisão de Modalidade (F2)
from .routers import modalidade
app.include_router(modalidade.router, tags=["🔀 Decisão de Modalidade"])

# Router de pesquisa de preços (Compras.gov)
from .routers import prices
app.include_router(prices.router, tags=["🔍 Compras.gov"])

# Skills (Habilidades)
from .routers import skills, skills_chat
app.include_router(skills.router, prefix="/api/skills", tags=["🎯 Skills"])
app.include_router(skills_chat.router, prefix="/api", tags=["🎯 Skill Wizard"])

# Prompt Templates (Gerenciamento de Prompts)
from .routers import prompt_templates
app.include_router(prompt_templates.router, tags=["🔧 Prompt Templates"])

# Notícias (News Feed)
from .routers import news
app.include_router(news.router, tags=["📰 Notícias"])


# ========== INFORMAÇÕES DO SISTEMA ==========

# ========== ADMIN INTERFACE ==========
from .admin import setup_admin
setup_admin(app, engine)

logger.info(f"✅ Sistema LIA v{settings.APP_VERSION} iniciado | API: http://localhost:8000/api/docs | Admin: http://localhost:8000/admin")


# ========== INICIAR APLICAÇÃO ==========

if __name__ == "__main__":
    import uvicorn
    
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=settings.DEBUG,
        log_level="warning",
        access_log=False
    )
