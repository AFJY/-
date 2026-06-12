#!/usr/bin/env bash
# 一键启动 Stock AI 服务
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"

if [ -f "$HOME/.hermes/.env" ]; then
  set -a
  # shellcheck disable=SC1091
  source "$HOME/.hermes/.env" 2>/dev/null || true
  set +a
fi

export PATH="$HOME/.local/bin:$PATH"
echo "Starting Stock AI on http://0.0.0.0:8765"
exec python3 main.py serve
