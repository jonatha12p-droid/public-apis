---
de: pesquisa
para: pesquisa
pedido: escritorio/pesquisa/pedidos/2026-10-21-cache-na-cota-assinatura.md
resultado: PARCIAL
nota: 4
status: respondido
---
# Resposta

**Resultado:** PARCIAL (lacuna da pesquisa de precos de prompt caching). Pesquisa nova em nível padrão, só a lacuna.

**Nota de curadoria:** 4 de 5. Checklist: 3 ângulos, 14 fontes distintas, fontes primárias, contraponto e seção de incertezas com datas. Desconto de 1 ponto por números de fontes secundárias marcados como não verificados (ex.: ~4%, 97%, 408M tokens).

**Resumo:** Não há fonte oficial da Anthropic com o peso de cache read e cache write na cota Pro/Max. Os docs do Claude Code confirmam que cada requisição relê a conversa e que isso consome cota, sem publicar a fórmula. Relatos de usuários divergem (leitura pesa pouco ou cheio); é evidência secundária, sem medição controlada. Para ver o consumo: /usage (barras 5 h e semanal, atribuição a skills e subagentes em 24 h ou 7 dias, só local), status line (rate_limits) e OpenTelemetry (session.id, query_source=subagent; mede tokens, não cota). Separar por sessão é possível por OTel e transcritos; por subagente individual na cota não há visão oficial (inferência). Não testado em sessão real.

**Caminho no acervo:** pesquisa/cache-de-prompt-na-cota-de-assinatura-pro-max-do-claude-code (válido até 2027-01-19)

**Relatório completo (só se precisar de detalhe):** /home/user/public-apis/escritorio/pesquisa/rascunhos/cache-na-cota-assinatura.md
