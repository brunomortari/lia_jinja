"""
Serviço para consumir a API de Dados Abertos do Compras.gov.br
Versão 2.0 - Com detecção de outliers (IQR) e integração PNCP
"""
import httpx
from typing import Optional, List, Dict, Any, Tuple
from datetime import datetime
import logging

from app.schemas.compras import (
    ItemPreco, ItemCatalogo, PdmMaterial,
    EstatisticasPreco, RespostaPrecos, TipoCatalogo,
    ContratacaoPNCP, ItemContratacao, ResultadoItemContratacao, DetalhesContratacao,
    DetalheItemPNCP
)
from .estatisticas_precos import calcular_estatisticas, detectar_outliers_iqr, calcular_percentil

logger = logging.getLogger(__name__)

BASE_URL = "https://dadosabertos.compras.gov.br"

# Timeout configuração (aumentado para APIs lentas)
TIMEOUT_CONFIG = httpx.Timeout(300.0, connect=30.0, read=300.0)


class ComprasGovService:
    """Serviço para interagir com a API de Dados Abertos do Compras.gov.br"""
    
    def __init__(self):
        self.base_url = BASE_URL
        self.client = None
    
    async def _get_client(self) -> httpx.AsyncClient:
        """Retorna um cliente HTTP assíncrono"""
        if self.client is None or self.client.is_closed:
            self.client = httpx.AsyncClient(timeout=TIMEOUT_CONFIG)
        return self.client
    
    async def close(self):
        """Fecha o cliente HTTP"""
        if self.client and not self.client.is_closed:
            await self.client.aclose()
    
    async def _fazer_requisicao(
        self, 
        endpoint: str, 
        params: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Faz uma requisição GET para a API"""
        client = await self._get_client()
        url = f"{self.base_url}{endpoint}"
        
        # Remove parâmetros None
        params = {k: v for k, v in params.items() if v is not None}
        
        logger.info(f"Requisição: {url} com params: {params}")
        
        try:
            response = await client.get(url, params=params)
            response.raise_for_status()
            return response.json()
        except httpx.HTTPStatusError as e:
            logger.error(f"Erro HTTP: {e.response.status_code} - {e.response.text}")
            raise
        except Exception as e:
            logger.error(f"Erro na requisição: {str(e)}")
            raise
    
    async def consultar_precos_material(
        self,
        codigo_catmat: int,
        estado: Optional[str] = None,
        codigo_uasg: Optional[str] = None,
        pagina: int = 1,
        tamanho_pagina: int = 100,
        codigo_classe: Optional[int] = None
    ) -> Tuple[List[ItemPreco], int, int]:
        """
        Consulta preços praticados para materiais (CATMAT)
        
        Returns:
            Tuple contendo lista de itens, total de registros e total de páginas
        """
        endpoint = "/modulo-pesquisa-preco/1_consultarMaterial"
        params = {
            "codigoItemCatalogo": codigo_catmat,
            "estado": estado,
            "codigoUasg": codigo_uasg,
            "pagina": pagina,
            "tamanhoPagina": tamanho_pagina,
            "codigoClasse": codigo_classe,
            "dataResultado": True
        }
        
        data = await self._fazer_requisicao(endpoint, params)
        
        itens = []
        resultado = data.get("resultado", [])
        
        for item_data in resultado:
            try:
                item = ItemPreco(**item_data)
                itens.append(item)
            except Exception as e:
                logger.warning(f"Erro ao parsear item: {e}")
                continue
        
        total_registros = data.get("totalRegistros", 0)
        total_paginas = data.get("totalPaginas", 0)
        
        return itens, total_registros, total_paginas
    
    async def consultar_precos_servico(
        self,
        codigo_catserv: int,
        estado: Optional[str] = None,
        codigo_uasg: Optional[str] = None,
        pagina: int = 1
    ) -> Tuple[List[ItemPreco], int, int]:
        """
        Consulta preços praticados para serviços (CATSERV)
        
        Returns:
            Tuple contendo lista de itens, total de registros e total de páginas
        """
        endpoint = "/modulo-pesquisa-preco/3_consultarServico"
        params = {
            "codigoItemCatalogo": codigo_catserv,
            "estado": estado,
            "codigoUasg": codigo_uasg,
            "pagina": pagina,
            "dataResultado": True
        }
        
        data = await self._fazer_requisicao(endpoint, params)
        
        itens = []
        resultado = data.get("resultado", [])
        
        for item_data in resultado:
            try:
                item = ItemPreco(**item_data)
                itens.append(item)
            except Exception as e:
                logger.warning(f"Erro ao parsear item: {e}")
                continue
        
        total_registros = data.get("totalRegistros", 0)
        total_paginas = data.get("totalPaginas", 0)
        
        return itens, total_registros, total_paginas
    
    async def consultar_item_material(
        self,
        codigo_item: int
    ) -> Optional[ItemCatalogo]:
        """Consulta informações de um item de material pelo código CATMAT"""
        endpoint = "/modulo-material/4_consultarItemMaterial"
        params = {
            "codigoItem": codigo_item,
            "pagina": 1,
            "tamanhoPagina": 10  # API exige mínimo de 10
        }
        
        try:
            data = await self._fazer_requisicao(endpoint, params)
            resultado = data.get("resultado", [])
            
            if resultado:
                return ItemCatalogo(**resultado[0])
            return None
        except Exception as e:
            logger.error(f"Erro ao consultar item: {e}")
            return None
    
    async def consultar_pdm_material(
        self,
        codigo_pdm: Optional[int] = None,
        codigo_classe: Optional[int] = None,
        pagina: int = 1
    ) -> List[PdmMaterial]:
        """Consulta PDMs (Padrão Descritivo de Material)"""
        endpoint = "/modulo-material/3_consultarPdmMaterial"
        params = {
            "codigoPdm": codigo_pdm,
            "codigoClasse": codigo_classe,
            "pagina": pagina,
            "statusPdm": True
        }
        
        data = await self._fazer_requisicao(endpoint, params)
        
        pdms = []
        resultado = data.get("resultado", [])
        
        for pdm_data in resultado:
            try:
                pdm = PdmMaterial(**pdm_data)
                pdms.append(pdm)
            except Exception as e:
                logger.warning(f"Erro ao parsear PDM: {e}")
                continue
        
        return pdms
    
    async def consultar_itens_por_pdm(
        self,
        codigo_pdm: int,
        pagina: int = 1,
        tamanho_pagina: int = 100
    ) -> Tuple[List[ItemCatalogo], int]:
        """
        Consulta todos os itens de uma família PDM
        
        Returns:
            Tuple com lista de itens e total de registros
        """
        endpoint = "/modulo-material/4_consultarItemMaterial"
        params = {
            "codigoPdm": codigo_pdm,
            "pagina": pagina,
            "tamanhoPagina": tamanho_pagina,
            "statusItem": True
        }
        
        data = await self._fazer_requisicao(endpoint, params)
        
        itens = []
        resultado = data.get("resultado", [])
        
        for item_data in resultado:
            try:
                item = ItemCatalogo(**item_data)
                itens.append(item)
            except Exception as e:
                logger.warning(f"Erro ao parsear item: {e}")
                continue
        
        total_registros = data.get("totalRegistros", 0)
        
        return itens, total_registros
    
    async def consultar_todos_precos_material(
        self,
        codigo_catmat: int,
        estado: Optional[str] = None,
        codigo_classe: Optional[int] = None,
        max_paginas: int = 3
    ) -> Tuple[List[ItemPreco], int]:
        """
        Consulta preços de um material, paginando automaticamente

        Returns:
            Tuple com lista completa de itens e total de registros
        """
        todos_itens = []
        pagina_atual = 1
        total_registros = 0

        while pagina_atual <= max_paginas:
            itens, total, total_paginas = await self.consultar_precos_material(
                codigo_catmat=codigo_catmat,
                estado=estado,
                pagina=pagina_atual,
                tamanho_pagina=10,
                codigo_classe=codigo_classe
            )
            
            if pagina_atual == 1:
                total_registros = total
            
            todos_itens.extend(itens)
            
            if pagina_atual >= total_paginas or not itens:
                break
            
            pagina_atual += 1
        
        return todos_itens, total_registros
    
    async def consultar_precos_familia_pdm(
        self,
        codigo_catmat: int,
        estado: Optional[str] = None,
        max_paginas: int = 3
    ) -> Tuple[List[ItemPreco], int, int, str]:
        """
        Consulta preços de toda a família PDM de um item
        
        Returns:
            Tuple com lista de itens, total de registros, código PDM e nome PDM
        """
        # Primeiro, buscar informações do item para descobrir o PDM
        item_info = await self.consultar_item_material(codigo_catmat)
        
        if not item_info or not item_info.codigo_pdm:
            # Se não encontrar PDM, retorna pesquisa normal
            itens, total = await self.consultar_todos_precos_material(
                codigo_catmat=codigo_catmat,
                estado=estado
            )
            return itens, total, 0, ""
        
        codigo_pdm = item_info.codigo_pdm
        nome_pdm = item_info.nome_pdm or ""
        
        # Buscar todos os itens da família PDM
        itens_pdm, _ = await self.consultar_itens_por_pdm(
            codigo_pdm=codigo_pdm,
            tamanho_pagina=500
        )
        
        # Para cada item da família, buscar preços
        todos_itens = []
        codigos_pesquisados = set()
        
        for item in itens_pdm:
            if item.codigo_item and item.codigo_item not in codigos_pesquisados:
                codigos_pesquisados.add(item.codigo_item)
                try:
                    itens_preco, _, _ = await self.consultar_precos_material(
                        codigo_catmat=item.codigo_item,
                        estado=estado,
                        pagina=1,
                        tamanho_pagina=10
                    )
                    todos_itens.extend(itens_preco)
                except Exception as e:
                    logger.warning(f"Erro ao buscar preços do item {item.codigo_item}: {e}")
                    continue
        
        return todos_itens, len(todos_itens), codigo_pdm, nome_pdm

    async def pesquisar_itens_por_descricao(
        self,
        termo: str,
        tamanho_pagina: int = 10
    ) -> List[ItemCatalogo]:
        """
        Pesquisa itens no catálogo de materiais pela descrição.
        Endpoint: /modulo-material/4_consultarItemMaterial
        """
        endpoint = "/modulo-material/4_consultarItemMaterial"
        params = {
            "descricaoItem": termo,
            "pagina": 1,
            "tamanhoPagina": tamanho_pagina,
            "statusItem": True
        }
        
        try:
            data = await self._fazer_requisicao(endpoint, params)
            resultado = data.get("resultado", [])
            
            itens = []
            for item_data in resultado:
                try:
                    item = ItemCatalogo(**item_data)
                    itens.append(item)
                except Exception as e:
                    logger.warning(f"Erro ao parsear item do catálogo: {e}")
                    continue
            
            return itens
        except Exception as e:
            logger.error(f"Erro ao pesquisar itens por descrição '{termo}': {e}")
            return []

    # ============================================================
    # Métodos PNCP - Portal Nacional de Contratações Públicas
    # ============================================================
    
    async def consultar_contratacao_pncp(
        self,
        id_compra: str
    ) -> Optional[ContratacaoPNCP]:
        """
        Consulta dados gerais de uma contratação no PNCP pelo idCompra
        Endpoint: /modulo-contratacoes/1.1_consultarContratacoes_PNCP_14133_Id
        """
        endpoint = "/modulo-contratacoes/1.1_consultarContratacoes_PNCP_14133_Id"
        params = {
            "tipo": "idCompra",
            "codigo": id_compra,
            "pagina": 1,
            "tamanhoPagina": 10
        }
        
        try:
            data = await self._fazer_requisicao(endpoint, params)
            resultado = data.get("resultado", [])
            
            if resultado:
                return ContratacaoPNCP(**resultado[0])
            return None
        except Exception as e:
            logger.error(f"Erro ao consultar contratação PNCP: {e}")
            return None
    
    async def consultar_itens_contratacao_pncp(
        self,
        id_compra: str
    ) -> List[ItemContratacao]:
        """
        Consulta itens de uma contratação no PNCP
        Endpoint: /modulo-contratacoes/2.1_consultarItensContratacoes_PNCP_14133_Id
        """
        endpoint = "/modulo-contratacoes/2.1_consultarItensContratacoes_PNCP_14133_Id"
        params = {
            "tipo": "idCompra",
            "codigo": id_compra,
            "pagina": 1,
            "tamanhoPagina": 100
        }
        
        try:
            data = await self._fazer_requisicao(endpoint, params)
            resultado = data.get("resultado", [])
            
            itens = []
            for item_data in resultado:
                try:
                    item = ItemContratacao(**item_data)
                    itens.append(item)
                except Exception as e:
                    logger.warning(f"Erro ao parsear item contratação: {e}")
                    continue
            
            return itens
        except Exception as e:
            logger.error(f"Erro ao consultar itens contratação PNCP: {e}")
            return []
    
    async def consultar_resultados_contratacao_pncp(
        self,
        id_compra: str
    ) -> List[ResultadoItemContratacao]:
        """
        Consulta resultados/vencedores de uma contratação no PNCP
        Endpoint: /modulo-contratacoes/3.1_consultarResultadoItensContratacoes_PNCP_14133_Id
        """
        endpoint = "/modulo-contratacoes/3.1_consultarResultadoItensContratacoes_PNCP_14133_Id"
        params = {
            "tipo": "idCompra",
            "codigo": id_compra,
            "pagina": 1,
            "tamanhoPagina": 100
        }
        
        try:
            data = await self._fazer_requisicao(endpoint, params)
            resultado = data.get("resultado", [])
            
            resultados = []
            for res_data in resultado:
                try:
                    res = ResultadoItemContratacao(**res_data)
                    resultados.append(res)
                except Exception as e:
                    logger.warning(f"Erro ao parsear resultado contratação: {e}")
                    continue
            
            return resultados
        except Exception as e:
            logger.error(f"Erro ao consultar resultados contratação PNCP: {e}")
            return []
    
    async def consultar_detalhes_contratacao(
        self,
        id_compra: str,
        codigo_item_filtro: Optional[int] = None
    ) -> DetalhesContratacao:
        """
        Consulta todos os detalhes de uma contratação consolidando os 3 endpoints PNCP

        Args:
            id_compra: ID da compra no PNCP
            codigo_item_filtro: Se fornecido, filtra itens e resultados por este código de catálogo
        """
        try:
            # Buscar dados gerais
            contratacao = await self.consultar_contratacao_pncp(id_compra)

            if not contratacao:
                return DetalhesContratacao(
                    encontrado=False,
                    id_compra=id_compra,
                    mensagem=f"Contratação {id_compra} não encontrada no PNCP"
                )

            # Construir URL do PNCP
            url_pncp = contratacao.url_pncp_construida

            # Buscar itens
            itens = await self.consultar_itens_contratacao_pncp(id_compra)

            # Buscar resultados/vencedores
            resultados = await self.consultar_resultados_contratacao_pncp(id_compra)

            # Filtrar por código de catálogo se especificado
            if codigo_item_filtro:
                itens_filtrados = [
                    item for item in itens
                    if item.codigo_item_catalogo == codigo_item_filtro
                ]
                # Pegar números dos itens filtrados para filtrar resultados
                numeros_itens = {item.numero_item for item in itens_filtrados if item.numero_item}
                resultados_filtrados = [
                    res for res in resultados
                    if res.numero_item in numeros_itens
                ]
                itens = itens_filtrados
                resultados = resultados_filtrados

            return DetalhesContratacao(
                encontrado=True,
                id_compra=id_compra,
                url_pncp=url_pncp,
                contratacao=contratacao,
                itens=itens,
                resultados=resultados
            )

        except Exception as e:
            logger.error(f"Erro ao consultar detalhes contratação: {e}")
            return DetalhesContratacao(
                encontrado=False,
                id_compra=id_compra,
                mensagem=f"Erro ao buscar contratação: {str(e)}"
            )

    async def enriquecer_itens_com_pncp(
        self,
        itens: List[ItemPreco],
        max_itens: int = 50
    ) -> List[ItemPreco]:
        """
        Enriquece os itens de preço com detalhes do PNCP.
        Busca informações adicionais para cada idCompra único.

        Args:
            itens: Lista de itens de preço
            max_itens: Máximo de compras únicas a buscar detalhes (para evitar muitas requisições)

        Returns:
            Lista de itens com campo detalhes_pncp preenchido
        """
        # Coletar idCompras únicos
        id_compras_unicos = list(set(
            item.id_compra for item in itens
            if item.id_compra is not None
        ))[:max_itens]

        if not id_compras_unicos:
            return itens

        logger.info(f"Enriquecendo {len(id_compras_unicos)} compras com dados PNCP")

        # Cache para armazenar detalhes já buscados
        cache_detalhes: Dict[str, Dict[str, Any]] = {}

        for id_compra in id_compras_unicos:
            try:
                # Buscar dados da contratação
                contratacao = await self.consultar_contratacao_pncp(id_compra)
                itens_contratacao = await self.consultar_itens_contratacao_pncp(id_compra)
                resultados = await self.consultar_resultados_contratacao_pncp(id_compra)

                # Indexar itens e resultados por número do item
                itens_por_numero = {i.numero_item: i for i in itens_contratacao if i.numero_item}
                resultados_por_numero = {r.numero_item: r for r in resultados if r.numero_item}

                cache_detalhes[id_compra] = {
                    "contratacao": contratacao,
                    "itens": itens_por_numero,
                    "resultados": resultados_por_numero
                }
            except Exception as e:
                logger.warning(f"Erro ao buscar detalhes PNCP para {id_compra}: {e}")
                continue

        # Enriquecer cada item com os detalhes do PNCP
        for item in itens:
            if item.id_compra and item.id_compra in cache_detalhes:
                dados = cache_detalhes[item.id_compra]
                contratacao = dados["contratacao"]
                numero_item = item.numero_item_compra

                # Buscar item e resultado correspondente
                item_pncp = dados["itens"].get(numero_item) if numero_item else None
                resultado_pncp = dados["resultados"].get(numero_item) if numero_item else None

                # Construir URL do PNCP
                url_pncp = contratacao.url_pncp_construida if contratacao else None

                # Montar detalhes enriquecidos
                detalhes = DetalheItemPNCP(
                    modalidade_nome=contratacao.modalidade_nome if contratacao else None,
                    situacao_compra=contratacao.situacao_compra_nome if contratacao else None,
                    objeto_compra=contratacao.objeto_compra if contratacao else None,
                    srp=contratacao.srp if contratacao else None,
                    quantidade_licitada=item_pncp.quantidade if item_pncp else None,
                    valor_unitario_estimado=item_pncp.valor_unitario_estimado if item_pncp else None,
                    valor_total_estimado=item_pncp.valor_total_estimado if item_pncp else None,
                    marca=resultado_pncp.marca if resultado_pncp else None,
                    modelo=resultado_pncp.modelo if resultado_pncp else None,
                    fabricante=resultado_pncp.fabricante if resultado_pncp else None,
                    aplicacao_margem_preferencia=resultado_pncp.aplicacao_margem_preferencia if resultado_pncp else None,
                    aplicacao_beneficio_meepp=resultado_pncp.aplicacao_beneficio_meepp if resultado_pncp else None,
                    porte_fornecedor=resultado_pncp.porte_fornecedor_nome if resultado_pncp else None,
                    url_pncp=url_pncp,
                    link_sistema_origem=contratacao.link_sistema_origem if contratacao else None
                )

                item.detalhes_pncp = detalhes

        return itens


# Service instance
compras_service = ComprasGovService()
