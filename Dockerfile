# Sistema LIA - Dockerfile
# ========================

FROM python:3.11-slim

# Definir diretorio de trabalho
WORKDIR /app

# Instalar dependencias do sistema (incluindo libpq para PostgreSQL e WeasyPrint)
RUN apt-get update && apt-get install -y \
    gcc \
    libpq-dev \
    libpango-1.0-0 \
    libpangocairo-1.0-0 \
    libgdk-pixbuf-2.0-0 \
    libffi-dev \
    shared-mime-info \
    libcairo2 \
    libpangoft2-1.0-0 \
    && rm -rf /var/lib/apt/lists/*

# Copiar requirements primeiro (para cache do Docker)
COPY requirements.txt .

# Instalar dependencias Python
RUN pip install --no-cache-dir -r requirements.txt

# Copiar codigo da aplicacao
COPY . .

# Criar diretorio static se nao existir
RUN mkdir -p static

# Garantir permissao de execucao no entrypoint
RUN chmod +x entrypoint.sh

# Criar usuario nao-root
RUN useradd -m appuser && chown -R appuser:appuser /app
USER appuser

# Expor porta
EXPOSE 8000

# Usar entrypoint para inicializar dados
ENTRYPOINT ["./entrypoint.sh"]
