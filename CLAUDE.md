# Escritório virtual de agentes

Regra principal: **toda pesquisa passa pela skill `escritorio-acervo`; nunca pesquisar sem consultar o acervo.**

- Acervo: `escritorio/acervo/` (comando: `python3 .claude/skills/escritorio-acervo/scripts/acervo.py <comando>`, rodado da raiz).
- Pedidos entre andares: arquivo curto em `escritorio/<andar-destino>/pedidos/`; a resposta (resumo + caminho) volta em `escritorio/<andar-origem>/respostas/`.
- Andares: pesquisa, desenvolvimento, marketing, redes-sociais, analise-dados, design, juridico.
- Fluxo de pesquisa (sessão principal; o que é script não gasta token): `acervo.py pedir` → `acervo.py triar` (no HIT já responde) → pesquisador indicado → `acervo.py checar` → `diretor-pesquisa` (só curadoria) → arquivar + `acervo.py responder`. Depois de cada subagente, registre os tokens com `acervo.py custo`. Detalhes na skill `escritorio-acervo`.
- Não abra subagente para o que o script faz (cada um custa de 13 a 50 mil tokens, medido).
- Jurídico: minutas pelo `redator-contratos`, que parte de `escritorio/juridico/modelos/` e pede a base legal ao acervo (`pedir --de juridico`). Minutas com dados de clientes só em `escritorio/privado/juridico/` (fora do git). Toda minuta sai com "Revisão humana necessária"; não é parecer de advogado.
- Acervo único para todos os andares e projetos: `escritorio/acervo/`.
- Skills e projetos guardados para uso futuro (inativos): `escritorio/biblioteca/INDEX.md`. Não ative nada de lá sem pedido do usuário.
- Entre andares, passe resumo + caminho, nunca o texto completo.
- Economia vem de reaproveitar; nunca corte a profundidade de pesquisa inédita.
