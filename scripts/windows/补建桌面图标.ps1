# 补建 Windows 桌面 Hermes 快捷方式（避免 irm | iex 引号问题）
# 用法: 右键 -> 使用 PowerShell 运行
# 或在 PowerShell 中: powershell -ExecutionPolicy Bypass -File "本文件路径"

$ErrorActionPreference = "Stop"
$Branch = "cursor/hermes-desktop-deploy-a460"
$Url = "https://raw.githubusercontent.com/AFJY/-/${Branch}/scripts/windows/Create-HermesShortcuts-Native.ps1"
$Temp = Join-Path $env:TEMP "Create-HermesShortcuts-Native.ps1"

Write-Host "下载脚本..."
Invoke-WebRequest -Uri $Url -OutFile $Temp -UseBasicParsing
Write-Host "运行..."
& $Temp
Read-Host "按 Enter 关闭"
