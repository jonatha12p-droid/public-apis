---
name: escritorio-acervo
description: Use quando um diretor de andar do escritório virtual recebe um pedido de pesquisa (de outro andar ou do usuário), antes de acionar qualquer agente pesquisador. Consulta o acervo local para reaproveitar pesquisas existentes, roteia o pedido ao agente certo, define a profundidade da pesquisa nova, faz a curadoria e arquiva o resultado. Também use para arquivar, buscar, listar ou renovar pesquisas vencidas.
---

# Escritório Acervo

Fluxo do diretor de andar: **reaproveitar antes de pesquisar, e pesquisar fundo quando for preciso.**

A economia vem de não repetir trabalho (consulta, roteamento e arquivamento rodam em script local, sem LLM). O que sobra em tokens é investido em pesquisas novas mais profundas. Nunca economize cortando a profundidade de uma pesquisa inédita.

## Fluxo

1. **Entender o pedido.** Reescreva em uma linha e extraia de 3 a 6 palavras-chave.
2. **Rotear.** Rode o roteador por regras (sem LLM):
   `python scripts/acervo.py rotear "<pedido>" --tabela references/roteamento.json`
   - `ROTA:` use o agente indicado.
   - `AMBIGUO:` decida só entre os candidatos listados (modelo menor basta).
   - `SEM_CANDIDATO:` use o agente padrão ou pergunte ao solicitante.
3. **Consultar o acervo antes de pesquisar.**
   `python scripts/acervo.py buscar "<pedido em poucas palavras>"`
   Use `--andar` para limitar a um andar. Leia o campo `RESULTADO`:

   | Resultado | O que fazer |
   |---|---|
   | `HIT` | Responda com o **resumo**. Abra o arquivo completo (`ler <id> --completo`) só se o resumo não bastar. Custo: poucos mil tokens. |
   | `PARCIAL` | Parta do resumo e pesquise **só a lacuna** (termos listados em `ACAO`). Use o nível de profundidade normal para a lacuna. |
   | `VENCIDA` | Atualização incremental: leia a pesquisa antiga, pesquise o que mudou desde a data de criação e arquive a nova versão (a antiga vai para `_historico`). |
   | `MISS` | Pesquisa nova, em **nível padrão ou profundo** (próximo passo). |

4. **Pesquisa nova: não seja raso.** Siga `references/politica-pesquisa.md`. Nível padrão é o mínimo para qualquer MISS que não seja pergunta factual simples. Escolha o nível e diga ao agente pesquisador qual é.
5. **Curadoria.** Avalie o resultado com o checklist de `references/politica-pesquisa.md` (nota de 1 a 5).
   - Nota 4 ou 5: arquive.
   - Nota 3: devolva ao agente com as lacunas específicas (no máximo 1 rodada extra).
   - Nota 1 ou 2: descarte e registre o motivo.
6. **Arquivar.** O resumo de até 700 caracteres é escrito pelo modelo menor; o resto é script:
   ```
   python scripts/acervo.py arquivar --arquivo <relatorio.md> --andar pesquisa \
     --titulo "..." --tipo mercado --tags "a,b,c" --resumo "..." \
     --fontes "url1 | url2" --nota 4
   ```
   Tipos e validade padrão: preco 3d, noticia 7d, mercado 30d, ia 30d, redes-sociais 30d, legislacao 60d, ferramenta 60d, tecnologia 90d, conceito e pesquisa-academica 365d. Use `--validade-dias` para exceções.
7. **Entregar ao andar solicitante** o **resumo + caminho do arquivo**, nunca o texto completo. Quem precisar de detalhe abre o arquivo.

## Regras de economia (sem perder qualidade)

- Nunca leia uma pesquisa completa só para decidir se serve. Decida pelo resumo.
- Nunca cole resultado bruto de busca no contexto do diretor. Agentes devolvem relatório condensado + caminho do arquivo.
- Comunicação entre andares é por arquivo e pasta, não por conversa longa.
- Mantenha as instruções fixas (este SKILL.md, prompt do diretor) no **início** do contexto e sem alterações, para aproveitar prompt caching (leitura de cache custa 10% da entrada; escrita custa 125%; expira em 5 minutos, ou 1 hora se estendido).
- Tarefas sem urgência (reindexar, resumir em lote, curadoria acumulada) podem ir pela Batch API, que cobra 50%.
- Modelo menor (Haiku) para: roteamento ambíguo, resumos de arquivamento, curadoria simples. Modelo maior (Sonnet; Opus em pesquisa profunda crítica) para: pesquisa, síntese e verificação.
- Carregue os arquivos de `references/` só quando o passo correspondente chegar.

## Manutenção

- `acervo.py vencidas` lista o que precisa de renovação. Renove só o que tem uso recente.
- `acervo.py stats` mostra taxa de reaproveitamento e economia estimada. Revise a cada semana; se `HIT` for baixo, as palavras-chave ou tags estão ruins.
- `acervo.py reindexar` reconstrói o índice a partir dos `.md` se você editar arquivos à mão.
- `acervo.py init --andares pesquisa,desenvolvimento` cria a estrutura inicial.
- Raiz do acervo: `--raiz`, variável `ESCRITORIO_ACERVO` ou `./escritorio/acervo`.

## Limites honestos

- A busca é lexical (BM25 + cobertura de termos), não semântica. Funciona bem com tags e títulos bons; sinônimos raros podem gerar `MISS` falso. Compensação: peça tags generosas no arquivamento.
- Os orçamentos de tokens em `references/politica-pesquisa.md` são **referências**, não limites impostos. Para impor teto de verdade, defina `max_tokens` e número de turnos na chamada do agente.
- Pesquisa vencida pode estar desatualizada. Respeite a validade.
