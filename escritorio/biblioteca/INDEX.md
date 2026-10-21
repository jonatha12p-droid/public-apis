# Biblioteca (guardado, inativo)

Material guardado para uso futuro. **Nada aqui é carregado como skill, agente ou instrução**: o Claude Code só descobre skills em `.claude/skills/` e agentes em `.claude/agents/`. Para ativar algo, copie para lá (comandos abaixo) e abra uma sessão nova.

Antes de ativar qualquer item, reveja a seção "Cuidados". Cada item é um instantâneo do repositório de origem, sem o histórico do git.

## youtube-agent-skill

| | |
|---|---|
| Origem | https://github.com/Jakeschincariol/youtube-agent-skill |
| Versão guardada | commit `a2feb21` (2026-09-16), licença MIT (arquivo em `skills/yt-script/LICENSE`) |
| O que é | 11 skills de YouTube (`yt-script`, `yt-package`, `yt-edit`, `yt-retention`, `yt-viral`, `yt-shorts`, `yt-seo`, `yt-chapters`, `yt-comment`, `yt-plan`, `yt-audit`) e 6 ferramentas em Python |
| Andares prováveis | redes-sociais, marketing, design |
| Análise | Auditado em 2026-10-21: os scripts só leem os arquivos passados por argumento, sem rede nem execução de comandos. Nada publica no YouTube |
| Testado | Sim: as 11 skills carregaram e as 6 ferramentas rodaram |

Ativar: `cp -r escritorio/biblioteca/youtube-agent-skill/skills/yt-* .claude/skills/`

Cuidados:
- O `hookscore.py` só reconhece padrões em inglês. Com ganchos em português as notas ficam quase iguais (34 a 39).
- `/yt-script` pede `~/.claude/youtube/voice.md`. O modelo para preencher está em `templates/voice.md`.
- As 11 descrições entram na lista de skills de toda sessão.

## harvey

| | |
|---|---|
| Origem | https://github.com/ethanplusai/harvey |
| Versão guardada | commit `55866a1` (2026-10-21), licença MIT |
| O que é | Agente autônomo de vendas por e-mail frio: acha empresas, escreve a sequência de e-mails, envia, lê as respostas e conduz a conversa. Usa a assinatura do Claude (ou do ChatGPT, via Codex) pela linha de comando, sem chave de API. Tem painel local na porta 5555 |
| O que foi guardado | Tudo, menos `.git`, `.github` e o GIF de 4,5 MB de `docs/` |
| Andares prováveis | marketing (vendas e prospecção), analise-dados |

Parte aproveitável sem rodar o programa, em português seria preciso adaptar:
- `skills/*.md`: 9 arquivos de conhecimento de vendas (`email_frameworks`, `objection_handling`, `lead_qualification`, `signal_playbook`, `offer_strategy`, `sales_methodology`, `prospecting_tactics`, `account_navigation`, `linkedin_outreach`). São texto puro e escrito em inglês.
- `prompts/*.md`: prompts dos agentes Scout, Writer e Handler.
- `harvey/agents/`: a divisão em Scout, Writer, Sender, Handler e Analyst.

O `CLAUDE.md` do projeto foi renomeado para `CLAUDE.md.original`. Com o nome original ele seria carregado como instrução sempre que se trabalhasse nessa pasta.

Análise: **superficial**. Olhei a estrutura, procurei segredos (nenhum) e listei os endereços que o código contata (OpenStreetMap, Hunter, Serper, DataForSEO, Instantly, Microsoft Graph, listas de spam e Precleared). Não li o código linha a linha e não rodei nada.

Cuidados antes de usar:
- **Envia e-mail de verdade** em nome de quem configurar. Pelo README o envio passa por aprovação, mas isso não foi testado aqui.
- **Legislação:** cold email para o Brasil envolve LGPD e as regras de consentimento. O próprio README trata de GDPR, CASL e outras leis, mas não da LGPD.
- **Privacidade:** a checagem opcional do Precleared envia o e-mail de cada contato a um serviço de terceiros (`precleared.dev`).
- **Cota:** roda em ciclos de 15 minutos usando a cota da assinatura. O consumo pode ser alto.
- **Credenciais:** precisa de um `.env` com acesso a e-mail e chaves de serviços. Nunca guardar esse arquivo no repositório.
- **LinkedIn:** o README avisa que automatizar o LinkedIn viola os termos de uso.
