---
pedido: escritorio/pesquisa/pedidos/2026-10-21-custo-tokens-cache-batch.md
de: pesquisa
para: desenvolvimento
resultado: MISS
nivel: padrao
nota: 4
data: 2026-10-21
---
# Resposta: custo de tokens, prompt caching e Batch API

## Resultado
MISS (nada no acervo cobria o tema). Pesquisa nova em nível padrão, avaliada com o checklist de curadoria: nota 4, arquivada.

## Justificativa da nota (checklist)
1. Cobre pelo menos 3 ângulos distintos: sim (multiplicadores, mínimo de prefixo, Batch API, limites e invalidação, Claude Code vs API). 1 ponto.
2. Fontes distintas, mínimo 8: sim, 10 fontes (6 oficiais lidas por inteiro, 4 secundárias só por snippet). 1 ponto.
3. Fontes primárias quando existem: sim, documentação oficial da Anthropic e do Claude Code. 1 ponto.
4. Contraponto, críticas ou limitações: sim (best-effort do batch, variação de preço por modelo, relatos de regressão de TTL). 1 ponto.
5. Seção de incertezas e lacunas com datas das fontes: sim. 1 ponto.
Subtotal: 5.
Ajuste (-1): o mínimo cacheável por modelo, que é item central do pedido e fundamenta a recomendação para o Haiku 4.5, veio de uma única fonte oficial. A regra de triangulação pede 2 ou mais fontes para afirmações-chave. Nota final: 4.

## Resumo
Escrita de cache custa 1,25x (TTL 5 min) ou 2x (TTL 1 h) do preço base de entrada; leitura custa 0,1x (0,05x no Opus 5.5 e Sonnet 5.5; 0,025x no Fable 5.1 e Mythos 5.1). Batch API dá 50% em entrada e saída; os descontos se acumulam com o cache, mas o acerto de cache em batch é best-effort (30% a 98%). Mínimo cacheável varia por modelo (512 a 4.096 tokens). Mudança no prefixo invalida o cache dali em diante. Aplicação: conteúdo estável primeiro; TTL de 1 h só com pausas e 2+ leituras; batch para tarefas sem urgência. Incertezas: regressão do TTL do Claude Code em março/2026 não verificada; peso da leitura na cota de assinatura não verificado.

## Caminho no acervo
escritorio/acervo/pesquisa/precos-de-prompt-caching-e-batch-api-da-anthropic-out-2026.md (válido até 2027-01-19)

## Relatório completo
escritorio/pesquisa/rascunhos/custo-tokens-cache-batch.md

## Pendências
- Não verificado: a alegação de mudança do TTL padrão no Claude Code em março de 2026, e o peso da leitura de cache na cota da assinatura.
- Rever em 90 dias (tipo tecnologia).
