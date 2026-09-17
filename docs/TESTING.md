# Estratégia e documentação dos testes

## Objetivo

A suíte automatizada verifica os componentes críticos do scraper e ajuda a detectar
regressões causadas por mudanças no HTML, na configuração da busca, na paginação ou no
formato dos dados retornados pelo G1.

Os testes foram projetados para ser determinísticos, reproduzíveis e independentes da
disponibilidade do portal.

## Abordagens adotadas

### Testes de caixa branca

Os testes estruturais exercitam decisões e caminhos internos relevantes, incluindo:

- condições de parada da paginação;
- fluxo de sucesso e fluxos de erro;
- tratamento de exceções de rede;
- respostas HTTP e tipos de conteúdo inválidos;
- campos obrigatórios e opcionais;
- descarte de registros sem URL;
- deduplicação por URL canônica;
- códigos de saída da CLI;
- criação condicional das métricas de qualidade.

A cobertura de instruções é medida pelo `pytest-cov`. Ela é usada como indicador de
apoio, não como única evidência de qualidade.

### Testes funcionais

Os testes funcionais validam entradas e saídas observáveis. Entre os comportamentos
verificados estão:

- conversão de HTML em registros estruturados;
- limpeza de tags e normalização de espaços;
- remoção de parâmetros de rastreamento;
- extração da URL editorial de redirecionadores do G1;
- representação de campos ausentes como `None`;
- gravação de CSV e JSON em UTF-8;
- geração do resumo de execução;
- cálculo das métricas de qualidade.

### Fixtures e testes de regressão

As fixtures em `tests/fixtures` representam estruturas conhecidas da página, como o
objeto `window.__CONTEXT__` e cards renderizados. Elas permitem reproduzir alterações e
testar seletores sem acessar a internet.

Quando houver uma mudança legítima no portal, o procedimento recomendado é:

1. preservar uma amostra sanitizada do novo HTML;
2. criar primeiro um teste que reproduza a regressão;
3. corrigir o parser;
4. executar toda a suíte;
5. comparar uma coleta real com a amostra manual.

### Simulação das dependências externas

As chamadas HTTP são substituídas por objetos simulados. Assim, a suíte consegue testar
respostas válidas, falhas de conexão, conteúdo inválido e falhas parciais sem depender da
rede ou gerar carga no portal.

## Matriz de testes

| Área | Cenário | Resultado esperado |
|---|---|---|
| Texto | HTML, entidades e espaços extras | Texto limpo e normalizado |
| URL | Parâmetros `utm_*` e fragmentos | URL canônica |
| URL | Redirecionador `measures.globo.com` | URL editorial extraída |
| Contexto | `window.__CONTEXT__` válido | Configuração recuperada |
| HTML | Campos opcionais ausentes | Registro mantido com `None` |
| API | Registro sem URL | Registro descartado |
| Cliente | Content-Type incorreto | Erro controlado |
| Cliente | Falha de conexão | `CollectionError` |
| Paginação | Vários lotes | Offsets processados corretamente |
| Paginação | Lote vazio | Execução encerrada sem loop |
| Resiliência | Falha em uma página | Dados anteriores preservados |
| Deduplicação | URL repetida | Apenas uma ocorrência mantida |
| Armazenamento | Registros válidos | CSV e JSON em UTF-8 |
| Qualidade | Saída e referência | Métricas entre 0 e 1 |
| CLI | Execução válida | Arquivos criados e exit code 0 |
| CLI | Nenhuma página válida | Exit code 1 |
| CLI | Falha inicial controlada | Exit code 2 |

## Execução

Instale as dependências:

```bash
python -m pip install -e ".[dev]"
```

Execute todos os testes:

```bash
python -m pytest
```

Execute o linter:

```bash
python -m ruff check src tests
```

Gere um relatório HTML de cobertura:

```bash
python -m pytest --cov=g1_scraper --cov-report=term-missing --cov-report=html
```

O relatório navegável será criado em `htmlcov/index.html`. No Windows:

```powershell
Invoke-Item .\htmlcov\index.html
```

## Interpretação da cobertura

O resultado oficial deve ser sempre o produzido pela execução mais recente de
`python -m pytest`. A documentação evita fixar uma porcentagem que possa ficar
desatualizada quando novos testes ou linhas forem adicionados.

O projeto prioriza os fluxos de rede, parsing, paginação, armazenamento, qualidade e CLI.
Não é necessário criar testes artificiais apenas para cobrir o bloco de inicialização
`if __name__ == "__main__"`.

## Separação entre testes offline e coleta real

A suíte automatizada é offline e determinística. A integração real é verificada
separadamente com:

```bash
python -m g1_scraper.cli --term lgpd --max-pages 5 --page-size 10 --delay 1
```

Essa separação permite distinguir falha do código, indisponibilidade de rede e mudança
do portal. A qualidade da coleta real é avaliada contra a amostra independente em
`data/reference/manual_sample.json`.

## Integração contínua

O workflow em `.github/workflows/ci.yml` executa o linter e a suíte a cada push e pull
request. Isso impede que alterações com regressões sejam incorporadas silenciosamente.

## Limitações

- As fixtures precisam ser atualizadas quando a estrutura legítima do portal mudar.
- Testes offline não comprovam que o G1 está disponível naquele instante.
- Cobertura alta não substitui uma amostra manual independente.
- A API de busca utilizada pelo frontend é interna e pode mudar sem aviso.

