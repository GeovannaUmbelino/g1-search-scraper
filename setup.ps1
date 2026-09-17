$ErrorActionPreference = "Stop"

function Invoke-Step {
    param(
        [string]$Message,
        [scriptblock]$Command
    )

    Write-Host "`n$Message" -ForegroundColor Cyan
    & $Command

    if ($LASTEXITCODE -ne 0) {
        throw "Falha durante: $Message"
    }
}

if (-not (Get-Command python -ErrorAction SilentlyContinue)) {
    throw "Python não foi encontrado. Instale o Python 3.10 ou superior e tente novamente."
}

if (-not (Test-Path ".venv")) {
    Invoke-Step "Criando o ambiente virtual..." {
        python -m venv .venv
    }
}
else {
    Write-Host "`nO ambiente virtual .venv já existe." -ForegroundColor Yellow
}

$Python = ".\.venv\Scripts\python.exe"

Invoke-Step "Atualizando o pip..." {
    & $Python -m pip install --upgrade pip
}

Invoke-Step "Instalando o projeto e as dependências de desenvolvimento..." {
    & $Python -m pip install -e ".[dev]"
}

Invoke-Step "Executando a análise estática..." {
    & $Python -m ruff check src tests
}

Invoke-Step "Executando os testes automatizados..." {
    & $Python -m pytest
}

Write-Host "`nProjeto configurado e validado com sucesso!" -ForegroundColor Green
Write-Host "Para realizar a coleta, execute:" -ForegroundColor Green
Write-Host "$Python -m g1_scraper.cli --term lgpd --max-pages 5 --page-size 10 --delay 1"

