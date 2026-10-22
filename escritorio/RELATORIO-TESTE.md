# Relatório do teste ponta a ponta (2026-10-21)

## Arquitetura: o que mudou em relação ao plano

- A documentação atual do Claude Code (sub-agents) diz que um subagente pode criar subagentes até 3 níveis abaixo da conversa principal; a variável `CLAUDE_CODE_MAX_SUBAGENT_SPAWN_DEPTH=1` desliga isso.
- **Neste ambiente (Claude Code na nuvem) os subagentes não tinham a ferramenta Agent** (medido: a primeira tentativa falhou com "No such tool available: Agent").
- Adaptação: `diretor-pesquisa.md` ganhou um modo em duas etapas. Na **TRIAGEM**, ele roteia e busca no acervo e devolve uma `DECISAO`. Na **CURADORIA**, dá a nota e arquiva. Entre as duas, a sessão principal aciona o pesquisador. Onde o aninhamento funcionar, o diretor delega direto.
- `model:` por agente aceita `haiku`, `sonnet`, `opus`, `fable`, `inherit` ou um ID completo. Os agentes foram criados com esse campo, mas só viram tipos próprios numa sessão nova. No teste usei agentes genéricos com o mesmo modelo de cada papel (diretor em Haiku, pesquisador em Sonnet).

## Fluxo executado

| # | Etapa | Modelo | Resultado | Tokens (medidos, `subagent_tokens`) |
|---|---|---|---|---|
| 0 | diretor-desenvolvimento grava o pedido e tenta delegar | Haiku | pedido gravado; delegação falhou (sem Agent) | 54.197 |
| 1 | diretor-pesquisa, triagem | Haiku | `AMBIGUO`, resolvido para pesquisador-tecnico; busca deu `MISS` | 58.993 |
| 2 | pesquisador-tecnico, nível padrão | Sonnet | relatório com 10 fontes (6 oficiais) | 129.239 |
| 3 | diretor-pesquisa, curadoria | Haiku | nota 4, arquivado | 71.682 |
| 4 | mesmo pedido de novo, triagem | Haiku | `ROTA` por regra; busca deu `HIT` | 59.378 |

- Ciclo MISS completo (1+2+3): **259.914 tokens**. Ciclo HIT (4): **59.378 tokens**. Economia medida na repetição: cerca de 200 mil tokens (77%).
- O pesquisador (129 mil) ficou dentro da referência do nível padrão (80 a 160 mil).
- **O HIT custou muito mais que a estimativa de 3 a 8 mil.** Quase tudo é custo fixo de abrir um subagente: prompt de sistema, definições de ferramentas e leitura do SKILL.md. Esse custo se repete nas etapas 0, 1, 3 e 4.
- Ressalva: `subagent_tokens` soma todos os tokens, incluindo leituras de cache. A parte em cache custa bem menos, mas a ferramenta não separa uma da outra.

### `acervo.py stats` (saída real)

```
buscas: 2  HIT=1  PARCIAL=0  VENCIDA=0  MISS=1
taxa de reaproveitamento total (HIT): 50%
roteamentos resolvidos so por regra (sem LLM): 50% de 2
pesquisas arquivadas: 1
```

São 2 buscas apenas, então a taxa não diz nada sobre o uso real.

## Ajustes feitos

- `roteamento.json`: o `padrao` era "pesquisador-geral", que não existe; agora é `pesquisador-tecnico`. O técnico ganhou as palavras cache, caching, batch, prompt, llm, sdk, infraestrutura e infrastructure. O primeiro pedido tinha dado `AMBIGUO` por falta delas.
- O diretor subiu o nível para "profunda" por conta própria. No teste mantive "padrão", que era o nível pedido pelo solicitante.

## Recomendações

1. **Busca no acervo direto pela sessão principal.** Rodar `acervo.py buscar` custa poucos milhares de tokens de saída e não exige abrir um subagente. Só acione o diretor-pesquisa em caso de MISS, PARCIAL ou VENCIDA.
2. Rode `stats` com custos medidos: `--custo-pesquisa 260000 --custo-hit <custo do HIT feito na sessão principal>`. O padrão de 6.000 para HIT não vale para HIT feito por subagente.
3. Conferência rápida: os multiplicadores de cache, os mínimos por modelo e a combinação batch + cache arquivados batem com a página oficial de prompt caching (consultada em 2026-10-21).

## Graphify (README lido em 2026-10-21)

- Pacote `graphifyy`, instalado com `uv tool install graphifyy` e registrado com `graphify install`. Integra como skill com hook no Claude Code; o servidor MCP vem pelo extra `graphifyy[mcp]`. O README não menciona `graphify serve`, ao contrário do que o contexto dizia. A licença é Apache-2.0 e MIT.
- Código é analisado localmente, sem LLM. Docs e PDFs precisam de um passe de modelo.
- O "80% menos tokens" aparece na propaganda do produto pago, sem metodologia. Os benchmarks medem recuperação, não gasto de tokens.
- **Veredito:** não adotar agora para o acervo. O acervo é só markdown, então pagaria extração por LLM, e a busca do `acervo.py` custa zero. Candidato futuro para os repositórios de código do andar de Desenvolvimento.

## Decisões em aberto (seção 8)

Quais andares criar além destes dois; assinatura ou API; um acervo único ou um por projeto; tipos de pesquisa mais frequentes.

## Teste 2: fluxo por script (2026-10-21)

Pedido do andar Redes Sociais sobre frequência e horário de posts no Instagram e no TikTok.

| Etapa | Feita por | Tokens (medidos) |
|---|---|---|
| `pedir` + `triar` (MISS, ROTA por regra para pesquisador-redes-sociais) | script | 0 de subagente |
| Pesquisa, nível padrão | pesquisador-redes-sociais (Sonnet) | 40.072 |
| `checar` | script | 0 (nota provisória 3) |
| Curadoria | diretor-pesquisa (Haiku) | 17.633 (nota 3 confirmada) |

- A triagem por subagente custava de 13.501 a 58.993 tokens; agora custa zero.
- A curadoria caiu de 26.782 a 71.682 tokens para 17.633.
- O fluxo de HIT (`triar` respondendo sozinho) foi testado numa cópia do acervo: nenhum subagente aberto.
- **A pesquisa não foi arquivada.** A política de rede do ambiente bloqueia os sites das fontes (buffer.com, metricool.com, tiktok.com e about.instagram.com recebem 403 do gateway), então o pesquisador só viu resumos de busca.
- O `checar` original teria dado nota 4. Acrescentei o desconto "mais [não verificado] que [verificado]", e com ele a nota caiu para 3. As duas pesquisas antigas continuam com nota 4.
- O pedido segue aberto, com as lacunas registradas, até a rede ser liberada.

### Rodadas extras com a rede liberada

- O WebFetch continuou com erro de DNS mesmo com a rede liberada, enquanto o `curl` chegava aos sites. Por isso foi criado o `scripts/ler_pagina.py`.
- Duas rodadas não leram nada: 26.570 e 31.290 tokens. A segunda falhou porque a mudança de ferramentas do agente só passa a valer numa sessão nova.
- A rodada com o leitor de páginas (Sonnet, 83.927 tokens) leu 9 fontes e confirmou os números do Buffer.
- Curadoria final (20.537 tokens): nota 3, **descartada**. Nenhuma fonte primária segmenta perfis de até 10 mil seguidores, e as recomendações oficiais das plataformas não puderam ser lidas.
- Custo total da pesquisa: 220.029 tokens, dos quais cerca de 58 mil foram perdidos com a ferramenta.

### Pedido reformulado (v2): arquivado com nota 4

- O novo pedido aceita estudos de vendors como evidência direcional, não exige recorte por tamanho de conta e trata a posição oficial ilegível como lacuna.
- Custos: pesquisa partindo do rascunho anterior, 76.809 tokens; curadoria, 21.432 (nota 3: só uma fonte para o horário do Instagram); rodada extra, 67.374; curadoria final, 26.746 (nota 4, arquivada). Total do v2: 192.361 tokens.
- Busca de teste depois do arquivamento: HIT. Auditoria: 0 problemas.

## Skills de YouTube (Jakeschincariol/youtube-agent-skill), instaladas em 2026-10-21

- Auditoria antes de instalar: 11 skills (`yt-*`) mais 6 scripts Python, licença MIT. Os scripts só leem os arquivos passados por argumento: nenhum acessa a rede, executa comandos ou lê credenciais. Os `SKILL.md` são só instruções de escrita. Nada publica no YouTube.
- Instalação: pastas `yt-*` em `.claude/skills/` (escopo do projeto). A licença MIT ficou em `yt-script/LICENSE`, e o modelo de perfil de voz em `escritorio/design/modelos/youtube-voice.md`.
- Teste: as 11 skills aparecem na sessão, `/yt-script` carrega e as 6 ferramentas rodam (`hookscore`, `title`, `deadair`, `chapters`, `retention`, `swipe`). `chapters`, `retention` e `swipe` recusam amostras muito pequenas, por desenho.
- Limitação: o `hookscore.py` usa expressões em inglês. Com ganchos em português ele quase não reconhece fórmula e dá notas quase iguais (34 a 39, todas "WEAK"). Mesmo em inglês, todas ficaram "WEAK" (37 a 46). Serve como comparação relativa de ganchos em inglês, não como nota absoluta.
- Para escrever roteiros completos, a skill pede `~/.claude/youtube/voice.md`, que ainda não existe.

## Biblioteca de itens guardados (2026-10-21)

- Decisão do usuário: guardar skills e projetos externos para uso futuro, sem ativar. Criada `escritorio/biblioteca/` (catálogo em `INDEX.md`).
- As 11 skills de YouTube saíram de `.claude/skills/` e foram para `escritorio/biblioteca/youtube-agent-skill/`.
- Harvey (agente de vendas por e-mail frio) guardado inteiro, sem `.git`, `.github` e o GIF de 4,5 MB. O `CLAUDE.md` dele foi renomeado para `CLAUDE.md.original`, para não ser carregado como instrução.
- Playwright MCP (Microsoft) guardado em `escritorio/biblioteca/playwright-mcp/`, inativo. É uma casca de ~50 linhas sobre o pacote `playwright`; o catálogo (`INDEX.md`) traz os cuidados e a alternativa Playwright CLI.

## Medição real (2026-10-21)

- Comandos novos no `acervo.py`: `custo` registra os tokens de cada etapa de um pedido; `marcar` reclassifica eventos; `--teste` deixa um evento fora do `stats`. O `stats` passou a usar só custos medidos.
- O registro foi corrigido: a linha 5 era teste, e as linhas 6, 7 e 9 eram HITs falsos (o peso do cache na cota estava marcado como não verificado).
- Os custos de hoje foram lançados com base nos `subagent_tokens` de cada chamada.
- Resultado real: **reaproveitamento 0 de 6 buscas**; 838.062 tokens de subagente gastos; 112.057 deles perdidos com falhas de ferramenta; **279.354 tokens por pesquisa arquivada**; economia medida até agora: zero.
- O `stats` antigo mostrava 57% de reaproveitamento e cerca de 456 mil tokens economizados.

## Pesquisa de ferramentas de IA para redes sociais (2026-10-21)

- Primeiro pedido real usando o fluxo completo e o registro de custo. Arquivada com nota 4 depois de uma rodada extra. Custo: 241.630 tokens (pesquisa 96.698, rodada 90.508, duas curadorias somando 54.424).
- Defeito encontrado e corrigido no `checar`: ele só contava `[verificado]` escrito exatamente assim e ignorava marcas com ressalva, como `[verificado, 2026-10-21]`. Neste relatório havia 24 verificadas, não 8. As notas provisórias das outras pesquisas não mudaram, exceto a da primeira versão de frequência de posts (descartada), que subiu de 3 para 4. Aquele descarte foi decidido pela curadoria por conteúdo, então continua valendo.
- Playwright instalado (2026-10-22): MCP do projeto via `.mcp.json` e `.claude/mcp/playwright.sh`, e modo `--js` no `ler_pagina.py` para os pesquisadores. Leu os preços do Vizard montados por JavaScript; o Canva continua bloqueado pelo Cloudflare. As 25 ferramentas do MCP custam cerca de 5.300 tokens por sessão.

## Andar jurídico (2026-10-22)

- Criado o andar `juridico`, com as pastas pedidos, respostas e modelos, o `diretor-juridico` (Haiku, reservado) e o `redator-contratos` (Sonnet). O redator não pesquisa na web: parte dos modelos do andar, busca a base legal no acervo e devolve os `PEDIDOS_DE_PESQUISA` do que faltar. As minutas ficam em `escritorio/privado/juridico/`, fora do git.
- A pesquisa jurídica continua no andar de Pesquisa, feita pelo `pesquisador-legal`, cujo roteamento ganhou 18 palavras (cláusula, jurisprudência, CDC, STJ...). Os dois testes de `rotear` deram `ROTA` por regra.
- Tipo novo: `jurisprudencia`, com validade de 90 dias.
- Regra nova do `checar`: perde 1 ponto o item de Achados que cita artigo, lei, resolução, súmula ou decisão sem fonte oficial (.gov.br, .jus.br, .leg.br ou conselho profissional). Itens já marcados [não verificado] não contam de novo. As 5 pesquisas arquivadas mantiveram a nota provisória.
- `escritorio/juridico/modelos/checklist-revisao.md`: os 11 artigos citados (CC 412, 413, 473, 598; CDC 49, 51; Lei 9.610, art. 49; LGPD 7º e 39; CPC 63; Lei 14.063, art. 4º) foram conferidos no Planalto com o `ler_pagina.py`.

## Economia de tokens, itens 1 a 5 (2026-10-22)

Custo medido até aqui: 2,43 milhões de tokens de subagente, ou 243 mil por pesquisa arquivada. Divisão: pesquisa 50%, curadoria 19%, rodadas extras 16%, redação 8%, falhas 5%, triagem por agente 3%.

1. **Fontes bloqueadas.** `references/dominios-bloqueados.json` começa com 6 domínios. O `ler_pagina.py` responde `BLOQUEADO` na hora e anota sozinho bloqueios novos de Cloudflare (401/403 com `cf-mitigated`, ou desafio no `--js`); `--forcar` ignora a lista. Todo pedido novo traz o critério "fonte bloqueada vira [não verificado: leitura humana] e não pede rodada extra". A curadoria devolve `LEITURA_HUMANA` em vez de pedir rodada.
2. **Páginas menores.** A saída padrão do `ler_pagina.py` caiu de 15.000 para 5.000 caracteres, com aviso para usar `--buscar` quando corta. Os 6 pesquisadores passam a começar sempre com `--buscar`.
3. **Leitura por seção.** `acervo.py ler <id> --secao achados,incertezas --angulo "<termo>"`. No teste, o ângulo "google" da pesquisa de anúncio pago deu 4,6 mil caracteres, contra 33 mil da pesquisa inteira. O redator passou a usar isso e a manter a minuta em pasta, um arquivo por parte. A minuta da Criativos Digitais foi dividida em 8 arquivos: corpo com 5,7 mil palavras, anexos de 77 a 1,4 mil e revisão com 2,4 mil.
4. **Curadoria leve.** `acervo.py pacote <relatorio>` monta pergunta, resumo, ângulos (com itens, fontes e marcas), contrapontos, incertezas e fontes. No teste deu 10,5 mil caracteres, contra 32 mil do relatório. O diretor julga pelo pacote e usa `grep` para conferir pontos.
5. **Nível rápido.** O `triar` desce de padrão para rápida em `VENCIDA` e em `PARCIAL` com até 3 termos faltando. A política lista os casos de confirmação pontual (`--nivel rapida` + `--rapida-ok`).

Efeito esperado: de 243 mil para 140 a 160 mil tokens por pesquisa arquivada. A ser confirmado pelo `stats` nas próximas pesquisas.
