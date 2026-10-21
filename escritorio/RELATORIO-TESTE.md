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
