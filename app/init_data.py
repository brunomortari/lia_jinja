"""
Sistema LIA - Script de Inicializacao de Dados
===============================================
Importa o PAC do CSV e cria usuario admin
"""

import os
import csv
import io
import logging
import asyncio
import secrets
from sqlalchemy import select
from passlib.context import CryptContext
from .database import AsyncSessionLocal, engine, Base
from .models import User, PAC
from .config import settings
# Importar modelos adicionais para garantir registro dos relacionamentos no SQLAlchemy
from .models import projeto, artefatos

# Tenta importar aiofiles para I/O assíncrono
try:
    import aiofiles
    HAS_AIOFILES = True
except ImportError:
    HAS_AIOFILES = False

logger = logging.getLogger(__name__)

# Contexto de hashing de senha (mesmo que FastAPI-Users usa)
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


async def criar_tabelas():
    """Cria todas as tabelas no banco (gerenciado por Alembic, não use mais)"""
    logger.info("Tabelas gerenciadas por Alembic (nao criando aqui)")
    # async with engine.begin() as conn:
    #     await conn.run_sync(Base.metadata.create_all)
    # logger.info("Tabelas criadas com sucesso!")


async def criar_usuario_admin(db):
    """Cria usuario admin se nao existir"""
    result = await db.execute(select(User).filter(User.email == "admin@tre-go.jus.br"))
    admin = result.scalars().first()
    
    if not admin:
        # Usar senha da variável de ambiente ou gerar uma segura
        admin_password = settings.ADMIN_PASSWORD
        if not admin_password:
            admin_password = secrets.token_urlsafe(16)
            logger.warning(
                f"ADMIN_PASSWORD não configurada! Usando senha gerada: {admin_password}\n"
                "ATENÇÃO: Configure ADMIN_PASSWORD no .env para produção!"
            )
        
        admin = User(
            nome="Administrador",
            email="admin@tre-go.jus.br",
            hashed_password=pwd_context.hash(admin_password),
            cargo="Administrador",
            grupo="TIC",
            is_active=True,
            is_superuser=True,
            is_verified=True
        )
        db.add(admin)
        await db.commit()
        logger.info(f"Usuario admin criado: admin@tre-go.jus.br")
    else:
        logger.info("Usuario admin ja existe")


async def importar_pac_csv(db, csv_path: str = None):
    """Importa dados do PAC a partir do CSV"""

    # Verificar se ja existem dados
    result = await db.execute(select(PAC))
    # Eficiente para checar existencia, mas para count preciso seria select(func.count(PAC.id))
    # Como queremos saber se existe > 0, first() basta
    if result.scalars().first():
        count_result = await db.execute(select(PAC)) # Re-execute for rough count or just skip
        # Simplificacao: se tem 1, pulamos
        logger.info(f"PAC ja possui dados. Pulando importacao.")
        return
    
    # Se nenhum caminho for fornecido, determina o caminho a partir da variável de ambiente ou um padrão.
    if not csv_path:
        default_csv_path = os.path.join(os.path.dirname(__file__), 'data', 'DETALHAMENTOS.csv')
        csv_path = os.getenv("PAC_CSV_PATH", default_csv_path)
    
    if not os.path.exists(csv_path):
        logger.warning(f"Arquivo CSV do PAC não encontrado em '{csv_path}'. Pulando importação. (Pode ser configurado com a variável de ambiente PAC_CSV_PATH)")
        return

    logger.info(f"Importando PAC de: {csv_path}")

    # Mapeamento de colunas CSV -> modelo
    column_map = {
        "Ano": "ano",
        "Tipo Pac": "tipo_pac",
        "Iniciativa": "iniciativa",
        "Objetivo": "objetivo",
        "Unidade Técnica": "unidade_tecnica",
        "Unidade Administrativa": "unidade_administrativa",
        "Detalhamento": "detalhamento",
        "Quantidade": "quantidade",
        "Unidade": "unidade",
        "Frequência": "frequencia",
        "Valor Previsto": "valor_previsto",
        "Justificativa": "justificativa",
        "Prioridade": "prioridade",
        "Data Tr": "data_tr",
        "Disponibilidade Da Contratação": "disponibilidade_contratacao",
        "Número Contrato": "numero_contrato",
        "Ano Contrato": "ano_contrato",
        "Vencimento Contrato": "vencimento_contrato",
        "Prorrogação Contrato": "prorrogacao_contrato",
        "Contratação Continuada": "contratacao_continuada",
        "Catmat/catser": "catmat_catser",
        "Despesa": "despesa",
        "Elemento De Despesa": "elemento_despesa",
        "Natureza De Despesa": "natureza_despesa",
        "Inativo": "inativo",
        "Motivo Rejeição": "motivo_rejeicao",
        "Motivo Ajuste": "motivo_ajuste",
        "Número Pad": "numero_pad",
        "Ano Pad": "ano_pad",
        "Tipo De Contratação": "tipo_contratacao",
        "Descrição": "descricao",
        "Fase": "fase",
    }

    registros = 0

    # Tentar diferentes encodings
    encodings = ['utf-8', 'latin-1', 'cp1252', 'iso-8859-1']

    for encoding in encodings:
        try:
            # Usar I/O assíncrono se disponível, senão run_in_executor
            if HAS_AIOFILES:
                async with aiofiles.open(csv_path, 'r', encoding=encoding) as f:
                    content = await f.read()
                reader = csv.DictReader(io.StringIO(content), delimiter=';')
            else:
                # Fallback: executar I/O em thread separada para não bloquear
                loop = asyncio.get_event_loop()
                content = await loop.run_in_executor(
                    None, 
                    lambda: open(csv_path, 'r', encoding=encoding).read()
                )
                reader = csv.DictReader(io.StringIO(content), delimiter=';')

                for row in reader:
                    pac_data = {}

                    for csv_col, model_col in column_map.items():
                        # Normalizar nome da coluna (remover acentos e caracteres especiais)
                        value = None
                        for key in row.keys():
                            # Comparar ignorando acentos
                            key_normalized = key.replace('ã', 'a').replace('á', 'a').replace('ç', 'c').replace('é', 'e').replace('ê', 'e').replace('í', 'i').replace('ó', 'o').replace('ú', 'u')
                            csv_col_normalized = csv_col.replace('ã', 'a').replace('á', 'a').replace('ç', 'c').replace('é', 'e').replace('ê', 'e').replace('í', 'i').replace('ó', 'o').replace('ú', 'u')

                            if key_normalized.lower() == csv_col_normalized.lower():
                                value = row[key]
                                break

                        if value and value.strip():
                            pac_data[model_col] = value.strip()

                    # Converter ano para int
                    if 'ano' in pac_data:
                        try:
                            pac_data['ano'] = int(pac_data['ano'])
                        except:
                            pac_data['ano'] = 2025
                    else:
                        pac_data['ano'] = 2025

                    # Converter quantidade para float
                    if 'quantidade' in pac_data:
                        try:
                            pac_data['quantidade'] = float(pac_data['quantidade'].replace(',', '.'))
                        except:
                            pac_data['quantidade'] = None

            # Converter prioridade para int
                    if 'prioridade' in pac_data:
                        try:
                            pac_data['prioridade'] = int(pac_data['prioridade'])
                        except:
                            pac_data['prioridade'] = None

                    # Criar registro
                    pac = PAC(**pac_data)
                    db.add(pac)
                    registros += 1

                await db.commit()
                logger.info(f"Importados {registros} registros do PAC com encoding {encoding}")
                return

        except UnicodeDecodeError:
            continue
        except Exception as e:
            logger.error(f"Erro ao importar CSV com encoding {encoding}: {e}")
            await db.rollback()
            continue

    logger.error("Nao foi possivel importar o CSV com nenhum encoding")


async def criar_skills_sistema(db):
    """Cria skills padrao do sistema se nao existirem"""
    from .models import Skill
    
    # Verificar se ja existem skills do sistema
    count = await db.execute(select(Skill).filter(Skill.escopo == 'system'))
    if count.scalars().first():
        logger.info("Skills do sistema ja existem. Pulando criacao.")
        return

    logger.info("Criando skills do sistema...")
    skills = [
        {
            "nome": "Auditoria Rigorosa",
            "descricao": "Foco em conformidade legal e antecipacao de questionamentos",
            "instrucoes": "Atue como um auditor rigoroso. Cite sempre os artigos especificos da Lei 14.133/2021. Antecipe possiveis apontamentos de orgaos de controle (TCU/TCE) e justifique cada decisao com base legal solida. Seja detalhista na fundamentacao.",
            "escopo": "system"
        },
        {
            "nome": "Sustentabilidade",
            "descricao": "Enfase em criterios e praticas sustentaveis",
            "instrucoes": "Priorize a sustentabilidade em todas as etapas. Inclua criterios de sustentabilidade ambiental, social e economica. Cite o Decreto 7.746/2012 e a Instrucao Normativa 01/2010. Sugira especificacoes tecnicas que privilegiem produtos reciclados ou de menor impacto ambiental.",
            "escopo": "system"
        },
        {
            "nome": "Linguagem Simplificada",
            "descricao": "Texto claro, direto e acessivel (Plain Language)",
            "instrucoes": "Utilize Linguagem Simples (Plain Language). Evite jurisdiques desnecessario, voz passiva e periodos longos. Explique termos tecnicos. O objetivo e que qualquer cidadao compreenda o documento. Use topicos e listas para facilitar a leitura.",
            "escopo": "system"
        },
        {
            "nome": "Foco em Inovacao",
            "descricao": "Busca por solucoes inovadoras e modernas",
            "instrucoes": "Incentive a inovacao. Ao definir o objeto, nao se limite a solucoes tradicionais. Explore possibilidades de contratacao de solucoes inovadoras ou tecnologias recentes que tragam maior eficiencia. Foque em especificacoes funcionais (resultados) ao inves de descritivas.",
            "escopo": "system"
        },
        {
            "nome": "Protecao de Dados (LGPD)",
            "descricao": "Cuidado extremo com privacidade e dados pessoais",
            "instrucoes": "Atencao maxima a Lei Geral de Protecao de Dados (LGPD). Verifique se ha tratamento de dados pessoais. Inclua clausulas de responsabilidade e confidencialidade. Avalie riscos de vazamento de dados na execucao do contrato.",
            "escopo": "system"
        }
    ]

    for s in skills:
        skill = Skill(**s)
        db.add(skill)
    
    await db.commit()
    logger.info(f"Criadas {len(skills)} skills do sistema.")


async def main():
    """Funcao principal de inicializacao"""
    logger.info("=" * 50)
    logger.info("Inicializando dados do Sistema LIA (Async)")
    logger.info("=" * 50)

    # Criar tabelas
    await criar_tabelas()

    # Criar sessao
    async with AsyncSessionLocal() as db:
        try:
            # Criar usuario admin
            await criar_usuario_admin(db)

            # Importar PAC
            await importar_pac_csv(db)
            
            # Criar Skills do Sistema
            await criar_skills_sistema(db)

        finally:
             await db.close()

    logger.info("=" * 50)
    logger.info("Inicializacao concluida!")
    logger.info("=" * 50)


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    asyncio.run(main())
