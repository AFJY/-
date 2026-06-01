#!/usr/bin/env bash
# Install Hermes Agent + DeepSeek config + ALL optional Python/system deps
# that do not require third-party API keys.
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
bash "${SCRIPT_DIR}/install-hermes-deepseek.sh"

export PATH="${HOME}/.local/bin:${HOME}/.npm-global/bin:${PATH}"
HERMES_ROOT="${HERMES_HOME:-$HOME/.hermes}/hermes-agent"
VENV="${HERMES_ROOT}/venv"

echo "==> Installing all lazy / optional Python packages..."
"${VENV}/bin/python" -c "
from tools.lazy_deps import LAZY_DEPS
s=set()
for v in LAZY_DEPS.values():
    s.update(v)
s.add('ddgs')
for line in sorted(s):
    print(line)
" > /tmp/hermes-all-deps.txt

uv pip install --python "${VENV}/bin/python" -r /tmp/hermes-all-deps.txt

echo "==> Post-install (node, browser, ripgrep, ffmpeg)..."
hermes postinstall

echo "==> Playwright Chromium..."
cd "${HERMES_ROOT}"
npx --yes playwright install chromium 2>/dev/null || true
if command -v sudo >/dev/null && sudo -n true 2>/dev/null; then
  sudo DEBIAN_FRONTEND=noninteractive npx playwright install-deps chromium 2>/dev/null || true
fi

echo "==> Free web search (no API key)..."
hermes config set web.search_backend ddgs

echo "==> Skills Hub init..."
hermes skills list >/dev/null || true

echo "==> Docker (optional terminal backend)..."
if ! command -v docker >/dev/null 2>&1; then
  if command -v sudo >/dev/null && sudo -n true 2>/dev/null; then
    sudo DEBIAN_FRONTEND=noninteractive apt-get update -qq
    sudo DEBIAN_FRONTEND=noninteractive apt-get install -y -qq docker.io || true
  fi
fi

echo "==> Codex CLI (optional OAuth import)..."
mkdir -p "${HOME}/.npm-global"
npm config set prefix "${HOME}/.npm-global" 2>/dev/null || true
export PATH="${HOME}/.npm-global/bin:${PATH}"
npm install -g @openai/codex 2>/dev/null || true

if ! grep -q 'npm-global/bin' "${HOME}/.bashrc" 2>/dev/null; then
  echo 'export PATH="$HOME/.npm-global/bin:$PATH"' >> "${HOME}/.bashrc"
fi

echo ""
echo "==> Doctor summary:"
hermes doctor || true

echo ""
echo "Remaining items need YOUR API keys / OAuth (see .env.example):"
echo "  DEEPSEEK_API_KEY, FAL_KEY, DISCORD_BOT_TOKEN, OPENROUTER_API_KEY,"
echo "  XAI_API_KEY, GITHUB_TOKEN, HASS_URL/HASS_TOKEN, Spotify auth, etc."
