from fastapi import APIRouter, Query
from typing import List, Optional
from app.routers.views.home_views import fetch_licitacao_news

router = APIRouter(prefix="/api/news", tags=["news"])

@router.get("/", response_model=List[dict])
async def get_news(q: Optional[str] = Query(None, description="Busca por termo")):
    """
    Retorna notícias sobre Licitações e IA (sempre retorna pelo menos 2 notícias).
    Filtra apenas conteúdo indesejado (corrupção, fraude, escândalo).
    """
    noticias = await fetch_licitacao_news()
    
    # Exclui apenas conteúdo realmente negativo
    exclui = ["corrupção", "fraude", "escândalo", "crime"]
    
    filtradas = []
    for n in noticias:
        titulo = n["titulo"].lower()
        
        # Pula se contém termos de exclusão
        if any(e in titulo for e in exclui):
            continue
        
        # Se houver busca específica, filtra por termo
        if q:
            if q.lower() in titulo:
                filtradas.append(n)
        else:
            # Sem filtro de busca, inclui tudo que passou na exclusão
            filtradas.append(n)
    
    # Se ficou vazio, retorna as originais sem os termos de exclusão
    if not filtradas:
        filtradas = [n for n in noticias if not any(e in n["titulo"].lower() for e in exclui)]
    
    # Garante pelo menos 2 notícias
    return filtradas if filtradas else noticias[:2]
