---
de: desenvolvimento
para: pesquisa
status: respondido
nivel_sugerido: padrao   # rapida | padrao | profunda
---
# Pergunta
Preços atuais da API da Anthropic para prompt caching e Batch API: multiplicadores de leitura/escrita de cache, TTL de 5 min e 1 h, tamanho mínimo de prefixo cacheável, desconto do Batch API, se o desconto de batch combina com cache, e limitações de ambos.

# Para que serve
Decidir como estruturar os prompts fixos dos diretores (o que fica no prefixo cacheável) e quais tarefas do sistema multiagente vão para Batch API.

# Respondida quando
- Multiplicadores de escrita e leitura de cache para cada TTL (5 min e 1 h) com valores atuais.
- Tamanho mínimo de prefixo cacheável por modelo, e se varia por modelo.
- Desconto do Batch API e se ele combina com cache (ou não), com a fonte oficial.
- Limitações relevantes (latência do batch, janela de processamento, limites de cache, invalidação por mudança no prefixo).
