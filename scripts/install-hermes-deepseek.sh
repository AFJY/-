#!/usr/bin/env bash
# Install or update Hermes Agent and configure DeepSeek as the LLM backend.
set -euo pipefail

HERMES_HOME="${HERMES_HOME:-$HOME/.hermes}"
DEEPSEEK_MODEL="${DEEPSEEK_MODEL:-deepseek-v4-pro}"
DEEPSEEK_BASE_URL="${DEEPSEEK_BASE_URL:-https://api.deepseek.com/v1}"

echo "==> Installing / updating Hermes Agent..."
curl -fsSL https://raw.githubusercontent.com/NousResearch/hermes-agent/main/scripts/install.sh \
  | bash -s -- --skip-setup --skip-browser

export PATH="${HOME}/.local/bin:${PATH}"

echo "==> Updating to latest main..."
if [ -d "${HERMES_HOME}/hermes-agent/.git" ]; then
  git -C "${HERMES_HOME}/hermes-agent" fetch origin main
  git -C "${HERMES_HOME}/hermes-agent" pull --ff-only origin main || true
  if command -v uv >/dev/null 2>&1; then
    VENV_PY="${HERMES_HOME}/hermes-agent/venv/bin/python"
    if [ -x "${VENV_PY}" ]; then
      uv pip install --python "${VENV_PY}" -e "${HERMES_HOME}/hermes-agent[all]"
    fi
  fi
fi

echo "==> Configuring DeepSeek provider..."
hermes config set model.provider deepseek
hermes config set model.default "${DEEPSEEK_MODEL}"
hermes config set model.base_url "${DEEPSEEK_BASE_URL}"

if [ -n "${DEEPSEEK_API_KEY:-}" ]; then
  hermes config set DEEPSEEK_API_KEY "${DEEPSEEK_API_KEY}"
  echo "==> DEEPSEEK_API_KEY written to ${HERMES_HOME}/.env"
else
  echo ""
  echo "WARN: DEEPSEEK_API_KEY is not set."
  echo "  export DEEPSEEK_API_KEY='sk-...'"
  echo "  hermes config set DEEPSEEK_API_KEY \"\$DEEPSEEK_API_KEY\""
  echo "  Or run: hermes setup"
fi

echo ""
echo "==> Hermes version:"
hermes --version || true

echo ""
echo "==> Health check:"
hermes doctor || true

echo ""
echo "Done. Start chatting with: hermes"
echo "Optional messaging gateway: hermes gateway install && hermes gateway start"
