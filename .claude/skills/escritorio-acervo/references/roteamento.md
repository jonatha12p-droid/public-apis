# Roteamento por regras

O roteador (`acervo.py rotear`) lê `references/roteamento.json` e compara as palavras do pedido com as palavras-chave de cada agente. Resolve a maioria dos pedidos sem gastar token.

## Como editar a tabela

```json
{
  "padrao": "pesquisador-geral",
  "agentes": [
    {"nome": "pesquisador-mercado", "andar": "pesquisa",
     "palavras": ["mercado", "concorrente", "preço", "tendência"]}
  ]
}
```

- Cada agente tem de 8 a 20 palavras-chave. Inclua variações e termos em inglês.
- Um agente é escolhido sozinho quando casa pelo menos 2 termos e tem 1 termo de vantagem sobre o segundo colocado. Ajuste com `--minimo` e `--margem`.
- Se der `AMBIGUO`, o modelo menor decide só entre os candidatos listados, vendo apenas o pedido e os 2 ou 3 nomes. Isso custa poucas centenas de tokens.
- Use `acervo.py stats` para ver a fração de rotas resolvidas só por regra. Se ficar abaixo de 70%, melhore as palavras-chave.

## Pedidos entre andares

O andar solicitante grava o pedido em `<andar-destino>/pedidos/` (um `.md` por pedido, com a pergunta e o contexto mínimo). O diretor do andar de destino processa, e a resposta (resumo + caminho) volta em `<andar-origem>/respostas/`. Conversa longa entre andares é o que mais gasta contexto; prefira arquivos curtos.
