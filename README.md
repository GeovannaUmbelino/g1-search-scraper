# G1 Search Scraper — Desafio NetLab UFRJ

Scraper resiliente e auditável desenvolvido em Python para coletar resultados da busca do portal G1.

A solução utiliza Requests e Beautiful Soup, trata falhas de rede e campos ausentes, implementa paginação, remove duplicidades e gera dados estruturados em CSV e JSON, além de logs, resumo da execução e métricas de qualidade.

## Objetivo

O projeto corrige uma rotina de web scraping que deixou de funcionar após mudanças na estrutura e no funcionamento da página:

```text
https://g1.globo.com/busca/?q=lgpd
```

Além da correção da coleta, o projeto apresenta:

- diagnóstico da falha original;
- código modular e reutilizável;
- tratamento de erros e campos ausentes;
- paginação baseada no mecanismo atual;
- deduplicação por URL canônica;
- armazenamento em CSV e JSON;
- testes automatizados;
- integração contínua;
- amostra manual de referência;
- métricas de qualidade dos dados;
- estratégia controlada de uso de LLM;
- limitações e possibilidades de evolução.

## Diagnóstico do código original

O problema não era apenas um seletor HTML desatualizado.

Atualmente, a página pública do G1 entrega inicialmente o esqueleto de uma aplicação React. Os resultados da busca são carregados posteriormente pela fonte de dados utilizada pelo frontend.

Os principais problemas identificados no código original foram:

1. Os seletores `.resultado`, `.titulo`, `.resumo` e `.data` não correspondem mais à estrutura atual.
2. `requests.get()` era utilizado como se todos os cards estivessem presentes no HTML inicial.
3. As páginas anteriores eram descartadas por causa da atribuição:

   ```python
   resultados = dados_pagina
   ```

   O correto seria acumular os resultados.
4. A paginação era baseada no parâmetro `page`, enquanto o mecanismo atual utiliza `offset` e quantidade de registros.
5. Chamadas a `.get_text()` eram feitas sem verificar se o elemento existia.
6. Não havia timeout, validação de status HTTP, retentativas ou backoff.
7. Não existia tratamento para respostas inválidas.
8. Não havia deduplicação.
9. A execução utilizava apenas `print`, sem níveis ou contexto de log.
10. Os timestamps não indicavam explicitamente o fuso horário.
11. O CSV não possuía padronização explícita de codificação.
12. A função principal era executada durante o import do arquivo, dificultando testes e reutilização.

## Solução implementada

O fluxo principal da solução é:

```text
Página pública do G1
        ↓
Beautiful Soup extrai window.__CONTEXT__
        ↓
Configuração atual da busca
        ↓
Requisições paginadas por offset e tamanho
        ↓
Parser e normalização dos campos
        ↓
Canonicalização e deduplicação das URLs
        ↓
CSV + JSON + resumo da execução + métricas
```

Beautiful Soup é utilizado para:

- analisar o HTML inicial;
- localizar e extrair `window.__CONTEXT__`;
- remover marcações HTML de títulos e resumos;
- normalizar entidades e espaços;
- processar cards renderizados diretamente no HTML, quando disponíveis.

A comunicação HTTP está isolada em um cliente próprio. Dessa forma, alterações futuras na fonte de dados não ficam misturadas com as regras de parsing, armazenamento ou avaliação.

## Dados coletados

Quando disponíveis, cada registro contém:

| Campo | Descrição |
|---|---|
| `title` | Título da notícia |
| `url` | URL canônica da notícia |
| `summary` | Resumo do resultado |
| `published_at` | Data de publicação ou atualização |
| `result_page` | Página ou lote no qual o resultado foi encontrado |
| `collected_at` | Horário da coleta em ISO 8601 |
| `search_term` | Termo utilizado na busca |
| `source` | Fonte do resultado |

Campos opcionais ausentes são armazenados como `null` no JSON e como célula vazia no CSV. A ausência desses campos não interrompe a execução.

A URL é considerada o campo mínimo necessário para rastrear e deduplicar um resultado.

## Estrutura do projeto

```text
g1-search-scraper/
├── .github/
│   └── workflows/
│       └── ci.yml
├── data/
│   ├── processed/
│   │   ├── g1_lgpd.csv
│   │   └── g1_lgpd.json
│   └── reference/
│       ├── README.md
│       └── manual_sample.json
├── docs/
│   ├── LLM_STRATEGY.md
│   ├── QUALITY.md
│   └── TESTING.md
├── reports/
│   ├── quality_metrics.json
│   └── run_summary.json
├── src/
│   └── g1_scraper/
│       ├── __init__.py
│       ├── cli.py
│       ├── client.py
│       ├── models.py
│       ├── parsers.py
│       ├── quality.py
│       ├── scraper.py
│       └── storage.py
├── tests/
│   ├── fixtures/
│   ├── conftest.py
│   ├── test_cli.py
│   ├── test_client_storage.py
│   ├── test_parsers.py
│   ├── test_quality.py
│   └── test_scraper.py
├── .gitignore
├── Makefile
├── pyproject.toml
├── README.md
├── setup.ps1
└── setup.sh
```

## Requisitos

- Python 3.10 ou superior;
- acesso à internet para a coleta real;
- PowerShell no Windows ou Bash no Linux/macOS.

Os testes automatizados são offline e não dependem da disponibilidade do portal.

## Instalação automática

### Windows PowerShell

Em um checkout limpo:

```powershell
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
.\setup.ps1
```

O script:

1. cria o ambiente virtual `.venv`;
2. atualiza o `pip`;
3. instala o projeto e as dependências;
4. executa o Ruff;
5. executa os testes automatizados.

### Linux ou macOS

```bash
chmod +x setup.sh
./setup.sh
```

## Instalação manual

### Windows PowerShell

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
python -m pip install -e ".[dev]"
```

Caso a política do PowerShell bloqueie a ativação:

```powershell
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
.\.venv\Scripts\Activate.ps1
```

### Linux ou macOS

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -e ".[dev]"
```

## Execução da coleta

Com o ambiente virtual ativado:

```bash
python -m g1_scraper.cli --term lgpd --max-pages 5 --page-size 10 --delay 1
```

Também é possível utilizar o comando instalado:

```bash
g1-scraper --term lgpd --max-pages 5 --page-size 10 --delay 1
```

### Parâmetros

| Parâmetro | Padrão | Descrição |
|---|---:|---|
| `--term` | `lgpd` | Termo pesquisado |
| `--max-pages` | `5` | Quantidade máxima de páginas ou lotes |
| `--page-size` | `10` | Quantidade de resultados solicitada por lote |
| `--delay` | `1` | Intervalo em segundos entre as requisições |
| `--output-dir` | `data/processed` | Diretório de saída dos dados |
| `--reference` | `data/reference/manual_sample.json` | Amostra manual |
| `--log-level` | `INFO` | Nível dos logs |

Para coletar mais resultados, é possível aumentar `--max-pages`. Por exemplo:

```bash
python -m g1_scraper.cli --term lgpd --max-pages 10 --page-size 10 --delay 1
```

Entretanto, uma nova coleta representa uma nova fotografia temporal. Caso ela seja utilizada como evidência final, a amostra manual, as métricas e a documentação também deverão ser atualizadas.

## Arquivos gerados

A execução gera:

```text
data/processed/g1_lgpd.csv
data/processed/g1_lgpd.json
reports/run_summary.json
reports/quality_metrics.json
```

O CSV utiliza `UTF-8 com BOM`, melhorando a compatibilidade com o Microsoft Excel no Windows.

O JSON utiliza UTF-8 e preserva os caracteres acentuados.

## Códigos de saída

| Código | Significado |
|---:|---|
| `0` | Pelo menos uma página foi coletada com sucesso |
| `1` | Nenhuma página foi coletada com sucesso |
| `2` | Ocorreu uma falha controlada antes do início da paginação |

## Testes automatizados

Execute:

```bash
python -m pytest
```

Para executar a análise estática:

```bash
python -m ruff check src tests
```

Para gerar também um relatório HTML de cobertura:

```bash
python -m pytest --cov=g1_scraper --cov-report=term-missing --cov-report=html
```

O relatório será criado em:

```text
htmlcov/index.html
```

No Windows, ele pode ser aberto com:

```powershell
Invoke-Item .\htmlcov\index.html
```

Na versão congelada para esta entrega foram obtidos:

```text
23 testes aprovados
96% de cobertura de instruções
Ruff sem violações
```

Esses números representam a versão avaliada. O resultado atual deve sempre ser confirmado executando novamente os comandos.

A estratégia de caixa branca, os testes funcionais, as fixtures e a matriz de cenários estão documentados em:

```text
docs/TESTING.md
```

## Integração contínua

O workflow:

```text
.github/workflows/ci.yml
```

executa automaticamente o Ruff e o Pytest em cada `push` e `pull request`.

Isso ajuda a impedir que alterações futuras sejam incorporadas com regressões conhecidas.

## Avaliação da qualidade dos dados

Foi criada manualmente uma amostra independente com cinco resultados observados diretamente na busca do G1.

A amostra está em:

```text
data/reference/manual_sample.json
```

As fórmulas e os pressupostos estão documentados em:

```text
docs/QUALITY.md
```

### Dimensões avaliadas

| Dimensão | Métrica |
|---|---|
| Completude | Proporção de campos preenchidos |
| Cobertura | URLs da referência recuperadas |
| Precisão | Itens do recorte coletado presentes na referência |
| Acurácia | Correspondência exata dos títulos |
| Atualidade | Concordância de posição com a observação manual |
| Unicidade | Proporção de URLs canônicas distintas |
| Consistência | URLs e datas em formatos válidos |
| Rastreabilidade | Presença de termo, página, fonte e horário |

## Evidência final congelada

A execução utilizada como evidência final foi realizada em 16 de setembro de 2026.

A observação manual dos resultados foi registrada em:

```text
2026-09-16T10:11:00-03:00
```

A coleta automatizada ocorreu aproximadamente entre:

```text
2026-09-16T13:15:37+00:00
2026-09-16T13:15:42+00:00
```

Esses horários correspondem aproximadamente a `10:15` no horário de Brasília.

### Resumo da execução

| Indicador | Resultado |
|---|---:|
| Registros coletados | 50 |
| Páginas tentadas | 5 |
| Páginas concluídas | 5 |
| Duplicados removidos | 0 |
| Erros registrados | 0 |
| Tamanho da referência manual | 5 |

### Métricas obtidas

| Métrica | Resultado |
|---|---:|
| Completude de todos os campos | 1.0 |
| Completude dos campos obrigatórios | 1.0 |
| Cobertura da referência | 1.0 |
| Precisão contra a referência | 1.0 |
| Acurácia dos títulos correspondentes | 1.0 |
| Concordância de ordem/atualidade | 0.6 |
| Unicidade | 1.0 |
| Consistência das URLs | 1.0 |
| Consistência das datas | 1.0 |
| Rastreabilidade | 1.0 |

Os arquivos utilizados nessa avaliação são:

```text
data/processed/g1_lgpd.csv
data/processed/g1_lgpd.json
data/reference/manual_sample.json
reports/run_summary.json
reports/quality_metrics.json
```

## Interpretação da atualidade igual a 0.6

A métrica `currentness_order_agreement` compara a posição exata dos primeiros resultados coletados com a posição registrada na observação manual.

O valor `0.6` significa que três dos cinco itens permaneceram exatamente na mesma posição.

Essa divergência é compatível com o comportamento de uma busca dinâmica, pois aproximadamente quatro minutos se passaram entre a observação manual e a coleta automatizada.

Durante esse intervalo:

- novos conteúdos podem ser indexados;
- a relevância dos resultados pode ser recalculada;
- a ordem pode ser alterada pelo portal.

Apesar da mudança de posição:

- todas as cinco URLs de referência foram recuperadas;
- a cobertura foi `1.0`;
- a precisão foi `1.0`;
- a acurácia dos títulos foi `1.0`;
- não houve registros duplicados;
- não houve erro de coleta.

Portanto, o resultado `0.6` representa uma diferença temporal de ordenação, e não uma regressão do parser.

## Como reproduzir esta evidência

Existem duas formas de reprodução.

### 1. Reproduzir a validação determinística

Esta opção não modifica os dados congelados:

```powershell
.\.venv\Scripts\python.exe -m ruff check src tests
.\.venv\Scripts\python.exe -m pytest
```

Resultados esperados para a versão congelada:

```text
All checks passed!
23 passed
96% de cobertura
```

Também é possível inspecionar os artefatos:

```powershell
Get-Content .\reports\run_summary.json -Encoding UTF8
Get-Content .\reports\quality_metrics.json -Encoding UTF8
Get-Content .\data\reference\manual_sample.json -Encoding UTF8
```

### 2. Produzir uma nova coleta dinâmica

```powershell
.\.venv\Scripts\python.exe -m g1_scraper.cli `
  --term lgpd `
  --max-pages 5 `
  --page-size 10 `
  --delay 1
```

Essa execução consulta o estado atual do portal e pode produzir quantidade, ordem, datas e métricas diferentes.

Por esse motivo, uma nova execução não reproduz necessariamente os mesmos valores históricos. Para utilizá-la como nova evidência, é necessário:

1. criar ou atualizar a amostra manual;
2. registrar o novo horário de observação;
3. executar a coleta em momento próximo;
4. conferir os dados gerados;
5. recalcular as métricas;
6. sincronizar o README e os relatórios.

## Estratégia de uso de LLM

A LLM é proposta somente como apoio ao diagnóstico, à manutenção e ao monitoramento do scraper.

Ela não participa da coleta dos registros e não preenche campos ausentes.

### Possíveis usos

O modelo pode:

- analisar HTML sanitizado;
- comparar versões da página;
- identificar mudanças estruturais;
- sugerir seletores candidatos;
- examinar logs de execução;
- sugerir casos de teste;
- apontar inconsistências entre versões.

### Dados fornecidos ao modelo

Somente dados controlados seriam enviados:

- trechos limitados e sanitizados de HTML;
- seletores atuais;
- quantidade de elementos encontrados;
- diferenças entre fixtures;
- status HTTP e `Content-Type`;
- logs sem cookies, tokens ou dados pessoais;
- esquema esperado da saída;
- testes que precisam continuar funcionando.

### Validação das sugestões

Nenhuma sugestão seria aplicada automaticamente.

Antes de qualquer alteração:

1. o seletor deve encontrar elementos no HTML fornecido;
2. título e URL devem vir do mesmo card;
3. os testes automatizados devem ser executados;
4. a coleta deve ser comparada com uma amostra manual;
5. a mudança deve passar por revisão humana;
6. a alteração deve ser incorporada por pull request;
7. a versão pode ser executada em modo sombra antes da promoção.

### Prevenção de alucinações

Para impedir que a LLM introduza informações inexistentes:

- o modelo não tem permissão para escrever na base coletada;
- campos ausentes permanecem `null`;
- a saída deve seguir um esquema JSON fechado;
- seletores sugeridos precisam ser validados com Beautiful Soup;
- evidências devem citar literalmente o HTML recebido;
- os registros finais continuam sendo produzidos exclusivamente pelo parser determinístico.

A proposta completa está documentada em:

```text
docs/LLM_STRATEGY.md
```

## Logs e diagnóstico

A aplicação utiliza o módulo `logging` com níveis configuráveis:

```text
DEBUG
INFO
WARNING
ERROR
```

Exemplo:

```bash
python -m g1_scraper.cli --term lgpd --log-level DEBUG
```

Os logs informam:

- termo pesquisado;
- página e offset;
- quantidade encontrada;
- total informado pela busca;
- falhas parciais;
- interrupção por página vazia;
- duplicados removidos;
- quantidade de páginas concluídas.

## Uso responsável

O coletor utiliza:

- limite de páginas;
- atraso entre requisições;
- timeout;
- retentativas;
- backoff;
- identificação por `User-Agent`.

O `User-Agent` utilizado é:

```text
g1-search-scraper/1.0 (+https://github.com/GeovannaUmbelino/g1-search-scraper)
```

A ferramenta não deve ser utilizada para contornar autenticação, CAPTCHA ou bloqueios do portal.

Antes de utilização institucional ou execução recorrente, devem ser verificados os termos de uso do portal, o arquivo `robots.txt`, os limites de requisição e a existência de uma fonte oficial de dados.

## Limitações

- A fonte utilizada pelo frontend é interna e pode mudar sem aviso.
- O portal pode alterar o formato de `window.__CONTEXT__`.
- Os testes offline não garantem que o G1 esteja disponível no momento da coleta.
- As fixtures precisam ser atualizadas após mudanças legítimas na estrutura.
- A amostra manual utilizada possui cinco registros.
- A ordenação da busca pode mudar entre a observação manual e a coleta.
- Datas relativas apresentadas pela interface podem exigir normalização adicional.
- Uma coleta nova pode sobrescrever os artefatos da execução anterior.

## Melhorias futuras

- versionar execuções históricas por timestamp;
- implementar persistência incremental;
- armazenar grandes volumes em Parquet;
- monitorar mudanças estruturais;
- criar teste opcional de contrato com a fonte real;
- gerar alertas para quedas de volume ou completude;
- guardar fixtures históricas sanitizadas;
- adicionar métricas de observabilidade;
- implementar cache e requisições condicionais;
- executar periodicamente em ambiente controlado;
- utilizar sugestões de LLM somente após validação e revisão humana.

## Autoria

Desenvolvido por **Geovanna Alves Umbelino** como solução para o desafio técnico do NetLab UFRJ.

GitHub:

```text
https://github.com/GeovannaUmbelino
```