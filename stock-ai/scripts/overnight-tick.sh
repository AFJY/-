#!/usr/bin/env bash
# 定期打快照到日志（供早上查看）
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
LOG="$ROOT/logs/overnight.log"
mkdir -p "$ROOT/logs"

while true; do
  if curl -sf --max-time 15 http://127.0.0.1:8765/api/status -o /tmp/stock_ai_snap.json 2>/dev/null; then
    eq=$(python3 -c "import json; d=json.load(open('/tmp/stock_ai_snap.json')); print(f\"{d['equity']:.2f}\")" 2>/dev/null || echo "?")
    ret=$(python3 -c "import json; d=json.load(open('/tmp/stock_ai_snap.json')); print(f\"{d['monthly']['return_pct']:.2f}\")" 2>/dev/null || echo "?")
    echo "[$(date -Iseconds)] equity=$eq monthly=${ret}%" >>"$LOG"
  else
    echo "[$(date -Iseconds)] status fetch failed" >>"$LOG"
  fi
  sleep 300
done
