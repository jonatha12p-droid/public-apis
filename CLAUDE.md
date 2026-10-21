# Escritório virtual de agentes

Regra principal: **toda pesquisa passa pela skill `escritorio-acervo`; nunca pesquisar sem consultar o acervo.**

- Acervo: `escritorio/acervo/` (comando: `python3 .claude/skills/escritorio-acervo/scripts/acervo.py <comando>`, rodado da raiz).
- Pedidos entre andares: arquivo curto em `escritorio/<andar-destino>/pedidos/`; a resposta (resumo + caminho) volta em `escritorio/<andar-origem>/respostas/`.
- Pedido de pesquisa: acione o subagente `diretor-pesquisa`. Desenvolvimento pede pesquisa via `diretor-desenvolvimento`.
- Entre andares, passe resumo + caminho, nunca o texto completo.
- Economia vem de reaproveitar; nunca corte a profundidade de pesquisa inédita.
