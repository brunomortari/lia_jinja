
import os
import sys
import asyncio
import logging
from datetime import datetime, timezone
from typing import Optional, List

import httpx
from sqlalchemy import Column, Integer, String, Boolean, Text, DateTime, BigInteger
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.orm import declarative_base
from dotenv import load_dotenv

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger("CatalogScraper")

# Load environment variables
# Assuming running from project root or catalogo dir
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(current_dir)
load_dotenv(os.path.join(project_root, ".env"))

# Database Configuration
DATABASE_URL = os.getenv("DATABASE_URL")
if not DATABASE_URL:
    logger.error("DATABASE_URL not found in .env")
    sys.exit(1)

# Async conversion logic (matching app/database.py)
if DATABASE_URL.startswith("postgresql://"):
    DATABASE_URL = DATABASE_URL.replace("postgresql://", "postgresql+asyncpg://")
elif DATABASE_URL.startswith("sqlite://") and "aiosqlite" not in DATABASE_URL:
    DATABASE_URL = DATABASE_URL.replace("sqlite://", "sqlite+aiosqlite://")

# Database Setup
engine = create_async_engine(DATABASE_URL, echo=False)
AsyncSessionLocal = async_sessionmaker(bind=engine, class_=AsyncSession, expire_on_commit=False)
Base = declarative_base()

# Models
class Material(Base):
    __tablename__ = "materiais"
    
    codigo_item = Column(BigInteger, primary_key=True, index=True)
    descricao_item = Column(Text, nullable=True)
    codigo_grupo = Column(Integer, index=True)
    nome_grupo = Column(String(255), nullable=True)
    codigo_classe = Column(Integer, index=True)
    nome_classe = Column(String(255), nullable=True)
    codigo_pdm = Column(Integer, index=True)
    nome_pdm = Column(String(255), nullable=True)
    status_item = Column(Boolean, default=True)
    item_sustentavel = Column(Boolean, default=False)
    data_atualizacao = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

class Servico(Base):
    __tablename__ = "servicos"
    
    codigo_servico = Column(BigInteger, primary_key=True, index=True)
    nome_servico = Column(Text, nullable=True)
    codigo_secao = Column(Integer, index=True)
    nome_secao = Column(String(255), nullable=True)
    codigo_divisao = Column(Integer, index=True)
    nome_divisao = Column(String(255), nullable=True)
    codigo_grupo = Column(Integer, index=True)
    nome_grupo = Column(String(255), nullable=True)
    codigo_classe = Column(Integer, index=True)
    nome_classe = Column(String(255), nullable=True)
    codigo_subclasse = Column(Integer, index=True)
    nome_subclasse = Column(String(255), nullable=True)
    codigo_cpc = Column(BigInteger, nullable=True)
    status_servico = Column(Boolean, default=True)
    data_atualizacao = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

# API Client
API_BASE_URL = "https://dadosabertos.compras.gov.br"

async def fetch_page(client: httpx.AsyncClient, url: str, page: int, page_size: int = 500):
    while True:
        try:
            response = await client.get(url, params={"pagina": page, "tamanhoPagina": page_size})
            
            if response.status_code == 200:
                return response.json()
            
            if response.status_code == 429: # Too Many Requests
                logger.warning(f"Rate limit 429 hit for page {page}. Waiting 20 seconds before retrying...")
                await asyncio.sleep(20)
                continue
            
            logger.error(f"Failed to fetch page {page}: {response.status_code} - {response.text}")
            return None
        except Exception as e:
            logger.error(f"Error fetching page {page} from {url}: {e}")
            return None

async def init_db():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

async def sync_materials():
    logger.info("Starting Materials Sync...")
    url = f"{API_BASE_URL}/modulo-material/4_consultarItemMaterial"
    
    async with httpx.AsyncClient(timeout=60.0) as client:
        # Initial fetch to get total pages
        initial_data = await fetch_page(client, url, 1, 500)
        if not initial_data:
            logger.error("Could not fetch initial material data")
            return

        total_pages = initial_data.get("totalPaginas", 0)
        logger.info(f"Total pages for Materials: {total_pages}")

        async with AsyncSessionLocal() as session:
            for page in range(1, total_pages + 1):
                logger.info(f"Processing Material Page {page}/{total_pages}")
                # Wait 5 seconds between requests as requested
                await asyncio.sleep(5)
                
                data = await fetch_page(client, url, page, 500)
                if not data:
                    continue
                
                results = data.get("resultado", [])
                if not results:
                    continue

                for item in results:
                    codigo = item.get("codigoItem")
                    if not codigo:
                        continue

                    # Check existence
                    existing = await session.get(Material, codigo)
                    if not existing:
                        existing = Material(codigo_item=codigo)
                        session.add(existing)
                    
                    # Update fields
                    existing.descricao_item = item.get("descricaoItem")
                    existing.codigo_grupo = item.get("codigoGrupo")
                    existing.nome_grupo = item.get("nomeGrupo")
                    existing.codigo_classe = item.get("codigoClasse")
                    existing.nome_classe = item.get("nomeClasse")
                    existing.codigo_pdm = item.get("codigoPdm")
                    existing.nome_pdm = item.get("nomePdm")
                    existing.status_item = item.get("statusItem")
                    existing.item_sustentavel = item.get("itemSustentavel")
                
                # Commit every page
                try:
                    await session.commit()
                except Exception as e:
                    logger.error(f"Error committing page {page}: {e}")
                    await session.rollback()

async def sync_services():
    logger.info("Starting Services Sync...")
    url = f"{API_BASE_URL}/modulo-servico/6_consultarItemServico"
    
    async with httpx.AsyncClient(timeout=60.0) as client:
        initial_data = await fetch_page(client, url, 1, 500)
        if not initial_data:
            logger.error("Could not fetch initial service data")
            return

        total_pages = initial_data.get("totalPaginas", 0)
        logger.info(f"Total pages for Services: {total_pages}")

        async with AsyncSessionLocal() as session:
            for page in range(1, total_pages + 1):
                logger.info(f"Processing Service Page {page}/{total_pages}")
                # Wait 5 seconds between requests as requested
                await asyncio.sleep(5)

                data = await fetch_page(client, url, page, 500)
                if not data:
                    continue
                
                results = data.get("resultado", [])
                if not results:
                    continue

                for item in results:
                    codigo = item.get("codigoServico")
                    if not codigo:
                        continue

                    existing = await session.get(Servico, codigo)
                    if not existing:
                        existing = Servico(codigo_servico=codigo)
                        session.add(existing)
                    
                    existing.nome_servico = item.get("nomeServico")
                    existing.codigo_secao = item.get("codigoSecao")
                    existing.nome_secao = item.get("nomeSecao")
                    existing.codigo_divisao = item.get("codigoDivisao")
                    existing.nome_divisao = item.get("nomeDivisao")
                    existing.codigo_grupo = item.get("codigoGrupo")
                    existing.nome_grupo = item.get("nomeGrupo")
                    existing.codigo_classe = item.get("codigoClasse")
                    existing.nome_classe = item.get("nomeClasse")
                    existing.codigo_subclasse = item.get("codigoSubclasse")
                    existing.nome_subclasse = item.get("nomeSubclasse")
                    existing.codigo_cpc = item.get("codigoCpc")
                    existing.status_servico = item.get("statusServico")
                
                try:
                    await session.commit()
                except Exception as e:
                    logger.error(f"Error committing page {page}: {e}")
                    await session.rollback()

async def main():
    logger.info("Starting Catalog Scraper...")
    await init_db()
    # Run sequentially
    await sync_materials()
    await sync_services()
    logger.info("Finished Catalog Scraper.")

if __name__ == "__main__":
    asyncio.run(main())
