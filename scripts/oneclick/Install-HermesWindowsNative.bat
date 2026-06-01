@echo off
chcp 65001 >nul
title Hermes Agent + DeepSeek (Windows 本机)
cd /d "%~dp0"
echo.
echo  Hermes Agent + DeepSeek — Windows 本机安装（无需 WSL）
echo  ======================================================
echo.
powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0..\windows\Install-HermesWindowsNative.ps1"
exit /b %ERRORLEVEL%
