#!/usr/bin/env bash

set -euo pipefail

if ! command -v python3 >/dev/null 2>&1; then
    echo "Python 3 não foi encontrado. Instale o Python 3.10 ou superior." >&2
    exit 1
fi

if [ ! -d ".venv" ]; then
    echo "Criando o ambiente virtual..."
    python3 -m venv .venv
else
    echo "O ambiente virtual .venv já existe."
fi

PYTHON=".venv/bin/python"

echo "Atualizando o pip..."
"$PYTHON" -m pip install --upgrade pip

echo "Instalando o projeto e as dependências de desenvolvimento..."
"$PYTHON" -m pip install -e ".[dev]"

echo "Executando a análise estática..."
"$PYTHON" -m ruff check src tests

echo "Executando os testes automatizados..."
"$PYTHON" -m pytest

echo
echo "Projeto configurado e validado com sucesso!"
echo "Para realizar a coleta, execute:"
echo "$PYTHON -m g1_scraper.cli --term lgpd --max-pages 5 --page-size 10 --delay 1"

