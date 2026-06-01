# Hermes + DeepSeek Windows 本机一键安装（避免 irm | iex 引号/管道问题）
# 用法: 右键 -> 使用 PowerShell 运行

$ErrorActionPreference = "Stop"
$Branch = "cursor/hermes-desktop-deploy-a460"

if (-not $env:DEEPSEEK_API_KEY) {
    $env:DEEPSEEK_API_KEY = Read-Host "请输入 DeepSeek API Key (sk-...)"
}
if (-not $env:DEEPSEEK_API_KEY) {
    Write-Host "错误: 需要 DEEPSEEK_API_KEY" -ForegroundColor Red
    Read-Host "按 Enter 退出"
    exit 1
}

$Url = "https://raw.githubusercontent.com/AFJY/-/${Branch}/scripts/windows/Install-HermesWindowsNative.ps1"
$Temp = Join-Path $env:TEMP "Install-HermesWindowsNative.ps1"

Write-Host "下载安装脚本..."
Invoke-WebRequest -Uri $Url -OutFile $Temp -UseBasicParsing
Write-Host "开始安装（首次约 5-15 分钟）..."
& $Temp
