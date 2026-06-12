#!/usr/bin/env bash
# 保持公网隧道存活，挂了自动换 URL
LOG="/tmp/stock-ai-tunnel.log"
URL_FILE="/tmp/stock-ai-tunnel.url"

while true; do
  if [ -f "$URL_FILE" ]; then
    URL=$(cat "$URL_FILE")
    if curl -sf --max-time 8 -H "Bypass-Tunnel-Reminder: true" "$URL/api/health" >/dev/null 2>&1; then
      sleep 30
      continue
    fi
  fi

  pkill -f "localtunnel --port 8765" 2>/dev/null || true
  sleep 2
  rm -f "$LOG"
  npx -y localtunnel --port 8765 >"$LOG" 2>&1 &
  sleep 8
  URL=$(grep -o 'https://[^ ]*loca\.lt' "$LOG" | head -1)
  if [ -n "$URL" ]; then
    echo "$URL" >"$URL_FILE"
    echo "[$(date -Iseconds)] tunnel: $URL" >> /workspace/stock-ai/logs/overnight.log
  fi
  sleep 30
done
