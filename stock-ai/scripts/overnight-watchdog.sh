#!/usr/bin/env bash
# 夜间守护：Stock AI 服务挂了自动重启，写日志
set -uo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"
LOG="$ROOT/logs/overnight.log"
mkdir -p "$ROOT/logs" "$ROOT/data"

if [ -f "$HOME/.hermes/.env" ]; then
  set -a
  # shellcheck disable=SC1091
  source "$HOME/.hermes/.env" 2>/dev/null || true
  set +a
fi

log() { echo "[$(date -Iseconds)] $*" | tee -a "$LOG"; }

log "Overnight watchdog started (pid $$)"

while true; do
  if curl -sf --max-time 5 http://127.0.0.1:8765/api/health >/dev/null 2>&1; then
    sleep 60
    continue
  fi

  log "Service down — restarting serve"
  pkill -f "python3 main.py serve" 2>/dev/null || true
  sleep 2
  nohup python3 main.py serve >>"$LOG" 2>&1 &
  sleep 8

  if curl -sf --max-time 10 http://127.0.0.1:8765/api/health >/dev/null; then
    log "Restart OK"
  else
    log "Restart FAILED — will retry in 30s"
    sleep 30
  fi
done
