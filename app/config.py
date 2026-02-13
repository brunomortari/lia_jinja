"""
Sistema LIA - Configurações
=============================
Este módulo centraliza todas as configurações do sistema.
Utiliza pydantic-settings para carregar variáveis de ambiente.

Autor: Equipe TRE-GO
Data: Janeiro 2026
"""

from pydantic_settings import BaseSettings
from pydantic import field_validator, model_validator
from typing import List, Union
from pathlib import Path
import warnings


class Settings(BaseSettings):
    """
    Classe de configurações do sistema
    
    As configurações podem ser definidas via:
    1. Arquivo .env
    2. Variáveis de ambiente do sistema
    3. Valores padrão (definidos aqui)
    """
    
    # ========== APLICAÇÃO ==========
    APP_NAME: str = "Sistema LIA"
    APP_VERSION: str = "1.0.0"
    APP_DESCRIPTION: str = "Licitações com IA - Equipe Nativa: TRE-GO, TRE-AC e TJAP"
    DEBUG: bool = True
    API_PUBLIC_URL: str = "http://localhost:8000"
    
    # ========== BANCO DE DADOS ==========
    # PostgreSQL como banco principal (configurado via docker-compose)
    DATABASE_URL: str
    
    # ========== SEGURANÇA JWT ==========
    SECRET_KEY: str
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 1440  # 24 horas
    
    # ========== CORS ==========
    CORS_ORIGINS: List[str] = [
        "http://localhost:8000",
        "http://127.0.0.1:8000",
        "http://localhost:8080",
        "http://127.0.0.1:8080",
    ]

    @field_validator('CORS_ORIGINS', mode='before')
    @classmethod
    def parse_cors_origins(cls, v):
        """Converte string separada por virgulas em lista"""
        if isinstance(v, str):
            return [origin.strip() for origin in v.split(',')]
        return v

    @model_validator(mode='after')
    def validate_security(self):
        """Valida configurações de segurança"""
        # Validar SECRET_KEY
        if len(self.SECRET_KEY) < 32:
            if not self.DEBUG:
                raise ValueError(
                    "SECRET_KEY deve ter pelo menos 32 caracteres em produção. "
                    "Gere uma com: python -c \"import secrets; print(secrets.token_urlsafe(32))\""
                )
            else:
                warnings.warn(
                    "SECRET_KEY muito curta! Use pelo menos 32 caracteres. "
                    "Gere uma com: python -c \"import secrets; print(secrets.token_urlsafe(32))\"",
                    UserWarning
                )

        # Validar que não está usando a chave padrão insegura
        insecure_keys = ["lia", "secret", "changeme", "your-secret-key"]
        if self.SECRET_KEY.lower() in insecure_keys:
            if not self.DEBUG:
                raise ValueError("SECRET_KEY insegura detectada! Gere uma nova chave para produção.")
            else:
                warnings.warn("SECRET_KEY insegura! Gere uma nova chave.", UserWarning)

        return self
    

    # ========== OPENROUTER (IA NATIVA) ==========
    OPENROUTER_API_KEY: str = ""
    OPENROUTER_BASE_URL: str = "https://openrouter.ai/api/v1"
    OPENROUTER_DEFAULT_MODEL: str = "arcee-ai/trinity-mini:free"
    OPENROUTER_TIMEOUT: int = 120

    # ========== REDIS ==========
    REDIS_URL: str = "redis://localhost:6379/0"

    # ========== ADMIN ==========
    # Senha do admin inicial (NUNCA usar valor padrão em produção!)
    ADMIN_PASSWORD: str = ""

    # ========== DADOS ==========
    PAC_CSV_PATH: str = "app/data/DETALHAMENTOS.csv"
    
    class Config:
        """Configuração do Pydantic"""
        # Use absolute path to the repository .env so loading works independent
        # of the current working directory (helps when running via managers/containers)
        BASE_DIR = Path(__file__).resolve().parent.parent
        env_file = str(BASE_DIR / '.env')
        env_file_encoding = "utf-8"
        case_sensitive = True


# Instância global
# Carregar configurações
settings = Settings()

# ========== MODELOS IA DISPONÍVEIS ==========
# Lista de modelos OpenRouter disponíveis para o usuário
AVAILABLE_MODELS = [
    {
        "id": "allenai/molmo-2-8b:free",
        "name": "Molmo 2 8B",
        "description": "Modelo multimodal eficiente",
        "tier": "free",
        "icon": "🔮"
    },
    {
        "id": "arcee-ai/trinity-large-preview:free",
        "name": "Trinity Large",
        "description": "Alta capacidade de raciocínio",
        "tier": "free",
        "icon": "⚡"
    },
    {
        "id": "arcee-ai/trinity-mini:free",
        "name": "Trinity Mini",
        "description": "Rápido e leve (Padrão)",
        "tier": "free",
        "icon": "⚡"
    },
    {
        "id": "cognitivecomputations/dolphin-mistral-24b-venice-edition:free",
        "name": "Dolphin Mistral 24B",
        "description": "Versão não censurada do Mistral",
        "tier": "free",
        "icon": "�"
    },
    {
        "id": "deepseek/deepseek-r1-0528:free",
        "name": "DeepSeek R1",
        "description": "Especialista em raciocínio (CoT)",
        "tier": "free",
        "icon": "🧮"
    },
    {
        "id": "google/gemma-3-12b-it:free",
        "name": "Gemma 3 12B",
        "description": "Modelo intermediário do Google",
        "tier": "free",
        "icon": "💎"
    },
    {
        "id": "google/gemma-3-27b-it:free",
        "name": "Gemma 3 27B",
        "description": "Alta performance Google",
        "tier": "free",
        "icon": "💎"
    },
    {
        "id": "meta-llama/llama-3.3-70b-instruct:free",
        "name": "Llama 3.3 70B",
        "description": "Estado da arte em open source",
        "tier": "free",
        "icon": "🦙"
    },
    {
        "id": "mistralai/mistral-small-3.1-24b-instruct:free",
        "name": "Mistral Small 3",
        "description": "Eficiente e preciso",
        "tier": "free",
        "icon": "🌪️"
    },
    {
        "id": "nvidia/nemotron-3-nano-30b-a3b:free",
        "name": "Nemotron 3 30B",
        "description": "Otimizado pela NVIDIA",
        "tier": "free",
        "icon": "🤮"
    },
    {
        "id": "nousresearch/hermes-3-llama-3.1-405b:free",
        "name": "Hermes 3 405B",
        "description": "Maior modelo gratuito disponível",
        "tier": "free",
        "icon": "🔥"
    },
    {
        "id": "openai/gpt-oss-120b:free",
        "name": "GPT OSS 120B",
        "description": "Modelo open source (réplica GPT)",
        "tier": "free",
        "icon": "🧠"
    },
    {
        "id": "openai/gpt-oss-20b:free",
        "name": "GPT OSS 20B",
        "description": "Versão leve GPT Open Source",
        "tier": "free",
        "icon": "🧠"
    },
    {
        "id": "qwen/qwen3-4b:free",
        "name": "Qwen3 4B",
        "description": "Ultra leve e rápido",
        "tier": "free",
        "icon": "🐉"
    },
    {
        "id": "qwen/qwen3-next-80b-a3b-instruct:free",
        "name": "Qwen3 Next 80B",
        "description": "Performance de ponta chinês",
        "tier": "free",
        "icon": "🐉"
    },
    {
        "id": "tngtech/deepseek-r1t-chimera:free",
        "name": "DeepSeek R1T Chimera",
        "description": "Merge experimental R1",
        "tier": "free",
        "icon": "🧪"
    },
    {
        "id": "tngtech/deepseek-r1t2-chimera:free",
        "name": "DeepSeek R1T2 Chimera",
        "description": "Variação Chimera V2",
        "tier": "free",
        "icon": "🧪"
    },
    {
        "id": "tngtech/tng-r1t-chimera:free",
        "name": "TNG R1T Chimera",
        "description": "Merge TNG",
        "tier": "free",
        "icon": "🧪"
    },
    {
        "id": "upstage/solar-pro-3:free",
        "name": "Solar Pro 3",
        "description": "Especialista em lógica",
        "tier": "free",
        "icon": "☀️"
    },
    {
        "id": "liquid/lfm-2.5-1.2b-thinking:free",
        "name": "Liquid LFM 2.5",
        "description": "Arquitetura líquida inovadora",
        "tier": "free",
        "icon": "�"
    }
]

# Tiers de modelos (para UI)
MODEL_TIERS = {
    "free": {
        "name": "Gratuito",
        "color": "#10b981"
    },
    "standard": {
        "name": "Standard",
        "color": "#3b82f6"
    },
    "premium": {
        "name": "Premium",
        "color": "#8b5cf6"
    }
}


# ========== CONSTANTES DO SISTEMA ==========

class ProjetoStatus:
    """
    Status possíveis de um projeto:
    - RASCUNHO: Nenhum DFD criado.
    - EM_ANDAMENTO: DFD criado, mas o Edital (último) ainda não.
    - CONCLUIDO: Edital aprovado e enviado ao SEI.
    """
    RASCUNHO = "rascunho"
    EM_ANDAMENTO = "em_andamento"
    CONCLUIDO = "concluido"


class ArtefatoStatus:
    """
    Status possíveis de um artefato:
    - RASCUNHO: Ainda não foi aprovado.
    - APROVADO: Foi aprovado.
    """
    RASCUNHO = "rascunho"
    APROVADO = "aprovado"


class TipoArtefato:
    """Tipos de artefatos no sistema"""
    DFD = "dfd"
    PESQUISA_PRECOS = "pesquisa_precos"
    ANALISE_RISCOS = "riscos"
    ETP = "etp"
    TR = "tr"
    EDITAL = "edital"


class PerfilUsuario:
    """Perfis de acesso no sistema"""
    ADMIN = "admin"
    OPERADOR = "operador"
    VISUALIZADOR = "visualizador"
