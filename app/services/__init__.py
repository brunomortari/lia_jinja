"""
Sistema LIA - Services Package
===============================
Camada de serviços que encapsula lógica de negócio e integração com APIs externas.

Serviços Disponíveis:
- PacService: Operações com itens do PAC (Plano de Aceleração do Crescimento)
- ComprasGovService: Integração com API de Dados Abertos do Compras.gov.br
- Funções de estatísticas de preços: Cálculo e detecção de outliers
- ArtefatosService: Mapeamento de campos IA para modelos do banco
- PDFService: Geração de PDFs de artefatos
- DeepResearchService: [NOT IMPLEMENTED] Pesquisa aprofundada com APIs externas

Padrão de Importação:
Importe os singletons e classes diretamente dos módulos:
- from app.services.pac_service import pac_service, PacService
- from app.services.compras_service import compras_service, ComprasGovService
- from app.services.estatisticas_precos import calcular_estatisticas, detectar_outliers_iqr
- from app.services.artefatos_service import mapear_campos_artefato
- from app.services.pdf_service import gerar_pdf_artefato

Autor: Equipe TRE-GO
Data: Fevereiro 2026
"""

# Re-exports para compatibilidade (padrão de imports antigos)
from .pac_service import pac_service, PacService

__all__ = [
    "pac_service",
    "PacService",
]
