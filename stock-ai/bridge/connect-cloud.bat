@echo off
cd /d "%~dp0"
title Stock AI THS Bridge

set SERVER=wss://rare-cats-bake.loca.lt/ws/ths
if not "%~1"=="" set SERVER=%~1

echo ==========================================
echo   Stock AI - Tonghuashun Cloud Bridge
echo   Open THS Yuanhang BEFORE running
echo ==========================================
echo.
echo Server: %SERVER%
echo.

where py >nul 2>&1 && set PY=py
if not defined PY where python >nul 2>&1 && set PY=python
if not defined PY (
  echo ERROR: Python not found. Install Python 3 and add to PATH.
  pause
  exit /b 1
)

echo Installing websockets akshare...
%PY% -m pip install --user websockets akshare

echo.
echo Connecting... Keep this window OPEN.
echo Success = line with Connected
echo.
%PY% ths_agent.py --server %SERVER% --sync-watchlist --ui

echo.
echo Disconnected. Press any key to exit.
pause
