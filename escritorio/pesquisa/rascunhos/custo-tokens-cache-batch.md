# Preços de prompt caching e Batch API da Anthropic (out/2026) e uso em prompts fixos de diretores

## Pergunta
Preços atuais da API da Anthropic para prompt caching e Batch API: multiplicadores de leitura/escrita (TTL 5 min e 1 h), tamanho mínimo de prefixo, desconto do batch, combinação batch + cache e limitações. Uso: estruturar prompts fixos dos diretores de um sistema multiagente e decidir quais tarefas vão para batch. Nível: padrão. Data da pesquisa: 2026-10-21.

## Resumo executivo
Escrita de cache custa 1,25x (5 min) ou 2x (1 h) o preço base de entrada; leitura custa 0,1x, e 0,05x no Opus 5.5 e no Sonnet 5.5 (0,025x no Fable 5.1 e no Mythos 5.1). O Batch API dá 50% de desconto em entrada e saída, os multiplicadores se acumulam, mas os acertos de cache em batch são "best-effort" (30% a 98% de hit). O mínimo cacheável varia por modelo: 512, 1.024, 2.048 ou 4.096 tokens. Qualquer mudança no prefixo (tools, system, messages, nessa ordem) invalida o que vem depois. No Claude Code por assinatura o TTL padrão da conversa principal é 1 h; na API, 5 min.

## Achados

### 1. Multiplicadores de cache (preço base de entrada = 1x)
- Escrita 5 min = 1,25x; escrita 1 h = 2x; leitura/refresh = 0,1x [1][3]. [verificado, 2 fontes oficiais]
- Exceções de leitura: 0,05x no Opus 5.5 ($0,20/MTok) e no Sonnet 5.5 ($0,10/MTok); 0,025x no Fable 5.1 e no Mythos 5.1 ($0,25/MTok) [1][3]. O Sonnet 5 (sem ".5") lê a $0,20 (0,1x) [3]. [verificado]
- Retorno: o cache de 5 min se paga com 1 leitura; o de 1 h com 2 leituras (com 0,1x) [3]. Com 0,05x o ponto de equilíbrio da escrita de 1 h é ainda mais cedo (cálculo próprio, interpretação).
- Preços por MTok (entrada base / escrita 5m / escrita 1h / leitura) [3]: Opus 5.5 $4 / 5 / 8 / 0,20; Opus 5 e 4.5 a 4.8 $5 / 6,25 / 10 / 0,50; Sonnet 5.5 $2 / 2,50 / 4 / 0,10; Sonnet 5 $2 / 2,50 / 4 / 0,20; Sonnet 4.5 e 4.6 $3 / 3,75 / 6 / 0,30; Haiku 5.5 (prompt até 100 mil tokens) $0,10 / 0,125 / 0,20 / 0,01; Haiku 4.5 $1 / 1,25 / 2 / 0,10; Fable 5.1 $10 / 12,50 / 20 / 0,25. [verificado]
- Haiku 5.5 tem preço por tamanho de prompt: acima de 100 mil tokens, tudo sobe (entrada $0,50, leitura $0,05), e leituras/escritas de cache contam para o tamanho [1][3]. [verificado]
- TTL padrão: 5 min, renovado sem custo a cada uso; o relógio começa no início da requisição que escreve ou lê, não no fim da resposta [1]. TTL de 1 h: `{"type":"ephemeral","ttl":"1h"}` [1]. [verificado]
- Misturar TTLs: colocar as entradas de 1 h antes das de 5 min; a cobrança usa 3 posições (A leitura, B escrita 1 h, C escrita 5 min) [1]. [verificado]
- Retenção/privacidade: prompt caching é elegível a ZDR [1].

### 2. Tamanho mínimo de prefixo cacheável (varia por modelo) [1]
- 512 tokens: Fable 5.1, Mythos 5.1, Opus 5.5, Opus 5, Sonnet 5.5, Fable 5, Mythos 5, Haiku 5.5.
- 1.024: Opus 4.8, Sonnet 5, Sonnet 4.6, Sonnet 4.5, Opus 4.1, Opus 4, Sonnet 4.
- 2.048: Mythos Preview, Opus 4.7, Haiku 3.5.
- 4.096: Opus 4.6, Opus 4.5, Haiku 4.5.
- Prompt menor que o mínimo é processado sem cache e sem erro; confirme `cache_creation_input_tokens` e `cache_read_input_tokens` (ambos 0 = não cacheou) [1]. [verificado, fonte única mas oficial e detalhada]
- Implicação: um prompt fixo de diretor com 600 tokens cacheia no Sonnet 5.5, mas não no Haiku 4.5 (exige 4.096).

### 3. Batch API
- Desconto de 50% em entrada e saída; ex.: Sonnet 5.5 batch $1 entrada / $5 saída; Opus 5.5 $2 / $10; Haiku 5.5 (até 100 mil) $0,05 / $0,25; Fable 5.1 $5 / $25 [2][3]. [verificado]
- Combina com cache: os multiplicadores "se acumulam" com o desconto do batch [1][2][3]. Cálculo próprio (interpretação): leitura de cache em batch no Sonnet 5.5 ≈ $0,05/MTok (0,05 x 0,5 x $2), contra $2 de entrada normal sem cache.
- Cache em batch é "best-effort": os pedidos rodam em paralelo e em qualquer ordem; a doc cita taxas típicas de 30% a 98% [2]. Recomendações oficiais: blocos `cache_control` idênticos em todos os pedidos, fluxo constante de pedidos, máximo de conteúdo compartilhado; e como lotes levam de 5 min a 1 h, preferir o cache de 1 h [1][2]. [verificado]
- Padrão mais econômico segundo a doc: mandar primeiro um batch com 1 só pedido que grava o prefixo de 1 h, esperar terminar e só então submeter o resto [1]. [verificado]
- Janela: a maioria dos lotes termina em menos de 1 h; expira em 24 h (pedidos expirados não são cobrados); resultados disponíveis 29 dias após a criação [2]. Limites: 100.000 pedidos ou 256 MB por lote [2]. Fila de processamento por tier: 200 mil (Start), 300 mil (Build), 500 mil (Scale) [4]. [verificado]
- Não suportado em batch: `stream`, `speed` (fast mode) e `max_tokens: 0` (pré-aquecimento de cache) [1][2][3]. `max_tokens` mínimo = 1.
- O lote pode ultrapassar levemente o limite de gasto do workspace [2].

### 4. Limites e invalidação do cache
- Máximo de 4 breakpoints explícitos por requisição; o cache automático ocupa 1 dos 4; lookback de 20 blocos por breakpoint; escritas só ocorrem nos breakpoints [1]. [verificado]
- Hierarquia tools -> system -> messages: mudar um nível invalida ele e os seguintes. Mudar definições de tools invalida tudo; `tool_choice` e adicionar/remover imagens invalidam tools+system; toggle de web search/citações invalida o nível de tools [1]. [verificado]
- Acerto exige prefixo idêntico (hash criptográfico até o ponto do breakpoint) [1]. Cache isolado por workspace na API Claude; por organização no Bedrock e Google Cloud [1].
- Concorrência: a entrada só fica disponível depois que a primeira resposta começa; para requisições paralelas, espere a primeira [1]. Pré-aquecimento com `max_tokens: 0` existe (cobra a escrita) mas é rejeitado em batch [1][2].
- Rate limit: tokens lidos do cache não contam no ITPM na maioria dos modelos (exceção: Haiku 3.5); escrita de cache conta [4]. [verificado]

### 5. Claude Code (assinatura) vs API
- Claude Code cobra por consumo de tokens quando usado via API; em plano Pro/Max/Team/Enterprise o uso sai de uma cota de janela de 5 h e semanal, não de dólares por token [5]. [verificado]
- TTL padrão: assinatura dentro da cota incluída = 1 h na conversa principal; créditos de uso extra, API key ou nuvem = 5 min; subagentes, workflows, compactação e títulos = 5 min (exceto helpers controlados pelo servidor) [6]. Controles: `promptCacheTtl` / `CLAUDE_CODE_PROMPT_CACHE_TTL` (principal), `subagentPromptCacheTtl` / `CLAUDE_CODE_SUBAGENT_PROMPT_CACHE_TTL` (resto), `FORCE_PROMPT_CACHING_5M`, `ENABLE_PROMPT_CACHING_1H`; exigem v2.1.242+ [6]. [verificado]
- Subagente não lê o cache do pai (prefixo diferente); fork lê. Trocar de modelo, adicionar/remover tools (sem tool search) e compactar invalidam o cache [6].
- Batch não existe no Claude Code nem em sessões de Managed Agents (sessões são stateful; sem desconto de batch) [3][6]. [verificado]
- Não achei fonte oficial dizendo como a leitura de cache é ponderada na cota da assinatura; só que a conversa inteira é relida "à taxa de cache" e consome cota [5].

## Recomendações de aplicação (interpretação, não fato)
- Prompt fixo de cada diretor: colocar tudo que é estável (papel, regras, formatos, ferramentas) primeiro, com 1 breakpoint no último bloco estável; dados variáveis (tarefa, data, resultados) depois. Não alterar tools, `tool_choice` nem imagens entre chamadas se quiser reaproveitar o prefixo.
- Prefixo compartilhado entre diretores só gera hit se for byte a byte igual; um prefixo comum (regras do escritório) seguido do bloco específico do diretor permite 2 breakpoints.
- TTL: 5 min se o diretor é chamado em rajadas; 1 h se há pausas de 5 a 60 min entre chamadas (a escrita de 1 h custa 2x e só compensa com 2+ leituras).
- Batch: tarefas sem urgência (pesquisas em lote, revisões, classificação, avaliações); evitar para tarefas interativas ou em cadeia com dependência de resposta, já que a janela vai até 24 h. Em batch com prefixo grande compartilhado, usar a técnica do pedido-semente com cache de 1 h.
- Respeitar o mínimo por modelo: com Haiku 4.5 o prompt fixo precisa de 4.096 tokens para cachear.

## Contrapontos e limitações
- Cache em batch não tem garantia: 30% a 98% de hit; um batch esparso com TTL de 1 h pode custar mais que sem cache (uma fonte secundária faz esse alerta [9]; coerente com a matemática dos multiplicadores).
- Relatos de terceiros (GitHub issue, DEV, notícia de out/2026) dizem que o TTL padrão do Claude Code caiu de 1 h para 5 min em março de 2026 e que o TTL de 1 h some ao passar para créditos extras. A doc oficial atual confirma a parte do crédito extra [6], mas a alegação de regressão silenciosa de março não foi verificada em fonte oficial [7][8]. [não verificado]
- Preços variam por modelo (leitura 0,1x / 0,05x / 0,025x); não trate 0,1x como constante em planilhas.
- Multiplicador de 1,1x para `inference_geo: "us"` se aplica a todas as categorias, incluindo cache [3].
- O novo tokenizador (Claude 4.7+) gera cerca de 30% mais tokens para o mesmo texto, o que afeta o cálculo de custo e o mínimo de prefixo [3].

## Incertezas e lacunas
- Não consegui abrir claudeissues.com, propakistani.pk e eesel.ai (erro de DNS no ambiente); as alegações sobre regressão de TTL vêm só de snippets de busca. [não verificado]
- O blog oficial "Prompt caching is everything" redirecionou para o domínio claude.dev (não oficial/não confirmado); não foi lido. A seção de preços usada vem da doc de pricing, sem data de atualização na página.
- As páginas de doc não trazem data de publicação; valores refletem o que estava na doc em 2026-10-21. Rever em 90 dias (tipo tecnologia).
- Não verificado: como a leitura de cache é pesada na cota de assinatura do Claude Code; se o Batch API tem fila mais lenta em horários de pico além do aviso genérico de "demanda".
- O trecho final (60 mil caracteres) da página de prompt caching foi lido só por busca de palavras-chave (FAQ e batch), não por inteiro.

## Fontes
[1] Prompt caching, Anthropic (platform.claude.com), acessada 2026-10-21, https://platform.claude.com/docs/en/build-with-claude/prompt-caching (primária)
[2] Batch processing, Anthropic, 2026-10-21, https://platform.claude.com/docs/en/build-with-claude/batch-processing (primária)
[3] Pricing, Anthropic, 2026-10-21, https://platform.claude.com/docs/en/about-claude/pricing (primária)
[4] Rate limits, Anthropic, 2026-10-21, https://platform.claude.com/docs/en/api/rate-limits (primária)
[5] Manage costs effectively, Claude Code docs, 2026-10-21, https://code.claude.com/docs/en/costs (primária)
[6] How Claude Code uses prompt caching, Claude Code docs, 2026-10-21, https://code.claude.com/docs/en/prompt-caching (primária)
[7] GitHub issue espelhado "Cache TTL silently regressed from 1h to 5m around early March 2026", claudeissues.com (secundária, só snippet de busca)
[8] "Claude Reportedly Resets Your Cache to Charge You More", propakistani.pk, 2026-10-16 (secundária, só snippet de busca)
[9] "How to Cut Your LLM API Bill in 2026", developersdigest.tech (secundária, só snippet de busca)
[10] Guias de preço de terceiros (eesel.ai, fast.io), 2026 (secundárias, só snippets; usadas apenas como conferência de que o batch dá 50% e acumula com cache)
