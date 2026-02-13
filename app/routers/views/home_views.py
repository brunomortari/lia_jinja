"""
Sistema LIA - Views Home, PAC e Configurações
==============================================
Dashboard principal, listagem de artefatos, PAC e páginas de configuração.

Autor: Equipe TRE-GO
Data: Janeiro 2026
"""

from fastapi import APIRouter, Request, Depends, Form
from fastapi.responses import HTMLResponse, RedirectResponse, JSONResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from sqlalchemy.orm import selectinload
from typing import List, Optional
from datetime import datetime
import httpx
import xml.etree.ElementTree as ET

from app.database import get_db
from app.models.user import User
from app.config import settings
from app.models.projeto import Projeto
from app.models.pac import PAC
from app.models.artefatos import (
    DFD, ETP, TR, Riscos, Edital, PesquisaPrecos
)
from app.auth import optional_current_active_user

from .common import (
    templates,
    require_login,
    logger
)


router = APIRouter()


# ========== DASHBOARD INICIAL ==========

async def fetch_licitacao_news():
    """Busca notícias sobre Licitações e IA no Google News RSS."""
    # Busca 2 feeds: licitações e IA
    feeds = [
        "https://news.google.com/rss/search?q=licitações+públicas+brasil&hl=pt-BR&gl=BR&ceid=BR:pt-419",
        "https://news.google.com/rss/search?q=inteligência+artificial+IA+brasil&hl=pt-BR&gl=BR&ceid=BR:pt-419"
    ]
    noticias = []
    
    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            for rss_url in feeds:
                try:
                    response = await client.get(rss_url)
                    if response.status_code == 200:
                        root = ET.fromstring(response.content)
                        # Parse todas as notícias recentes (sem limite inicialmente)
                        for item in root.findall(".//item"):
                            title = item.find("title").text if item.find("title") is not None else "Sem título"
                            link = item.find("link").text if item.find("link") is not None else "#"
                            pub_date = item.find("pubDate").text if item.find("pubDate") is not None else ""
                            # Formatar data simples
                            data_fmt = "Recente"
                            if pub_date:
                                try:
                                    dt = datetime.strptime(pub_date[:16], "%a, %d %b %Y")
                                    # Só mostra notícias dos últimos 7 dias
                                    dias_atras = (datetime.utcnow() - dt).days
                                    if dias_atras <= 7:
                                        data_fmt = dt.strftime("%d %b")
                                    else:
                                        continue  # pula notícias muito antigas
                                except:
                                    pass
                            # Evita duplicatas
                            if not any(n["titulo"].lower() == title.lower() for n in noticias):
                                noticias.append({
                                    "titulo": title,
                                    "link": link,
                                    "data": data_fmt,
                                    "descricao": title
                                })
                except Exception as e:
                    logger.warning(f"Erro ao buscar feed {rss_url}: {e}")
                    continue
        
        # Se conseguiu notícias, retorna apenas 2
        if noticias:
            return noticias[:2]
            
    except Exception as e:
        logger.error(f"Erro geral ao buscar notícias RSS: {e}")
    
    # Fallback: retorna placeholder com instruções
    return [
        {
            "titulo": "Notícias sobre Licitações e IA em tempo real",
            "link": "https://news.google.com/search?q=licitações+públicas+brasil",
            "data": "Hoje",
            "descricao": "Atualizações contínuas sobre licitações públicas e inteligência artificial no Brasil"
        },
        {
            "titulo": "Acompanhe as últimas tendências em contratações públicas",
            "link": "https://news.google.com/search?q=inteligência+artificial+brasil",
            "data": "Hoje",
            "descricao": "Tecnologia e inovação em processos de licitação"
        }
    ]

async def fetch_online_models():
    """Verifica status dos modelos na API OpenRouter."""
    online_models = set()
    try:
        async with httpx.AsyncClient(timeout=2.0) as client:
            headers = {
                "Authorization": f"Bearer {settings.OPENROUTER_API_KEY}",
                "HTTP-Referer": "https://lia.tre-go.jus.br",
                "X-Title": "LIA TRE-GO"
            }
            resp = await client.get("https://openrouter.ai/api/v1/models", headers=headers)
            if resp.status_code == 200:
                data = resp.json()
                for model in data.get("data", []):
                    online_models.add(model.get("id"))
    except Exception as e:
        logger.warning(f"Erro ao verificar status dos modelos: {e}")
        # Fallback: mantém o default como online se falhar para não quebrar a UI
        online_models.add("arcee-ai/trinity-mini:free")
    return online_models

@router.get("/api/verificar-modelos", response_class=JSONResponse)
async def verificar_modelos_api():
    """API para verificar status dos modelos em tempo real (AJAX)."""
    online = await fetch_online_models()
    return {"online": list(online)}


@router.get("/api/ping-modelo/{modelo_nome:path}", response_class=JSONResponse)
async def ping_modelo_api(modelo_nome: str):
    """
    Faz um ping REAL no modelo para verificar se está respondendo.
    Envia uma mensagem mínima e verifica a resposta.
    
    Retorna:
    - status: 'online', 'rate_limited', 'offline', 'error'
    - tempo_ms: tempo de resposta em milissegundos
    - mensagem: descrição do status
    """
    import time
    
    start_time = time.time()
    
    try:
        async with httpx.AsyncClient(timeout=15.0) as client:
            headers = {
                "Authorization": f"Bearer {settings.OPENROUTER_API_KEY}",
                "HTTP-Referer": "https://lia.ai",
                "X-Title": "LIA",
                "Content-Type": "application/json"
            }
            
            # Requisição mínima para testar o modelo
            payload = {
                "model": modelo_nome,
                "messages": [{"role": "user", "content": "ping"}],
                "max_tokens": 1,
                "temperature": 0
            }
            
            resp = await client.post(
                "https://openrouter.ai/api/v1/chat/completions",
                headers=headers,
                json=payload
            )
            
            tempo_ms = int((time.time() - start_time) * 1000)
            
            if resp.status_code == 200:
                return {
                    "status": "online",
                    "tempo_ms": tempo_ms,
                    "mensagem": f"Respondeu em {tempo_ms}ms"
                }
            elif resp.status_code == 429:
                return {
                    "status": "rate_limited",
                    "tempo_ms": tempo_ms,
                    "mensagem": "Rate limit atingido"
                }
            elif resp.status_code == 503:
                return {
                    "status": "offline",
                    "tempo_ms": tempo_ms,
                    "mensagem": "Modelo indisponível"
                }
            else:
                error_detail = ""
                try:
                    error_data = resp.json()
                    error_detail = error_data.get("error", {}).get("message", "")
                except:
                    pass
                return {
                    "status": "error",
                    "tempo_ms": tempo_ms,
                    "mensagem": f"Erro {resp.status_code}: {error_detail[:50]}" if error_detail else f"Erro HTTP {resp.status_code}"
                }
                
    except httpx.TimeoutException:
        tempo_ms = int((time.time() - start_time) * 1000)
        return {
            "status": "offline",
            "tempo_ms": tempo_ms,
            "mensagem": "Timeout (15s)"
        }
    except Exception as e:
        tempo_ms = int((time.time() - start_time) * 1000)
        logger.error(f"Erro ao pingar modelo {modelo_nome}: {e}")
        return {
            "status": "error",
            "tempo_ms": tempo_ms,
            "mensagem": f"Erro: {str(e)[:30]}"
        }


@router.get("/", response_class=HTMLResponse)
async def home(
    request: Request,
    db: AsyncSession = Depends(get_db),
    usuario: User = Depends(optional_current_active_user)
):
    """Dashboard analítico da página inicial."""
    if not usuario:
        return RedirectResponse(url="/login", status_code=303)

    # Buscar todos os projetos do usuário
    result = await db.execute(select(Projeto).filter(Projeto.usuario_id == usuario.id))
    projetos_usuario = result.scalars().all()
    projeto_ids = [p.id for p in projetos_usuario]

    # Estatísticas gerais
    total_projetos = len(projetos_usuario)

    # Contar artefatos por tipo
    async def count_artefact(model):
        if not projeto_ids:
            return 0
        return (await db.execute(select(func.count()).filter(model.projeto_id.in_(projeto_ids)))).scalar() or 0

    total_dfds = await count_artefact(DFD)
    total_etps = await count_artefact(ETP)
    total_trs = await count_artefact(TR)
    total_riscos = await count_artefact(Riscos)
    total_editais = await count_artefact(Edital)
    total_pesquisas = await count_artefact(PesquisaPrecos)

    total_artefatos = total_dfds + total_etps + total_trs + total_riscos + total_editais + total_pesquisas

    # Artefatos gerados por IA
    async def count_ia(model):
        if not projeto_ids:
            return 0
        return (await db.execute(select(func.count()).filter(model.projeto_id.in_(projeto_ids), model.gerado_por_ia == True))).scalar() or 0

    artefatos_ia = (
        await count_ia(DFD) +
        await count_ia(ETP) +
        await count_ia(TR) +
        await count_ia(Riscos) +
        await count_ia(Edital)
    )

    # Projetos recentes (últimos 5)
    projetos_recentes = sorted(
        projetos_usuario,
        key=lambda p: p.data_atualizacao or p.data_criacao,
        reverse=True
    )[:5]

    # Atividades recentes (últimos artefatos criados/atualizados)
    atividades_recentes = []

    if projeto_ids:
        # Buscar artefatos recentes de todos os tipos
        artefato_configs = [
            (DFD, "DFD", "#5a9dd6", 3),
            (ETP, "ETP", "#51bb7b", 2),
            (TR, "TR", "#e6b800", 2),
            (Riscos, "Riscos", "#d65a5a", 2),
            (Edital, "Edital", "#7b51bb", 2),
            (PesquisaPrecos, "PesquisaPrecos", "#5ad6a7", 2)
        ]
        for model, tipo, cor, limit in artefato_configs:
            result = await db.execute(select(model).filter(model.projeto_id.in_(projeto_ids)).order_by(model.data_atualizacao.desc()).limit(limit))
            for item in result.scalars().all():
                projeto = next((p for p in projetos_usuario if p.id == item.projeto_id), None)
                if projeto:
                    atividades_recentes.append({
                        "tipo": tipo,
                        "cor": cor,
                        "projeto": projeto.titulo,
                        "data": item.data_atualizacao or item.data_criacao,
                        "acao": "Atualizado" if getattr(item, "data_atualizacao", None) else "Criado"
                    })

    # Ordenar atividades por data
    atividades_recentes.sort(key=lambda x: x["data"], reverse=True)
    atividades_recentes = atividades_recentes[:5]

    # Ajustar formato da data para exibição (Dia/Mês às Hora:Min)
    for atv in atividades_recentes:
        if isinstance(atv["data"], datetime):
             atv["data_fmt"] = atv["data"].strftime('%d/%m às %H:%M')
        else:
             atv["data_fmt"] = str(atv["data"])

    # Distribuição de artefatos por tipo
    distribuicao_artefatos = {
        "DFD": total_dfds,
        "ETP": total_etps,
        "TR": total_trs,
        "PGR": total_riscos,
        "Edital": total_editais,
        "PP": total_pesquisas
    }

    # Calcular taxa de uso de IA
    taxa_ia = round((artefatos_ia / total_artefatos * 100) if total_artefatos > 0 else 0)

    # Projetos por status
    projetos_em_andamento = sum(1 for p in projetos_usuario if p.status in ['em_andamento', 'planejamento'])
    projetos_concluidos = sum(1 for p in projetos_usuario if p.status == 'concluido')

    # Buscar Notícias Reais
    noticias = await fetch_licitacao_news()

    return templates.TemplateResponse(
        "pages/inicio.html",
        {
            "request": request,
            "usuario": usuario,
            "page": "inicio",
            "page_title": "Dashboard",
            # Estatísticas
            "total_projetos": total_projetos,
            "total_artefatos": total_artefatos,
            "artefatos_ia": artefatos_ia,
            "taxa_ia": taxa_ia,
            "projetos_em_andamento": projetos_em_andamento,
            "projetos_concluidos": projetos_concluidos,
            # Distribuição
            "distribuicao_artefatos": distribuicao_artefatos,
            # Listas
            "projetos_recentes": projetos_recentes,
            "atividades_recentes": atividades_recentes,
            "noticias": noticias
        }
    )


# ========== CRIAR PROJETO (via PAC) ==========

@router.post("/projetos/novo", response_class=HTMLResponse)
async def criar_projeto(
    request: Request,
    titulo: str = Form(...),
    prompt_inicial: str = Form(""),
    itens_pac: List[int] = Form(default=[]),
    itens_pac_json: Optional[str] = Form(default="[]"),
    db: AsyncSession = Depends(get_db),
    usuario: User = Depends(optional_current_active_user)
):
    """Cria novo projeto a partir de itens do PAC ou sem PAC (Justificativa de Excepcionalidade)."""
    import json
    
    if not usuario:
        return RedirectResponse(url="/login", status_code=303)

    # Se itens_pac_json foi enviado (novo formato de "Criar sem PAC"), usar esse
    if itens_pac_json and itens_pac_json != "[]":
        try:
            itens_pac_parsed = json.loads(itens_pac_json)
        except json.JSONDecodeError:
            itens_pac_parsed = []
    else:
        # Formato antigo: processar checkboxes individuais
        form_data = await request.form()
        itens_pac_parsed = []
        
        for pac_id in itens_pac:
            quantidade_key = f"quantidade_{pac_id}"
            quantidade = form_data.get(quantidade_key)
            try:
                quantidade = float(quantidade) if quantidade else None
            except (ValueError, TypeError):
                quantidade = None

            itens_pac_parsed.append({
                "id": pac_id,
                "quantidade": quantidade
            })

    projeto = Projeto(
        titulo=titulo,
        descricao="",
        prompt_inicial=prompt_inicial,
        usuario_id=usuario.id,
        itens_pac=itens_pac_parsed,  # Pode ser [] para projetos com Justificativa de Excepcionalidade
        status="rascunho"
    )
    db.add(projeto)
    await db.commit()
    await db.refresh(projeto)

    return RedirectResponse(url=f"/projetos/{projeto.id}", status_code=303)


# ========== PAC ==========

@router.get("/pac", response_class=HTMLResponse)
async def pac_page(
    request: Request,
    db: AsyncSession = Depends(get_db),
    usuario: User = Depends(optional_current_active_user)
):
    """Página do PAC."""
    if not usuario:
        return RedirectResponse(url="/login", status_code=303)

    result = await db.execute(select(PAC).filter(PAC.ano == 2025))
    itens = result.scalars().all()

    valor_total = 0.0
    for item in itens:
        if item.valor_previsto:
            try:
                clean_val = item.valor_previsto.replace('R$', '').replace(' ', '').replace('.', '').replace(',', '.')
                valor_total += float(clean_val)
            except (ValueError, AttributeError):
                continue

    valor_total_fmt = f"R$ {valor_total:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")

    return templates.TemplateResponse(
        "pages/pac.html",
        {
            "request": request,
            "usuario": usuario,
            "page": "pac",
            "page_title": "PAC 2025",
            "itens": itens,
            "valor_total": valor_total_fmt,
            "total_itens": len(itens)
        }
    )


# ========== CONFIGURAÇÕES ==========

@router.get("/configuracoes", response_class=HTMLResponse)
async def configuracoes_page(
    request: Request,
    db: AsyncSession = Depends(get_db),
    usuario: User = Depends(optional_current_active_user)
):
    """Página de configurações."""
    if not usuario:
        return RedirectResponse(url="/login", status_code=303)

    modelos_lista = [
        "allenai/molmo-2-8b:free",
        "arcee-ai/trinity-large-preview:free",
        "arcee-ai/trinity-mini:free",
        "cognitivecomputations/dolphin-mistral-24b-venice-edition:free",
        "deepseek/deepseek-r1-0528:free",
        "google/gemma-3-12b-it:free",
        "google/gemma-3-27b-it:free",
        "meta-llama/llama-3.3-70b-instruct:free",
        "mistralai/mistral-small-3.1-24b-instruct:free",
        "nvidia/nemotron-3-nano-30b-a3b:free",
        "nousresearch/hermes-3-llama-3.1-405b:free",
        "openai/gpt-oss-120b:free",
        "openai/gpt-oss-20b:free",
        "qwen/qwen3-4b:free",
        "qwen/qwen3-next-80b-a3b-instruct:free",
        "tngtech/deepseek-r1t-chimera:free",
        "tngtech/deepseek-r1t2-chimera:free",
        "tngtech/tng-r1t-chimera:free",
        "upstage/solar-pro-3:free",
        "liquid/lfm-2.5-1.2b-thinking:free"
    ]
    
    online_models = await fetch_online_models()
    
    modelos_ia = []
    for nome in sorted(modelos_lista):
        modelos_ia.append({
            "nome": nome,
            "online": nome in online_models
        })
    modelo_default = "arcee-ai/trinity-mini:free"
    return templates.TemplateResponse(
        "pages/configuracoes.html",
        {
            "request": request,
            "usuario": usuario,
            "page": "configuracoes",
            "page_title": "Configurações",
            "modelos_ia": modelos_ia,
            "modelo_default": modelo_default
        }
    )


# ========== MANUAL ==========

@router.get("/manual", response_class=HTMLResponse)
async def manual_page(
    request: Request,
    usuario: User = Depends(optional_current_active_user)
):
    """Página do Manual do Sistema."""
    if not usuario:
        return RedirectResponse(url="/login", status_code=303)

    return templates.TemplateResponse(
        "pages/manual.html",
        {
            "request": request,
            "usuario": usuario,
            "page": "manual",
            "page_title": "Manual do Sistema"
        }
    )


# ========== LISTAGEM UNIFICADA DE ARTEFATOS ==========

@router.get("/artefatos", response_class=HTMLResponse)
async def listar_todos_artefatos(
    request: Request,
    db: AsyncSession = Depends(get_db),
    usuario: User = Depends(optional_current_active_user)
):
    """Lista TODOS os artefatos de TODOS os projetos do usuário com navegação por abas."""
    if not usuario:
        return RedirectResponse(url="/login", status_code=303)

    # Eager load usuario relationship
    res = await db.execute(
        select(Projeto)
        .filter(Projeto.usuario_id == usuario.id)
        .options(selectinload(Projeto.usuario))
    )
    projetos_usuario = res.scalars().all()
    projeto_ids = [p.id for p in projetos_usuario]

    todos_artefatos = []
    artefatos_dfd = []
    artefatos_etp = []
    artefatos_tr = []
    artefatos_riscos = []
    artefatos_edital = []
    artefatos_pesquisa_precos = []

    async def fetch_and_process(Model, type_key, label, full_label, color, target_list):
        if not projeto_ids:
            return
        res = await db.execute(select(Model).filter(Model.projeto_id.in_(projeto_ids)))
        items = res.scalars().all()
        for item in items:
            projeto = next((p for p in projetos_usuario if p.id == item.projeto_id), None)
            if projeto:
                status = item.status or "rascunho"
                if status.lower() == 'salvo':
                    status = 'rascunho'

                extra_data = {}
                if type_key == "pesquisa-precos":
                    itens_cotados = item.itens_cotados or []
                    quantidade = len(itens_cotados)
                    valor_total = 0.0
                    for ic in itens_cotados:
                        if isinstance(ic, dict):
                            valor_unitario = ic.get('valor_unitario', 0) or ic.get('preco_unitario', 0) or 0
                            qtd = ic.get('quantidade', 1) or 1
                            try:
                                if isinstance(valor_unitario, str):
                                    valor_unitario = float(valor_unitario.replace('R$', '').replace('.', '').replace(',', '.').strip())
                                valor_total += float(valor_unitario) * float(qtd)
                            except (ValueError, AttributeError):
                                pass
                    
                    extra_data = {
                        "quantidade": quantidade,
                        "valor_total": valor_total
                    }

                artefato_dict = {
                    "id": item.id,
                    "tipo": type_key,
                    "tipo_label": label,
                    "tipo_completo": full_label,
                    "cor": color,
                    "projeto": projeto,
                    "status": status,
                    "data_atualizacao": item.data_atualizacao,
                    "data_criacao": item.data_criacao,
                    "versao": item.versao,
                    "gerado_por_ia": getattr(item, 'gerado_por_ia', False),
                    **extra_data
                }
                
                target_list.append(artefato_dict)
                todos_artefatos.append(artefato_dict)

    # Fetch all types
    await fetch_and_process(DFD, "dfd", "DFD", "Formalização da Demanda", "#3182CE", artefatos_dfd)
    await fetch_and_process(ETP, "etp", "ETP", "Estudo Técnico Preliminar", "#38A169", artefatos_etp)
    await fetch_and_process(TR, "tr", "TR", "Termo de Referência", "#D69E2E", artefatos_tr)
    await fetch_and_process(Riscos, "riscos", "PGR", "Gerenciamento de Riscos", "#E53E3E", artefatos_riscos)
    await fetch_and_process(Edital, "edital", "ED", "Edital de Licitação", "#805AD5", artefatos_edital)
    await fetch_and_process(PesquisaPrecos, "pesquisa-precos", "PP", "Pesquisa de Preços", "#319795", artefatos_pesquisa_precos)

    def ordenar_por_data(lista):
        return sorted(lista, key=lambda x: x['data_atualizacao'] or x['data_criacao'], reverse=True)

    todos_artefatos = ordenar_por_data(todos_artefatos)
    artefatos_dfd = ordenar_por_data(artefatos_dfd)
    artefatos_etp = ordenar_por_data(artefatos_etp)
    artefatos_tr = ordenar_por_data(artefatos_tr)
    artefatos_riscos = ordenar_por_data(artefatos_riscos)
    artefatos_edital = ordenar_por_data(artefatos_edital)
    artefatos_pesquisa_precos = ordenar_por_data(artefatos_pesquisa_precos)

    stats = {
        "total": len(todos_artefatos),
        "dfd": len(artefatos_dfd),
        "etp": len(artefatos_etp),
        "tr": len(artefatos_tr),
        "riscos": len(artefatos_riscos),
        "edital": len(artefatos_edital),
        "pesquisa_precos": len(artefatos_pesquisa_precos)
    }

    # Lista de modelos de IA (alfabética, com status online/offline)
    modelos_lista = [
        "allenai/molmo-2-8b:free",
        "arcee-ai/trinity-large-preview:free",
        "arcee-ai/trinity-mini:free",
        "cognitivecomputations/dolphin-mistral-24b-venice-edition:free",
        "deepseek/deepseek-r1-0528:free",
        "google/gemma-3-12b-it:free",
        "google/gemma-3-27b-it:free",
        "meta-llama/llama-3.3-70b-instruct:free",
        "mistralai/mistral-small-3.1-24b-instruct:free",
        "nvidia/nemotron-3-nano-30b-a3b:free",
        "nousresearch/hermes-3-llama-3.1-405b:free",
        "openai/gpt-oss-120b:free",
        "openai/gpt-oss-20b:free",
        "qwen/qwen3-4b:free",
        "qwen/qwen3-next-80b-a3b-instruct:free",
        "tngtech/deepseek-r1t-chimera:free",
        "tngtech/deepseek-r1t2-chimera:free",
        "tngtech/tng-r1t-chimera:free",
        "upstage/solar-pro-3:free",
        "liquid/lfm-2.5-1.2b-thinking:free"
    ]

    online_models = await fetch_online_models()

    modelos_ia = []
    for nome in sorted(modelos_lista):
        modelos_ia.append({
            "nome": nome,
            "online": nome in online_models
        })

    modelo_default = "arcee-ai/trinity-mini:free"

    return templates.TemplateResponse(
        "pages/artefatos_unificados.html",
        {
            "request": request,
            "usuario": usuario,
            "page": "artefatos",
            "page_title": "Artefatos",
            "artefatos_todos": todos_artefatos,
            "artefatos_dfd": artefatos_dfd,
            "artefatos_etp": artefatos_etp,
            "artefatos_tr": artefatos_tr,
            "artefatos_riscos": artefatos_riscos,
            "artefatos_edital": artefatos_edital,
            "artefatos_pesquisa_precos": artefatos_pesquisa_precos,
            "stats": stats,
            "projetos": projetos_usuario,
            "modelos_ia": modelos_ia,
            "modelo_default": modelo_default
        }
    )
