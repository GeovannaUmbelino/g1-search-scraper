# Estratégia de LLM com controle de evidências

## Onde usar

A LLM atua somente no **diagnóstico e manutenção assistida**, nunca como fonte dos dados.
Um monitor determinístico detecta anomalias (zero resultados, queda de completude,
mudança no hash estrutural ou seletores sem correspondência) e envia ao modelo:

- HTML sanitizado e limitado do contêiner de resultados;
- seletores atuais e suas contagens;
- diff entre a última fixture válida e o HTML novo;
- status HTTP, Content-Type e logs sem cookies, tokens ou dados pessoais;
- esquema obrigatório da saída e testes que precisam continuar passando.

O modelo responde em JSON estrito com `diagnosis`, `selector_candidates`, `evidence` e
`confidence`. Cada candidato deve citar um trecho literal do HTML fornecido.

## Validação antes de uso

1. rejeitar qualquer seletor que não encontre elementos na fixture nova;
2. exigir que URL e título sejam obtidos do mesmo card;
3. executar testes unitários, regressão nas fixtures e comparação com amostra manual;
4. exigir revisão humana e pull request; nunca alterar produção automaticamente;
5. implantar em modo sombra e comparar volumes/completude antes da promoção.

## Prevenção de alucinação

- temperatura baixa e saída estruturada;
- instrução explícita: “não preencha campos ausentes; use `null`”;
- lista fechada de campos e seletores;
- toda sugestão deve conter evidência copiada do HTML de entrada;
- validação por Beautiful Soup e JSON Schema;
- LLM não recebe permissão para escrever no banco nem produzir registros;
- valores coletados continuam vindo exclusivamente do parser determinístico.

## Pseudocódigo

```python
if monitor.detectou_regressao(metricas, assinatura_dom):
    pacote = sanitizar({"html": trecho_html, "diff": diff, "logs": logs, "schema": schema})
    sugestao = llm.gerar_json(pacote, temperature=0)
    validar_schema(sugestao)
    for seletor in sugestao["selector_candidates"]:
        assert BeautifulSoup(html, "html.parser").select(seletor)
    abrir_pull_request_para_revisao(sugestao)  # nunca aplicar automaticamente
```

