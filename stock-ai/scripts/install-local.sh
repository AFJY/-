#!/usr/bin/env bash
# Stock AI 本机部署 (Linux/macOS)
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"

echo "==> Stock AI 本机安装"
python3 -m pip install --user -r requirements.txt

mkdir -p data models logs

if [ ! -f config.yaml ]; then
  echo "config.yaml 已存在，跳过"
fi

# 加载 DeepSeek Key（若已装 Hermes）
if [ -f "$HOME/.hermes/.env" ]; then
  set -a
  # shellcheck disable=SC1091
  source "$HOME/.hermes/.env" 2>/dev/null || true
  set +a
  echo "已加载 ~/.hermes/.env"
fi

echo ""
echo "安装完成。启动方式:"
echo "  cd $ROOT"
echo "  python3 main.py train"
echo "  python3 main.py serve"
echo ""
echo "浏览器打开: http://localhost:8765"
echo "同花顺桥接 (Windows): 见 scripts/install-windows.ps1"
