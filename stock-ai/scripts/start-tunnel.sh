#!/usr/bin/env bash
# 生成公网访问链接（浏览器可直接打开，无需 Cursor 端口转发）
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
LOG="/tmp/stock-ai-tunnel.log"

# 确保服务在跑
if ! curl -sf --max-time 3 http://127.0.0.1:8765/api/health >/dev/null 2>&1; then
  echo "先启动服务: bash scripts/stock-ai.sh start"
  exit 1
fi

pkill -f "localtunnel --port 8765" 2>/dev/null || true
pkill -f "tunnel-watchdog.sh" 2>/dev/null || true
sleep 1
nohup bash "$(dirname "$0")/tunnel-watchdog.sh" >>/workspace/stock-ai/logs/overnight.log 2>&1 &
sleep 10
URL=$(cat /tmp/stock-ai-tunnel.url 2>/dev/null || grep -o 'https://[^ ]*loca\.lt' "$LOG" | head -1)
if [ -z "$URL" ]; then
  echo "隧道启动失败，查看 $LOG"
  exit 1
fi
echo ""
echo "=========================================="
echo "  在浏览器地址栏打开（不是搜索框）:"
echo "  $URL"
echo "=========================================="
echo ""
echo "同花顺桥接 WebSocket:"
echo "  ws://${URL#https://}/ws/ths"
echo "  (或 wss://${URL#https://}/ws/ths)"
echo ""
echo "首次打开可能要点 Continue 跳过 localtunnel 提示页"
