#!/usr/bin/env bash
# Inicia o Playwright MCP com a versao fixada. Detecta o ambiente na nuvem do
# Claude Code (Chromium em /opt/pw-browsers, root sem sandbox, proxy em
# HTTPS_PROXY) e acrescenta as opcoes so quando elas se aplicam.
extra=()
if [ -x /opt/pw-browsers/chromium ]; then
  extra+=(--executable-path /opt/pw-browsers/chromium)
fi
if [ "$(id -u)" = "0" ]; then
  extra+=(--no-sandbox)
fi
if [ -n "${HTTPS_PROXY:-}" ]; then
  extra+=(--proxy-server "$HTTPS_PROXY")
fi
exec npx -y @playwright/mcp@0.0.83 --headless --isolated --output-dir /tmp/playwright-mcp "${extra[@]}" "$@"
