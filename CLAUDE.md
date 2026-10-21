# Escritório virtual de agentes

Regra principal: **toda pesquisa passa pela skill `escritorio-acervo`; nunca pesquisar sem consultar o acervo.**

- Acervo: `escritorio/acervo/` (comando: `python3 .claude/skills/escritorio-acervo/scripts/acervo.py <comando>`, rodado da raiz).
- Pedidos entre andares: arquivo curto em `escritorio/<andar-destino>/pedidos/`; a resposta (resumo + caminho) volta em `escritorio/<andar-origem>/respostas/`.
- Andares: pesquisa, desenvolvimento, marketing, redes-sociais, analise-dados, design.
- Fluxo de pesquisa (sessão principal; o que é script não gasta token): `acervo.py pedir` → `acervo.py triar` (no HIT já responde) → pesquisador indicado → `acervo.py checar` → `diretor-pesquisa` (só curadoria) → arquivar + `acervo.py responder`. Detalhes na skill `escritorio-acervo`.
- Não abra subagente para o que o script faz (cada um custa de 13 a 50 mil tokens, medido).
- Acervo único para todos os andares e projetos: `escritorio/acervo/`.
- Entre andares, passe resumo + caminho, nunca o texto completo.
- Economia vem de reaproveitar; nunca corte a profundidade de pesquisa inédita.
