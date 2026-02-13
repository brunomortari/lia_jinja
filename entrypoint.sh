#!/bin/bash 
set -e

echo "=========================================="
echo "Sistema LIA - Inicializando..."
echo "=========================================="

# Aguardar banco de dados estar pronto
echo "Aguardando banco de dados..."
sleep 5

# Executar migrações Alembic
echo "Executando migrações de banco..."
alembic upgrade head

# Executar script de inicializacao
echo "Executando inicializacao de dados..."
# Executa como modulo para reconhecer os imports relativos dentro de 'app'
python -m app.init_data

# Iniciar aplicacao com hot-reload
echo "Iniciando aplicacao..."
exec uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
