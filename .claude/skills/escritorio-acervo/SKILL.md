---
name: escritorio-acervo
description: Use antes de qualquer pesquisa do escritório virtual (pedido de um andar ou do usuário), antes de acionar qualquer agente pesquisador. Consulta o acervo local para reaproveitar pesquisas existentes, roteia o pedido ao agente certo, define a profundidade da pesquisa nova, faz a curadoria e arquiva o resultado. Também use para arquivar, buscar, listar ou renovar pesquisas vencidas.
---

# Escritório Acervo

Fluxo do diretor de andar: **reaproveitar antes de pesquisar, e pesquisar fundo quando for preciso.**

A economia vem de não repetir trabalho (consulta, roteamento e arquivamento rodam em script local, sem LLM). O que sobra em tokens é investido em pesquisas novas mais profundas. Nunca economize cortando a profundidade de uma pesquisa inédita.

## Fluxo

Quem orquestra é a sessão principal. Só a pesquisa e o julgamento da curadoria usam agente; o resto é script. `A` = `python3 .claude/skills/escritorio-acervo/scripts/acervo.py`, rodado da raiz do projeto.

1. **Pedir.** Escreva a pergunta em 1 a 3 linhas e de 3 a 6 palavras-chave:
   `A pedir --de <andar> --pergunta "..." --palavras "a b c" --criterio "..." --criterio "..." [--para-que "..."] [--nivel padrao]`
   Se sair `JA_RESPONDIDO`, use a resposta existente.
2. **Triar** (rotear + buscar, sem LLM): `A triar <pedido>`
   - `HIT`: o script já grava a resposta no andar de origem. Fim.
   - `PARCIAL` / `VENCIDA` / `MISS`: sai um bloco `DECISAO` (agente, nível, escopo, pergunta, critérios, caminho de saída). Se o agente vier como `ESCOLHA entre ...`, escolha um dos listados.
3. **Pesquisar.** Acione o agente pesquisador indicado com o bloco `DECISAO`. Nunca baixe o nível para economizar (ver `references/politica-pesquisa.md`).
4. **Checar** (checklist mecânico): `A checar <relatorio> --nivel <nivel>` dá a `NOTA_PROVISORIA`.
5. **Curadoria.** Acione o `diretor-pesquisa` com: pedido, relatório, saída do `checar` e a devolução do pesquisador. Ele julga o que o script não vê, confirma ou corrige a nota e:
   - nota 4 ou 5: arquiva (`A arquivar ...`) e responde (`A responder <pedido> --id <id>`);
   - nota 3: devolve as lacunas; acione o pesquisador de novo (no máximo 1 rodada extra);
   - nota 1 ou 2: `A responder <pedido> --descartar "motivo"`.
6. **Entregar** ao andar solicitante só o resumo + caminho (já está no arquivo de resposta).
7. **Registrar o custo** de cada subagente acionado, logo depois que ele terminar, com o `subagent_tokens` que a ferramenta Agent relatou:
   `A custo <pedido> --etapa triagem|pesquisa|rodada|curadoria|falha|hit --tokens N`
   Use `falha` para rodadas perdidas por problema de ferramenta. Num HIT resolvido só por script, registre `--etapa hit --tokens 0`. Sem isso o `stats` não consegue medir a economia.

Tipos e validade padrão: preco 3d, noticia 7d, mercado 30d, ia 30d, redes-sociais 30d, legislacao 60d, ferramenta 60d, tecnologia 90d, conceito e pesquisa-academica 365d. Use `--validade-dias` no `arquivar` para exceções.

## Regras de economia (sem perder qualidade)

- Nunca leia uma pesquisa completa só para decidir se serve. Decida pelo resumo.
- Nunca cole resultado bruto de busca no contexto do diretor. Agentes devolvem relatório condensado + caminho do arquivo.
- Comunicação entre andares é por arquivo e pasta, não por conversa longa.
- Mantenha as instruções fixas (este SKILL.md, prompt do diretor) no **início** do contexto e sem alterações, para aproveitar prompt caching (leitura de cache custa 10% da entrada; escrita custa 125%; expira em 5 minutos, ou 1 hora se estendido).
- Tarefas sem urgência (reindexar, resumir em lote, curadoria acumulada) podem ir pela Batch API, que cobra 50%.
- Modelo menor (Haiku) para: roteamento ambíguo, resumos de arquivamento, curadoria simples. Modelo maior (Sonnet; Opus em pesquisa profunda crítica) para: pesquisa, síntese e verificação.
- Carregue os arquivos de `references/` só quando o passo correspondente chegar.

## Manutenção

- `acervo.py auditar` revisa o acervo sem gastar tokens: resumos fracos, poucas tags, incertezas fora do resumo, assuntos repetidos, HITs falsos no registro, pedidos sem resposta e arquivos fora do índice. Se terminar com `CURADOR: acione`, chame o agente `curador-acervo` só com os itens `[curador]`. Os itens `[diretor]` (vencidas, pedidos abertos) e `[script]` (reindexar, roteamento) não precisam dele.
- `acervo.py vencidas` lista o que precisa de renovação. Renove só o que tem uso recente.
- `acervo.py stats` mostra o reaproveitamento real (sem testes e sem HITs falsos), o custo medido por pedido, o custo por pesquisa arquivada e a economia medida. Ele só conta tokens de subagente: a sessão principal não é medida.
- Testes: passe `--teste` depois do subcomando (ou `ESCRITORIO_TESTE=1`), e o evento fica fora do `stats`.
- `acervo.py marcar --linha N --como teste|hit-falso|real` corrige a classificação de um evento já registrado (por exemplo, um HIT que a auditoria apontou como falso). Revise a cada semana; se `HIT` for baixo, as palavras-chave ou tags estão ruins.
- `acervo.py reindexar` reconstrói o índice a partir dos `.md` se você editar arquivos à mão.
- `acervo.py init --andares pesquisa,desenvolvimento` cria a estrutura inicial.
- Raiz do acervo: `--raiz`, variável `ESCRITORIO_ACERVO` ou `./escritorio/acervo`.

## Limites honestos

- Frases do resumo com "Incertezas:", "não verificado", "lacuna", "inferência" ou "não testado" não contam para `HIT`. Ao arquivar, ponha as incertezas no fim do resumo, depois de "Incertezas:".
- A busca é lexical (BM25 + cobertura de termos), não semântica. Funciona bem com tags e títulos bons; sinônimos raros podem gerar `MISS` falso. Compensação: peça tags generosas no arquivamento.
- Os orçamentos de tokens em `references/politica-pesquisa.md` são **referências**, não limites impostos. Para impor teto de verdade, defina `max_tokens` e número de turnos na chamada do agente.
- Pesquisa vencida pode estar desatualizada. Respeite a validade.
