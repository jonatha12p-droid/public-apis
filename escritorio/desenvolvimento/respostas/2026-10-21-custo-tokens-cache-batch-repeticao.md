# Resposta: custo de tokens, cache e Batch API (repetição)

- **Resultado:** HIT
- **Nota do acervo:** 4
- **Caminho no acervo:** `escritorio/acervo/pesquisa/precos-de-prompt-caching-e-batch-api-da-anthropic-out-2026.md` (criado 2026-10-21, válido até 2027-01-19)

## Resumo

Escrita de cache custa 1,25x (TTL 5 min) ou 2x (TTL 1 h) do preço base de entrada; leitura custa 0,1x (0,05x no Opus 5.5 e Sonnet 5.5; 0,025x no Fable 5.1 e Mythos 5.1). Batch API dá 50% em entrada e saída; os descontos se acumulam com o cache, mas o acerto de cache em batch é best-effort (30% a 98%). Mínimo cacheável varia por modelo (512 a 4.096 tokens). Mudança no prefixo invalida o cache dali em diante.

Aplicação: conteúdo estável primeiro no prefixo; TTL de 1 h só com pausas e 2 ou mais leituras; batch para tarefas sem urgência.

Incertezas registradas no acervo: regressão do TTL do Claude Code em março/2026 não verificada; peso da leitura na cota de assinatura não verificado.
