"""
Sistema LIA - Service de Exportação PDF
=========================================
Gera PDFs dos artefatos de forma dinâmica usando WeasyPrint.

Autor: Equipe TRE-GO
Data: Janeiro 2026
"""

from io import BytesIO
from datetime import datetime
from jinja2 import Template

try:
    from weasyprint import HTML, CSS
    HAS_WEASYPRINT = True
except ImportError:
    HAS_WEASYPRINT = False


# Template HTML genérico para PDF
HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="pt-BR">
<head>
    <meta charset="UTF-8">
    <title>{{ titulo }}</title>
    <style>
        @page {
            size: A4;
            margin: 2.5cm 2cm;
            @bottom-right {
                content: "Página " counter(page) " de " counter(pages);
                font-size: 9pt;
                color: #666;
            }
        }
        
        body {
            font-family: 'Times New Roman', serif;
            font-size: 12pt;
            line-height: 1.6;
            color: #000;
        }
        
        .header {
            text-align: center;
            border-bottom: 3px solid #003366;
            padding-bottom: 15px;
            margin-bottom: 30px;
        }
        
        .header h1 {
            margin: 0;
            font-size: 20pt;
            font-weight: bold;
            color: #003366;
            text-transform: uppercase;
        }
        
        .header h2 {
            margin: 10px 0 5px 0;
            font-size: 16pt;
            font-weight: bold;
            color: #333;
        }
        
        .metadata {
            font-size: 10pt;
            color: #666;
            margin-top: 10px;
        }
        
        .metadata strong {
            color: #333;
        }
        
        .secao {
            margin-top: 25px;
            page-break-inside: avoid;
        }
        
        .label {
            font-size: 13pt;
            font-weight: bold;
            color: #003366;
            margin-bottom: 8px;
            border-bottom: 1px solid #ccc;
            padding-bottom: 3px;
        }
        
        .valor {
            margin-left: 15px;
            margin-top: 10px;
            text-align: justify;
            white-space: pre-wrap;
            word-wrap: break-word;
        }
        
        .vazio {
            color: #999;
            font-style: italic;
        }
        
        .footer {
            margin-top: 40px;
            padding-top: 15px;
            border-top: 1px solid #ccc;
            font-size: 9pt;
            color: #666;
            text-align: center;
        }
    </style>
</head>
<body>
    <div class="header">
        <h1>Justiça Eleitoral</h1>
        <h2>{{ titulo }}</h2>
        <div class="metadata">
            <p>
                <strong>Projeto:</strong> {{ projeto.titulo }}<br>
                <strong>Versão:</strong> {{ artefato.versao }}<br>
                <strong>Status:</strong> {{ artefato.status|title }}<br>
                <strong>Data de Emissão:</strong> {{ data_emissao }}
            </p>
        </div>
    </div>
    
    {% for campo, conf in campos_config.items() %}
    <div class="secao">
        <div class="label">{{ conf.label }}</div>
        {% set valor = artefato[campo] %}
        {% if valor %}
            <div class="valor">{{ valor }}</div>
        {% else %}
            <div class="valor vazio">[Não preenchido]</div>
        {% endif %}
    </div>
    {% endfor %}
    
    <div class="footer">
        Documento gerado automaticamente pelo Sistema LIA em {{ data_emissao }}
    </div>
</body>
</html>
"""


def gerar_pdf_artefato(artefato, tipo_artefato: str, campos_config: dict, titulo: str, projeto) -> BytesIO:
    """
    Gera PDF de um artefato de forma dinâmica.
    
    Args:
        artefato: Objeto do modelo (DFD, ETP, TR, Riscos, Edital, PesquisaPrecos)
        tipo_artefato: Tipo do artefato (ex: 'dfd', 'etp')
        campos_config: Dicionário de configuração dos campos (ex: DFD_CAMPOS_CONFIG)
        titulo: Título do documento (ex: 'Documento de Formalização da Demanda')
        projeto: Objeto Projeto relacionado
        
    Returns:
        BytesIO: Buffer com o PDF gerado
        
    Raises:
        ImportError: Se WeasyPrint não estiver instalado
    """
    if not HAS_WEASYPRINT:
        raise ImportError(
            "WeasyPrint não está instalado. "
            "Instale com: pip install weasyprint"
        )
    
    # Converter artefato para dict para facilitar acesso no template
    artefato_dict = artefato.to_dict() if hasattr(artefato, 'to_dict') else {
        c.name: getattr(artefato, c.name) for c in artefato.__table__.columns
    }
    
    # Preparar contexto para o template
    context = {
        'titulo': titulo,
        'projeto': projeto,
        'artefato': artefato_dict,
        'campos_config': campos_config,
        'data_emissao': datetime.now().strftime('%d/%m/%Y às %H:%M'),
    }
    
    # Renderizar template
    template = Template(HTML_TEMPLATE)
    html_content = template.render(**context)
    
    # Gerar PDF
    pdf_buffer = BytesIO()
    HTML(string=html_content).write_pdf(pdf_buffer)
    pdf_buffer.seek(0)
    
    return pdf_buffer


def gerar_nome_arquivo_pdf(tipo_artefato: str, projeto_id: int, versao: int) -> str:
    """
    Gera nome padronizado para o arquivo PDF.
    
    Args:
        tipo_artefato: Tipo do artefato (ex: 'dfd', 'etp')
        projeto_id: ID do projeto
        versao: Versão do artefato
        
    Returns:
        str: Nome do arquivo (ex: 'DFD_Projeto_1_v1.pdf')
    """
    tipo_upper = tipo_artefato.upper().replace('_', '')
    timestamp = datetime.now().strftime('%Y%m%d')
    return f"{tipo_upper}_Projeto_{projeto_id}_v{versao}_{timestamp}.pdf"
