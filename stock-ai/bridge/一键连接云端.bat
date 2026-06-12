@echo off
chcp 65001 >nul
title 同花顺 → Stock AI 云端桥接
cd /d "%~dp0"

echo ==========================================
echo   同花顺 连接 Stock AI 云端
echo   请先打开：同花顺远航版
echo ==========================================
echo.

:: 默认云端隧道地址（若失效，问 Agent 要新地址）
set SERVER=wss://rare-cats-bake.loca.lt/ws/ths
if not "%~1"=="" set SERVER=%~1

echo WebSocket: %SERVER%
echo.

where python >nul 2>&1 || (
  echo 未找到 Python，请先安装 Python 3 并勾选 Add to PATH
  pause & exit /b 1
)

echo 安装依赖...
python -m pip install -q websockets akshare 2>nul

echo.
echo 读取自选股...
python ths_watchlist.py --ui 2>nul
echo.

echo 正在连接云端并推送行情...
echo 看到 Connected 即成功；保持本窗口不要关
echo.
python ths_agent.py --server %SERVER% --sync-watchlist --ui

echo.
echo 连接断开。若 503 错误，向 Agent 索取新的隧道地址后：
echo   一键连接云端.bat wss://新地址.loca.lt/ws/ths
pause
