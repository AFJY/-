@echo off
chcp 65001 >nul
title Stock AI - 同花顺桥接(云端)
cd /d "%~dp0"

echo 用法: 把下面的地址改成 Cursor Ports 里 8765 对应的地址
echo 例如 ws://localhost:8765/ws/ths  (端口已转发时)
echo.
set /p SERVER="请输入 WebSocket 地址 [ws://127.0.0.1:8765/ws/ths]: "
if "%SERVER%"=="" set SERVER=ws://127.0.0.1:8765/ws/ths

python ths_agent.py --server %SERVER% --sync-watchlist --ui
pause
