@echo off
chcp 65001 >nul
title Hermes Agent + DeepSeek 一键安装
cd /d "%~dp0"

echo.
echo  Hermes Agent + DeepSeek 一键安装 (Windows)
echo  ==========================================
echo.

where powershell >nul 2>&1
if errorlevel 1 (
    echo 错误: 未找到 PowerShell
    pause
    exit /b 1
)

powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0Install-HermesDesktop.ps1"
exit /b %ERRORLEVEL%
