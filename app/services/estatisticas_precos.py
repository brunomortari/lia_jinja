"""
Sistema LIA - Estatísticas de Preços
=====================================
Módulo centralizado para cálculo de estatísticas e detecção de outliers
em dados de preço obtidos via API Compras.gov.br.

Autor: Equipe TRE-GO
Data: Fevereiro 2026
"""

import statistics
import math
from typing import List, Tuple

from app.schemas.compras import ItemPreco, EstatisticasPreco


def calcular_percentil(valores: List[float], percentil: float) -> float:
    """
    Calcula o percentil de uma lista de valores usando interpolação linear.
    
    Args:
        valores: Lista de valores numéricos
        percentil: Percentil desejado (0-100)
        
    Returns:
        Valor do percentil calculado
    """
    n = len(valores)
    if n == 0:
        return 0.0
    
    valores_ordenados = sorted(valores)
    
    # Índice do percentil
    k = (n - 1) * percentil / 100
    f = math.floor(k)
    c = math.ceil(k)
    
    if f == c:
        return valores_ordenados[int(k)]
    
    # Interpolação linear
    return valores_ordenados[int(f)] * (c - k) + valores_ordenados[int(c)] * (k - f)


def detectar_outliers_iqr(
    itens: List[ItemPreco],
    multiplicador: float = 1.5
) -> Tuple[List[ItemPreco], float, float, float, float, float, int]:
    """
    Detecta outliers usando o método IQR (Intervalo Interquartil).
    
    Fórmula:
    - Q1 = 25º percentil
    - Q3 = 75º percentil
    - IQR = Q3 - Q1
    - Limite inferior = Q1 - (multiplicador * IQR)
    - Limite superior = Q3 + (multiplicador * IQR)
    - Outlier: valor < limite_inferior OU valor > limite_superior

    Args:
        itens: Lista de itens com preço
        multiplicador: Multiplicador para cálculo dos limites (default=1.5)
        
    Returns:
        Tuple com:
        - Lista de itens com flag is_outlier atualizado
        - Q1, Q3, IQR
        - Limite inferior, Limite superior
        - Quantidade de outliers
    """
    # Extrair preços válidos
    precos = [
        item.preco_unitario 
        for item in itens 
        if item.preco_unitario is not None and item.preco_unitario > 0
    ]
    
    if len(precos) < 4:  # Precisa de pelo menos 4 valores para calcular quartis
        # Marca todos como não-outlier se não há dados suficientes
        for item in itens:
            item.is_outlier = False
        return itens, 0, 0, 0, 0, 0, 0
    
    # Calcular quartis
    q1 = calcular_percentil(precos, 25)
    q3 = calcular_percentil(precos, 75)
    iqr = q3 - q1
    
    # Calcular limites
    limite_inferior = q1 - (multiplicador * iqr)
    limite_superior = q3 + (multiplicador * iqr)
    
    # Garantir que limite inferior não seja negativo para preços
    limite_inferior = max(0, limite_inferior)
    
    # Marcar outliers
    quantidade_outliers = 0
    for item in itens:
        if item.preco_unitario is not None and item.preco_unitario > 0:
            is_outlier = (item.preco_unitario < limite_inferior or 
                         item.preco_unitario > limite_superior)
            item.is_outlier = is_outlier
            if is_outlier:
                quantidade_outliers += 1
        else:
            item.is_outlier = False
    
    return itens, q1, q3, iqr, limite_inferior, limite_superior, quantidade_outliers


def calcular_estatisticas(
    itens: List[ItemPreco],
    incluir_outliers: bool = True
) -> EstatisticasPreco:
    """
    Calcula estatísticas descritivas dos preços.
    
    Args:
        itens: Lista de itens com preços
        incluir_outliers: Se False, exclui itens marcados como outlier
        
    Returns:
        Objeto EstatisticasPreco com todas as métricas calculadas
    """
    # Filtrar preços válidos
    if incluir_outliers:
        precos = [
            item.preco_unitario 
            for item in itens 
            if item.preco_unitario is not None and item.preco_unitario > 0
        ]
    else:
        precos = [
            item.preco_unitario 
            for item in itens 
            if item.preco_unitario is not None and item.preco_unitario > 0 and not item.is_outlier
        ]
    
    if not precos:
        return EstatisticasPreco(
            quantidade_registros=0,
            preco_minimo=None,
            preco_maximo=None,
            preco_medio=None,
            preco_mediana=None,
            desvio_padrao=None,
            coeficiente_variacao=None,
            q1=None,
            q3=None,
            iqr=None,
            limite_inferior=None,
            limite_superior=None,
            quantidade_outliers=0
        )
    
    preco_minimo = min(precos)
    preco_maximo = max(precos)
    preco_medio = statistics.mean(precos)
    preco_mediana = statistics.median(precos)
    
    # Quartis e IQR
    q1 = calcular_percentil(precos, 25) if len(precos) >= 4 else None
    q3 = calcular_percentil(precos, 75) if len(precos) >= 4 else None
    iqr = (q3 - q1) if q1 is not None and q3 is not None else None
    
    # Limites para outliers
    limite_inferior = None
    limite_superior = None
    if q1 is not None and iqr is not None:
        limite_inferior = max(0, q1 - 1.5 * iqr)
        limite_superior = q3 + 1.5 * iqr
    
    # Contar outliers
    quantidade_outliers = sum(1 for item in itens if item.is_outlier)
    
    # Desvio padrão (precisa de pelo menos 2 valores)
    desvio_padrao = None
    coeficiente_variacao = None
    
    if len(precos) >= 2:
        desvio_padrao = statistics.stdev(precos)
        # Coeficiente de Variação (CV) = (desvio padrão / média) * 100
        if preco_medio > 0:
            coeficiente_variacao = (desvio_padrao / preco_medio) * 100
    
    return EstatisticasPreco(
        quantidade_registros=len(precos),
        preco_minimo=round(preco_minimo, 4),
        preco_maximo=round(preco_maximo, 4),
        preco_medio=round(preco_medio, 4),
        preco_mediana=round(preco_mediana, 4),
        desvio_padrao=round(desvio_padrao, 4) if desvio_padrao else None,
        coeficiente_variacao=round(coeficiente_variacao, 2) if coeficiente_variacao else None,
        q1=round(q1, 4) if q1 is not None else None,
        q3=round(q3, 4) if q3 is not None else None,
        iqr=round(iqr, 4) if iqr is not None else None,
        limite_inferior=round(limite_inferior, 4) if limite_inferior is not None else None,
        limite_superior=round(limite_superior, 4) if limite_superior is not None else None,
        quantidade_outliers=quantidade_outliers
    )
