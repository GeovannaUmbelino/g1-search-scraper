# Plano de avaliação da qualidade

| Dimensão | Métrica | Critério sugerido |
|---|---|---|
| Completude | células preenchidas / células esperadas; separada para campos obrigatórios | obrigatórios = 100% |
| Atualidade | diferença entre ordem/datas observadas e coletadas no mesmo instante | sem divergência na amostra |
| Precisão | URLs da saída presentes na referência / URLs coletadas | 100% na amostra controlada |
| Acurácia | títulos exatamente iguais entre URLs correspondentes | 100% |
| Cobertura (recall) | URLs da referência recuperadas / URLs da referência | 100% |
| Unicidade | URLs canônicas distintas / registros | 100% |
| Consistência | URLs HTTPS do domínio Globo e datas ISO válidas / registros aplicáveis | 100% |
| Rastreabilidade | registros com termo, página, fonte e timestamp / registros | 100% |

`python -m g1_scraper.cli` grava os resultados em `reports/quality_metrics.json`.
A referência precisa ser manual e independente; uma referência vazia não deve ser
apresentada como evidência de qualidade.

## Pressuposto temporal da avaliação

A comparação considera os primeiros N resultados da coleta, sendo N o tamanho
da amostra manual. A metodologia pressupõe que a observação manual e a execução
do scraper sejam realizadas em momentos próximos e com a mesma ordenação da
busca.

Como o conteúdo do G1 é atualizado continuamente, novos resultados podem ser
publicados ou a ordem pode mudar entre a observação e a coleta. Nesse caso, uma
divergência de posição não representa necessariamente uma falha do scraper.

Para garantir a rastreabilidade, cada item da amostra registra sua posição,
página e horário de observação. As métricas representam uma fotografia da
execução avaliada e não uma garantia permanente sobre o portal.

A métrica `reference_precision` compara os primeiros N registros coletados com
os N itens da amostra. Já `currentness_order_agreement` verifica quantos itens
permaneceram exatamente na mesma posição. Portanto, essas métricas devem ser
interpretadas em conjunto.