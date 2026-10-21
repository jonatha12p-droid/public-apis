# Escritório virtual de agentes

Regra principal: **toda pesquisa passa pela skill `escritorio-acervo`; nunca pesquisar sem consultar o acervo.**

- Acervo: `escritorio/acervo/` (comando: `python3 .claude/skills/escritorio-acervo/scripts/acervo.py <comando>`, rodado da raiz).
- Pedidos entre andares: arquivo curto em `escritorio/<andar-destino>/pedidos/`; a resposta (resumo + caminho) volta em `escritorio/<andar-origem>/respostas/`.
- Andares: pesquisa, desenvolvimento, marketing, redes-sociais, analise-dados, design. Cada um tem `diretor-<andar>`; os demais pedem pesquisa ao `diretor-pesquisa`.
- Antes de acionar o `diretor-pesquisa`, rode `acervo.py buscar "<palavras-chave>"` na sessão principal. Se der HIT, use o resumo e não abra subagente (abrir um custa ~50 mil tokens, medido).
- Acervo único para todos os andares e projetos: `escritorio/acervo/`.
- Entre andares, passe resumo + caminho, nunca o texto completo.
- Economia vem de reaproveitar; nunca corte a profundidade de pesquisa inédita.
