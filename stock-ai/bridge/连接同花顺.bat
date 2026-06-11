@echo off
chcp 65001 >nul
title Stock AI - 同花顺桥接
cd /d "%~dp0"

echo ========================================
echo   Stock AI 同花顺桥接
echo   请保持同花顺远航版已打开
echo ========================================
echo.

set SERVER=ws://127.0.0.1:8765/ws/ths
if not "%~1"=="" set SERVER=%~1

echo 连接地址: %SERVER%
echo.

python ths_watchlist.py --ui 2>nul
echo.
echo 正在推送行情（Ctrl+C 停止）...
python ths_agent.py --server %SERVER% --sync-watchlist --ui
pause
