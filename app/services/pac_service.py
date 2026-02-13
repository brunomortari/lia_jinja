"""
Sistema LIA - PAC Service
==========================
Servico centralizado para operacoes com itens do PAC.
Elimina duplicacao de codigo entre ia.py, artefatos.py e views.py.

Autor: Equipe TRE-GO
Data: Janeiro 2026
"""

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import Dict, Any, List, Optional
import json
import logging

from app.models.pac import PAC
from app.models.projeto import Projeto

logger = logging.getLogger(__name__)


class PacService:
    """Servico para operacoes com itens do PAC"""

    @staticmethod
    async def get_itens_by_projeto(
        projeto: Optional[Projeto],
        db: AsyncSession
    ) -> List[Dict[str, Any]]:
        """
        Busca e serializa os itens do PAC vinculados a um projeto.

        Args:
            projeto: Objeto Projeto com campo itens_pac (JSON ou lista)
            db: Sessao async do banco de dados

        Returns:
            Lista de dicionarios com dados dos itens PAC, incluindo quantidade_projeto
        """
        if not projeto:
            return []

        itens_pac_data = []
        itens_config = PacService._parse_pac_items(projeto.itens_pac)

        for item_config in itens_config:
            pac_id = item_config.get('id')
            quantidade_projeto = item_config.get('quantidade')

            try:
                result = await db.execute(
                    select(PAC).filter(PAC.id == int(pac_id))
                )
                item = result.scalars().first()
                if item:
                    serialized = PacService._serialize_pac_item(item)
                    # Adicionar quantidade do projeto (ou usar a do PAC como fallback)
                    serialized['quantidade_projeto'] = quantidade_projeto if quantidade_projeto is not None else item.quantidade
                    itens_pac_data.append(serialized)
            except (ValueError, TypeError) as e:
                logger.warning(f"Erro ao buscar PAC id={pac_id}: {e}")
                continue

        return itens_pac_data

    @staticmethod
    async def get_itens_by_setor(
        setor: str,
        db: AsyncSession,
        ano: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        """
        Busca itens do PAC filtrados por setor (unidade tecnica).

        Args:
            setor: Nome do setor/unidade tecnica
            db: Sessao async do banco de dados
            ano: Ano do PAC (opcional, default=ano atual)

        Returns:
            Lista de dicionarios com dados dos itens PAC
        """
        if not setor:
            return []
            
        # Tenta filtrar por unidade tecnica que contenha o termo do setor
        # Ex: "TIC" busca itens de "Secretaria de TIC", "Coordenação TIC", etc.
        query = select(PAC).filter(PAC.unidade_tecnica.ilike(f"%{setor}%"))
        
        if ano:
            query = query.filter(PAC.ano == ano)
            
        result = await db.execute(query)
        itens = result.scalars().all()
        
        return [PacService._serialize_pac_item(item) for item in itens]

    @staticmethod
    def _parse_pac_items(itens_pac: Any) -> List[Dict[str, Any]]:
        """
        Converte o campo itens_pac em lista de objetos com id e quantidade.

        Suporta dois formatos:
        - Formato antigo (lista de IDs): [8, 9]
        - Formato novo (lista de objetos): [{"id": 8, "quantidade": 100}, {"id": 9, "quantidade": 50}]

        Args:
            itens_pac: Valor do campo itens_pac do projeto

        Returns:
            Lista de dicts com 'id' e 'quantidade' (quantidade pode ser None)
        """
        if not itens_pac:
            return []

        # Parse JSON string se necessário
        data = itens_pac
        if isinstance(itens_pac, str):
            try:
                data = json.loads(itens_pac)
            except json.JSONDecodeError:
                logger.warning(f"Falha ao parsear itens_pac JSON: {itens_pac}")
                return []

        if not isinstance(data, list):
            return []

        result = []
        for item in data:
            if isinstance(item, dict):
                # Formato novo: {"id": 8, "quantidade": 100}
                result.append({
                    'id': item.get('id'),
                    'quantidade': item.get('quantidade')
                })
            elif isinstance(item, (int, float)):
                # Formato antigo: apenas o ID
                result.append({
                    'id': int(item),
                    'quantidade': None
                })

        return result

    @staticmethod
    def _parse_pac_ids(itens_pac: Any) -> List[int]:
        """
        Converte o campo itens_pac em lista de IDs (para compatibilidade).

        Args:
            itens_pac: Valor do campo itens_pac do projeto

        Returns:
            Lista de IDs de itens PAC
        """
        items = PacService._parse_pac_items(itens_pac)
        return [item['id'] for item in items if item.get('id')]

    @staticmethod
    def _serialize_pac_item(item: PAC) -> Dict[str, Any]:
        """
        Serializa um item PAC para dicionario.

        Args:
            item: Objeto PAC do banco de dados

        Returns:
            Dicionario com dados do item
        """
        return {
            "id": item.id,
            "descricao": item.descricao,
            "detalhamento": item.detalhamento,
            "justificativa": item.justificativa,
            "valor_previsto": item.valor_previsto,
            "valor_por_item": item.valor_por_item,
            "quantidade": item.quantidade,
            "unidade": item.unidade,
            "objetivo": item.objetivo,
            "ano": item.ano
        }

    @staticmethod
    def serialize_pac_item_full(item: PAC) -> Dict[str, Any]:
        """
        Serializa um item PAC com todos os campos (para views).

        Args:
            item: Objeto PAC do banco de dados

        Returns:
            Dicionario completo com todos os campos do item
        """
        return {
            "id": item.id,
            "ano": item.ano,
            "tipo_pac": item.tipo_pac,
            "iniciativa": item.iniciativa,
            "objetivo": item.objetivo,
            "unidade_tecnica": item.unidade_tecnica,
            "unidade_administrativa": item.unidade_administrativa,
            "detalhamento": item.detalhamento,
            "descricao": item.descricao,
            "quantidade": item.quantidade,
            "unidade": item.unidade,
            "frequencia": item.frequencia,
            "valor_previsto": item.valor_previsto,
            "valor_por_item": item.valor_por_item,
            "justificativa": item.justificativa,
            "prioridade": item.prioridade,
            "catmat_catser": item.catmat_catser,
            "tipo_contratacao": item.tipo_contratacao,
            "fase": item.fase,
            "numero_contrato": item.numero_contrato,
            "vencimento_contrato": item.vencimento_contrato,
            "contratacao_continuada": item.contratacao_continuada,
        }


# Instancia global do servico (singleton pattern)
pac_service = PacService()
