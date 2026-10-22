# Política de pesquisa nova

Objetivo: pesquisas **fundas e verificadas**. A economia do escritório vem do reaproveitamento, não de cortar a profundidade. Em testes da Anthropic com sistemas multiagente, o uso de tokens explicou cerca de 80% da variação de desempenho em pesquisa; gastar mais, de forma bem distribuída, melhora o resultado.

## Níveis

Os valores são orçamentos de **referência** (estimativas), não limites impostos.

| Nível | Quando usar | Buscas | Páginas lidas por inteiro | Orçamento de referência |
|---|---|---|---|---|
| Rápida | Pergunta factual simples, um dado pontual | 3 a 6 | 2 a 3 | 20 a 40 mil tokens |
| **Padrão** (mínimo para MISS) | Tema novo, comparação, "como funciona", "o que existe sobre" | 10 a 15 | 5 a 8 | **80 a 160 mil tokens** |
| Profunda | Decisão cara, tema controverso ou em mudança rápida, base para projeto | 20 a 30 | 10 a 15 | 200 a 350 mil tokens |

Em dúvida entre dois níveis, escolha o maior. Pesquisa rasa arquivada contamina o acervo e é reaproveitada depois como se fosse boa.

**Quando a rápida basta** (o `triar` já desce para rápida nos dois primeiros casos):
- atualização de pesquisa vencida (`VENCIDA`): só o que mudou desde a data da base;
- lacuna pequena de uma pesquisa existente (`PARCIAL` com até 3 termos faltando);
- confirmação pontual: "o artigo X ainda diz Y?", "o preço do plano Z mudou?", "o termo de uso ainda permite W?". Peça com `--nivel rapida` e, no `triar`, use `--rapida-ok`.

Tema novo, comparação ou base para decisão continua no padrão ou no profundo.

## Método (níveis padrão e profundo)

1. **Plano antes de buscar.** Decomponha em 3 a 5 sub-perguntas (ângulos) e escreva para cada uma o critério de "respondida".
2. **Do amplo ao estreito.** Comece com buscas curtas e genéricas, depois refine com os termos que as primeiras descobertas revelarem.
3. **Leia a fonte, não só o trecho.** Abra as melhores páginas inteiras. Resumo de resultado de busca não sustenta afirmação importante.
4. **Triangule.** Toda afirmação-chave precisa de 2 ou mais fontes independentes. Prefira fontes primárias (documentação oficial, artigo original, dados do órgão). Anote a data de cada fonte.
5. **Procure o contraponto.** Faça pelo menos 1 busca dedicada a críticas, limitações, falhas ou evidência contrária.
6. **Segunda rodada de lacunas.** Depois do primeiro rascunho, liste o que falta ou está fraco e faça uma rodada extra de buscas só para isso.
7. **Passe de verificação.** Releia números, datas e citações contra a fonte. Marque cada afirmação-chave como `[verificado]` ou `[não verificado]`.
8. **Síntese separada.** Deixe claro o que é fato (com fonte), o que é interpretação e o que é incerteza.

**Nível profundo:** divida os ângulos entre subagentes em paralelo, cada um com contexto próprio. Cada subagente devolve relatório condensado (até cerca de 1.000 palavras, com fontes) e salva notas brutas em arquivo. O diretor lê só os relatórios.

## Quando parar

Pare quando **duas buscas seguidas não trouxerem informação nova relevante** ou quando o orçamento do nível acabar. Se parar pelo orçamento com lacunas importantes, registre-as na seção de incertezas em vez de esconder.

## Fontes bloqueadas

Alguns sites bloqueiam robôs (Cloudflare e afins) e não abrem nem com `--js`. A lista fica em `references/dominios-bloqueados.json`; o `ler_pagina.py` responde `BLOQUEADO` na hora e anota sozinho bloqueios novos. Fonte bloqueada vira `[não verificado: fonte bloqueada, leitura humana]` no relatório e entra na seção de incertezas. **Isso não justifica rodada extra**: uma nova rodada bate no mesmo bloqueio. Se a pergunta central depender dela, a curadoria devolve `LEITURA_HUMANA` com as URLs, para o usuário ler e enviar o texto.

## Onde NÃO gastar tokens

- Ler página inteira quando `--buscar` resolve; cada página lida fica no contexto até o fim e encarece todas as chamadas seguintes.
- Tentar várias URLs de um site que já respondeu 401/403 de anti-robô.
- Reler a mesma página duas vezes.
- Colar resultados brutos de busca no contexto do diretor.
- Repetir instruções que já estão no prompt fixo.
- Refazer pesquisa que o acervo já cobre (resultado `HIT`).

## Checklist de curadoria (o diretor usa para dar a nota)

Cada item atendido vale 1 ponto, de 0 a 5 após o ajuste abaixo.

- [ ] Cobre pelo menos 3 ângulos distintos do tema.
- [ ] Número mínimo de fontes distintas: 8 (padrão) ou 15 (profunda).
- [ ] Inclui fontes primárias quando existem.
- [ ] Tem contraponto, críticas ou limitações.
- [ ] Tem seção de incertezas e lacunas, com datas das fontes.

Ajuste: se alguma afirmação central não tem fonte, ou há número sem verificação, desconte 1 ponto. Nota 4 ou 5 arquiva; 3 volta ao agente com lacunas específicas; 1 ou 2 descarta.

## Direitos autorais

Parafraseie. Não copie trechos longos das fontes para o relatório; cite no máximo frases curtas, entre aspas, com a fonte.
