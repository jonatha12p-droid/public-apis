# Cache de prompt na cota de assinatura Pro/Max do Claude Code e como medir o consumo (out/2026)

## Pergunta
(1) Como tokens de leitura e de escrita de cache contam na cota da assinatura Pro/Max do Claude Code (normal, com desconto ou não contam)? (2) Como ver o consumo de cota no Claude Code e se dá para separar por sessão ou por subagente. Nível: padrão, só a lacuna. Preços de API, TTLs e Batch estão em `pesquisa/precos-de-prompt-caching-e-batch-api-da-anthropic-out-2026` (não repetidos). Data da pesquisa: 2026-10-21.

## Resumo executivo
Não existe fonte oficial da Anthropic que diga o peso de leitura/escrita de cache na cota Pro/Max: docs do Claude Code, central de ajuda e páginas de planos foram lidas e nenhuma publica a fórmula. O oficial confirma só que cada requisição reenvia a conversa inteira, relida "à taxa de cache", e que isso consome cota; a ponderação exata é desconhecida. Relatos de usuários divergem (de "cache read conta pouco" a "conta cheio"). Para medir: `/usage` (barras de cota 5 h/semanal, atribuição por skill/subagente/plugin/MCP, janela 24 h ou 7 dias, só dados locais), status line (`rate_limits`) e OpenTelemetry (`query_source=subagent`, `agent.name`; por instância só em spans). Separar por sessão: `session.id` no OTel e transcritos; por subagente: só por tipo/atribuição percentual, não em tokens exatos na cota.

## Achados

### 1. Contagem de cache na cota (fonte oficial)
- Não há documento oficial com a ponderação. A central de ajuda "How do usage and length limits work" diz que o uso depende de tamanho e complexidade da conversa, recursos, modelo e esforço, sem fórmula e sem citar cache de prompt; uso em claude.ai, Claude Code e Desktop conta no mesmo limite [3]. [verificado, ausência registrada]
- O artigo sobre Claude Code com Pro/Max lista janela de 5 h e semanal compartilhadas com o chat, e limite semanal separado para um modelo na Max; não cita caching [4]. [verificado, ausência registrada]
- O artigo "usage limit best practices" (central de ajuda geral, foco em claude.ai Projects) diz que conteúdo de projetos em cache "conta menos" contra os limites quando reaproveitado, e que após inatividade o cache expira e volta a contar integral [5]. Isso é desconto para Projects no chat; o artigo não menciona Claude Code, então não se pode extrapolar. [verificado, aplicabilidade ao Claude Code não verificada]
- Docs do Claude Code (costs): em sessão longa o Claude Code reenvia a conversa a cada requisição e relê o histórico "ao taxa de cache" (cached token rate), e mesmo uma pergunta de uma linha "ainda consome cota" pela conversa inteira; erro de cache (primeira mensagem após pausa maior que o TTL) reprocessa o contexto todo [1]. [verificado] Interpretação: leitura de cache conta (pelo menos em parte) na cota; "taxa de cache" remete ao preço de API, mas o texto não afirma que a cota usa os mesmos multiplicadores.
- Os documentos de cache do Claude Code dizem que, na assinatura dentro da cota, a conversa principal usa TTL de 1 h e subagentes/compactação 5 min [2]; relevante porque escrita de cache é mais cara e miss reprocessa tudo (ver acervo).
- Ao exceder a cota, o consumo vai para créditos de uso (usage credits), cobrados; aí o TTL da conversa principal cai para 5 min [2]. [verificado]

### 2. Evidência secundária (relatos de usuários; não oficial)
- Issue anthropics/claude-code #24147 (aberta 2026-02-08, ainda aberta, sem resposta de funcionário): em 30 dias, 5,09 bilhões de cache reads (99,93% do total) contra 3,9 milhões de tokens de entrada/saída e 176 milhões de escrita de cache; o autor argumenta que cache reads consomem cota cheia e pede peso reduzido [6]. Medição própria dos transcritos locais, não controlada contra o percentual de cota. [secundária]
- No mesmo thread, comentários conflitantes: um afirma que cache reads "não são cobrados, mas contam" na cota de sessão e semanal (14/mar); outro diz que o custo real de cota está na escrita de cache; outro diz que é "descontado, mas ainda real". Nenhum com medição [6]. Relato de ago/2026 (Pro, Opus 5): 408M tokens num dia não bateram o limite, enquanto 47M em outro dia esgotaram a janela de 5 h; uma sessão de 17 min com 3,6M de leituras consumiu cerca de 45% da janela; o autor pergunta se a leitura passou a ter peso cheio e abriu chamado [6]. [secundária, anedótica]
- Análise de terceiros (lilting.ch), via snippet de busca: ajustou dados de uso contra vários pesos de cache read; o melhor ajuste foi o de peso quase nulo para leitura, e diz que a Anthropic nunca divulgou a base dos "5x" e "20x" [7]. [secundária, não aberta na íntegra, não verificado]
- Relatos em claudeissues.com (#43893, #41506), via snippet: quedas de cota atribuídas a bugs/regressão de cache (razão de leitura caiu a ~4%) e limite atingido com 12M tokens quando antes passava de 1,7 bilhão; sugerem que o que pesa é miss/reescrita, não leitura em si [8]. [secundária, não verificado]
- Um usuário Max 20x relata cerca de 97% dos tokens como cache read, tratados como releituras baratas (christopheralarcon.com, via snippet) [9]. [secundária, não verificado]
- Síntese (interpretação): a evidência é compatível com leitura de cache pesando pouco por token, mas com volume gigante e miss/escrita sendo os grandes consumidores; nenhuma medição controlada (cota percentual versus tokens por tipo) foi encontrada.

### 3. Ver o consumo de cota
- `/usage`: bloco Session (tokens por modelo: input, output, cache read, cache write, e custo estimado a preço de lista; é feito para usuários de API e "não é relevante" para cobrança de assinantes), mais, para Pro/Max/Team/Enterprise, barras de uso do plano, estatísticas de atividade e quebra de uso [1]. Zera com `/clear`. [verificado]
- Linha `Prompt cache (main)` no `/usage` (v2.1.251+): requisições, % de input vindo de cache, misses (com causa provável na v2.1.260+), reconstruções esperadas, frio/quente e TTL; cobre só a conversa principal, não subagentes [1][2]. [verificado]
- Quebra do plano em `/usage`: atribuição recente a skills, subagentes, plugins e servidores MCP em % do total, recomendações (linhas com a fatia que cada uma endereça, mínimo 10%), loops agendados (v2.1.242+); tecla `d`/`w` alterna 24 h e 7 dias; valores aproximados, calculados do histórico local desta máquina, sem outros dispositivos nem claude.ai; atalho `f` aplica recomendações (v2.1.305+) [1]. [verificado]
- `/usage` mostra a linha de créditos de uso (gasto do mês e limite) e pode exibir "last-known usage" se o endpoint estiver limitado; `r` tenta de novo [1]. `/usage-credits` abre Settings > Usage no claude.ai [1].
- Artigo da central de ajuda cita `/status` para ver a alocação restante e avisos ao se aproximar do limite [4]; claude.ai Settings > Usage mostra "Plan usage limits" (5 h e semanais) e créditos [5]. [verificado]
- Status line: JSON de stdin traz `rate_limits.five_hour.used_percentage`/`resets_at` e `rate_limits.seven_day.*` (só assinantes Pro/Max, após a primeira resposta; cada janela pode faltar), `context_window.current_usage` com `cache_creation_input_tokens` e `cache_read_input_tokens`, e objeto `prompt_cache` (não conta subagentes) [10][2]. [verificado]
- `/insights` gera relatório HTML de sessões locais (consome cota) [1]. `claude -p ... --output-format json` mostra `usage.cache_creation` por TTL [2].

### 4. Separar por sessão e por subagente
- Oficial, dentro do Claude Code: o `/usage` atribui % a subagentes (como grupo) e skills/plugins/MCP, em janelas de 24 h/7 dias, só localmente; não mostra tokens ou % de cota por sessão nem por subagente individual [1]. A doc de subagentes confirma que as requisições do subagente "contam para os mesmos limites" da conversa principal; `/tasks` mostra modelo/esforço do subagente, sem custo [11]. [verificado; "não mostra por instância" é inferência por ausência]
- Transcritos: cada subagente grava `~/.claude/projects/{projeto}/{sessionId}/subagents/agent-{agentId}.jsonl`, retidos 30 dias por padrão (`cleanupPeriodDays`) [11]. Dá para somar tokens por sessão/subagente a partir desses arquivos (cálculo próprio, interpretação; usages por tipo estão nas respostas gravadas, não verificado aqui).
- OpenTelemetry: métrica `claude_code.token.usage` com `type` = input/output/cacheRead/cacheCreation; atributo `session.id` em tudo; `query_source` = main/subagent/auxiliary; `agent.name` por tipo de subagente (agentes definidos pelo usuário aparecem como `custom` a menos que `OTEL_LOG_TOOL_DETAILS=1`); `agent_id` e `parent_agent_id` só em spans de tracing beta (`CLAUDE_CODE_ENHANCED_TELEMETRY_BETA=1`) [12]. [verificado] Importante: isso mede tokens, não a cota; o OTel não explica a relação com a cota de assinatura [12].
- Percentuais de cota (5 h/semanal) vêm do servidor; ferramentas locais só estimam tokens (afirmação de terceiro, via snippet) [13]. [não verificado]
- Efeitos que afetam atribuição: subagente não lê o cache do pai (TTL 5 min), fork lê; sessões paralelas no mesmo diretório compartilham cache [2].

## Contrapontos e limitações
- A tese "cache read conta cheio" (issue #24147) vem de correlação sem controle, com volumes de tokens que não explicam a variação de cota; há relatos de dias com 408M tokens sem bater limite [6]. A tese "conta quase nada" (lilting.ch) é um ajuste estatístico de um autor e não foi lida na íntegra [7].
- Desconto "conta menos" da central de ajuda é para Projects no claude.ai, não para Claude Code [5].
- `/usage` é aproximado, local e exclui outros dispositivos e claude.ai; barras podem ficar desatualizadas [1].
- O custo em dólares do `/usage` é a preço de lista de API e não reflete a cota [1].

## Incertezas e lacunas
- Peso exato (por tipo de token e por modelo) na cota Pro/Max: sem fonte oficial depois de ler docs do Claude Code (costs, prompt-caching, statusline, sub-agents, monitoring), 3 artigos da central de ajuda e buscas dedicadas. [não verificado]
- Não achei declaração de funcionário da Anthropic sobre o tema; busca não exaustiva (thread do GitHub #24147 sem resposta).
- Não consegui abrir lilting.ch, blogg.sikt.no, dev.to, wokey.ai, scrum.org, letsdatascience.com (erro de DNS no ambiente); as evidências deles são só de snippet. Páginas de planos (claude.com/pricing) não foram abertas.
- Não li a parte final (cerca de 56 mil caracteres) da página de monitoring-usage nem os últimos 9 mil da de sub-agents.
- Páginas da central de ajuda sem data ("atualizada esta semana"). Docs refletem v2.1.3xx de out/2026; revalidar em 90 dias.
- Não testei `/usage` nem OTel numa sessão real; a ausência de visão por subagente individual na cota é inferência.

## Fontes
[1] Manage costs effectively, Claude Code docs, acessada 2026-10-21, https://code.claude.com/docs/en/costs (primária)
[2] How Claude Code uses prompt caching, Claude Code docs, 2026-10-21, https://code.claude.com/docs/en/prompt-caching (primária)
[3] How do usage and length limits work, Claude Help Center, 2026-10-21, https://support.claude.com/en/articles/11647753-how-do-usage-and-length-limits-work (primária)
[4] Using Claude Code with your Pro or Max plan, Claude Help Center, 2026-10-21 ("atualizada esta semana"), https://support.claude.com/en/articles/11145838-using-claude-code-with-your-pro-or-max-plan (primária)
[5] Usage limit best practices, Claude Help Center, 2026-10-21, https://support.claude.com/en/articles/9797557-usage-limit-best-practices (primária)
[6] Issue #24147 "Cache read tokens consume 99.93% of usage quota", anthropics/claude-code, aberta 2026-02-08, comentários até ago/2026, https://github.com/anthropics/claude-code/issues/24147 (secundária, relato de usuários)
[7] Anthropic's Unannounced Cache TTL Change and Claude Code Quota Exhaustion, lilting.ch, https://lilting.ch/en/articles/claude-code-cache-ttl-quota-exhaustion (secundária, só snippet)
[8] Issues #43893 e #41506, claudeissues.com, https://claudeissues.com/issue/43893-max-plan-5x-143x-token-usage-drop-limit-reached-with-12m-tokens-was-1-714m-witho e https://claudeissues.com/issue/41506-max-plan-token-usage-increased-3-5x-without-any-configuration-change-since-march (secundária, só snippet)
[9] My real Claude Code usage, christopheralarcon.com, https://christopheralarcon.com/blog/my-real-claude-code-usage/ (secundária, só snippet)
[10] Customize your status line, Claude Code docs, 2026-10-21, https://code.claude.com/docs/en/statusline (primária)
[11] Create custom subagents, Claude Code docs, 2026-10-21, https://code.claude.com/docs/en/sub-agents (primária)
[12] Monitoring usage (OpenTelemetry), Claude Code docs, 2026-10-21, https://code.claude.com/docs/en/monitoring-usage (primária; primeiros 100 mil caracteres)
[13] Claude Code usage tracker, ccassist.dev, https://ccassist.dev/claude-code-usage-tracker/ (secundária, só snippet)
[14] Acervo: pesquisa/precos-de-prompt-caching-e-batch-api-da-anthropic-out-2026 (interna)
