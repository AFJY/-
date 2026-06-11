#!/usr/bin/env bash
# Stock AI 一键脚本 — 启动 / 停止 / 查看状态
# 用法:
#   bash scripts/stock-ai.sh start    # 启动服务 + 夜间守护
#   bash scripts/stock-ai.sh status   # 查看当前状态（早上看这个）
#   bash scripts/stock-ai.sh stop     # 停止全部
#   bash scripts/stock-ai.sh morning  # 状态 + 最近日志

set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"
PORT="${STOCK_AI_PORT:-8765}"
HOST="${STOCK_AI_HOST:-127.0.0.1}"
LOG="$ROOT/logs/overnight.log"
PID_FILE="$ROOT/data/stock-ai-serve.pid"

mkdir -p "$ROOT/data" "$ROOT/logs" "$ROOT/models"

load_env() {
  if [ -f "$HOME/.hermes/.env" ]; then
    set -a
    # shellcheck disable=SC1091
    source "$HOME/.hermes/.env" 2>/dev/null || true
    set +a
  fi
  export PATH="$HOME/.local/bin:$PATH"
}

is_running() {
  curl -sf --max-time 3 "http://${HOST}:${PORT}/api/health" >/dev/null 2>&1
}

cmd_start() {
  load_env
  echo "==> Stock AI 启动"

  if ! python3 -c "import fastapi, yfinance" 2>/dev/null; then
    echo "安装依赖..."
    python3 -m pip install --user -q -r requirements.txt
  fi

  if [ ! -f "$ROOT/models/SPY.joblib" ] && [ ! -f "$ROOT/models/000001_SS.joblib" ]; then
    echo "首次运行，训练模型..."
    python3 main.py train
  fi

  if is_running; then
    echo "服务已在运行: http://${HOST}:${PORT}"
  else
    echo "启动 serve (端口 ${PORT})..."
    nohup python3 main.py serve >>"$LOG" 2>&1 &
    echo $! >"$PID_FILE"
    sleep 5
    if is_running; then
      echo "OK  http://${HOST}:${PORT}"
    else
      echo "启动失败，查看日志: tail -30 $LOG"
      exit 1
    fi
  fi

  # 守护与快照（若未在跑）
  if ! pgrep -f "overnight-watchdog.sh" >/dev/null 2>&1; then
    nohup bash "$ROOT/scripts/overnight-watchdog.sh" >>"$LOG" 2>&1 &
    echo "已启动夜间守护"
  fi
  if ! pgrep -f "overnight-tick.sh" >/dev/null 2>&1; then
    nohup bash "$ROOT/scripts/overnight-tick.sh" >>"$LOG" 2>&1 &
    echo "已启动权益快照 (每5分钟)"
  fi

  echo ""
  echo "同花顺桥接 (Windows 另开终端):"
  echo "  cd bridge && python ths_agent.py --server ws://${HOST}:${PORT}/ws/ths --sync-watchlist --ui"
  echo ""
  cmd_status
}

cmd_stop() {
  echo "==> 停止 Stock AI"
  pkill -f "python3 main.py serve" 2>/dev/null || true
  pkill -f "overnight-watchdog.sh" 2>/dev/null || true
  pkill -f "overnight-tick.sh" 2>/dev/null || true
  rm -f "$PID_FILE"
  echo "已停止"
}

cmd_status() {
  load_env
  echo "==> Stock AI 状态  $(date)"
  if is_running; then
  python3 - <<PY
import json, urllib.request
try:
    with urllib.request.urlopen("http://${HOST}:${PORT}/api/status", timeout=10) as r:
        d = json.load(r)
    m = d.get("monthly", {})
    print(f"  服务:     运行中  http://${HOST}:${PORT}")
    print(f"  总权益:   {d.get('equity', 0):,.2f}")
    print(f"  本月收益: {m.get('return_pct', 0):+.2f}%  (目标 {m.get('target_return_pct', '?')}%)")
    print(f"  同花顺:   {'已连接' if d.get('ths_connected') else '未连接'}")
    print(f"  行情数:   {len(d.get('quotes', []))}")
    print(f"  暂停:     {d.get('paused', False)}")
except Exception as e:
    print(f"  状态获取失败: {e}")
PY
  else
    echo "  服务: 未运行"
    echo "  启动: bash scripts/stock-ai.sh start"
  fi
}

cmd_morning() {
  cmd_status
  echo ""
  echo "==> 最近日志 (overnight.log)"
  if [ -f "$LOG" ]; then
    tail -20 "$LOG"
  else
    echo "  (暂无日志)"
  fi
  echo ""
  if [ -f "$ROOT/OVERNIGHT_STATUS.md" ]; then
    echo "详细说明: $ROOT/OVERNIGHT_STATUS.md"
  fi
}

case "${1:-start}" in
  start)   cmd_start ;;
  stop)    cmd_stop ;;
  status)  cmd_status ;;
  morning) cmd_morning ;;
  *)
    echo "用法: $0 {start|stop|status|morning}"
    exit 1
    ;;
esac
