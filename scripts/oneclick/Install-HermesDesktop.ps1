# =============================================================================
# Hermes Agent + DeepSeek 一键安装（Windows 本机 + 桌面快捷方式）
# 用法:
#   右键「使用 PowerShell 运行」或:
#   powershell -NoProfile -ExecutionPolicy Bypass -File Install-HermesDesktop.ps1
# 远程一行:
#   irm https://raw.githubusercontent.com/AFJY/-/cursor/hermes-desktop-deploy-a460/scripts/oneclick/Install-HermesDesktop.ps1 | iex
# =============================================================================

$ErrorActionPreference = "Stop"

$RepoUrl = if ($env:HERMES_DEPLOY_REPO) { $env:HERMES_DEPLOY_REPO } else { "https://github.com/AFJY/-.git" }
$RepoBranch = if ($env:HERMES_DEPLOY_BRANCH) { $env:HERMES_DEPLOY_BRANCH } else { "cursor/hermes-desktop-deploy-a460" }
$InstallDirName = "hermes-deploy"

function Write-Banner {
    Write-Host ""
    Write-Host "╔══════════════════════════════════════════════════════════╗" -ForegroundColor Cyan
    Write-Host "║   Hermes Agent + DeepSeek  一键安装 (Windows + 桌面)    ║" -ForegroundColor Cyan
    Write-Host "╚══════════════════════════════════════════════════════════╝" -ForegroundColor Cyan
    Write-Host ""
}

function Ensure-Wsl {
    if (-not (Get-Command wsl.exe -ErrorAction SilentlyContinue)) {
        Write-Host "未检测到 WSL2。" -ForegroundColor Yellow
        Write-Host "请以管理员打开 PowerShell，执行:  wsl --install" -ForegroundColor Yellow
        Write-Host "重启电脑后，再次运行本安装包。" -ForegroundColor Yellow
        Read-Host "按 Enter 退出"
        exit 1
    }
    $null = wsl -e true 2>$null
    if ($LASTEXITCODE -ne 0) {
        Write-Host "WSL 未就绪。请先打开 Ubuntu 完成首次初始化。" -ForegroundColor Yellow
        Read-Host "按 Enter 退出"
        exit 1
    }
}

function Get-DeepSeekKey {
    $k = $env:DEEPSEEK_API_KEY
    if (-not $k) {
        $k = Read-Host "请输入 DeepSeek API Key (sk-...)"
    }
    if (-not $k) { throw "需要 DEEPSEEK_API_KEY" }
    return $k.Trim()
}

function Escape-BashSingleQuoted([string]$s) {
    return $s.Replace("'", "'\''")
}

Write-Banner
Ensure-Wsl

$key = Get-DeepSeekKey
$escapedKey = Escape-BashSingleQuoted $key

Write-Host "==> 在 WSL 内安装 Hermes（首次约 5-15 分钟）..." -ForegroundColor Green

$bashScript = @"
set -euo pipefail
export DEEPSEEK_API_KEY='$escapedKey'
export HERMES_DEPLOY_REPO='$RepoUrl'
export HERMES_DEPLOY_BRANCH='$RepoBranch'
export HERMES_DEPLOY_DIR="\$HOME/$InstallDirName"
INSTALL_SH="\$HOME/$InstallDirName/scripts/oneclick/install-hermes-desktop.sh"
if [ -f "\$INSTALL_SH" ]; then
  bash "\$INSTALL_SH"
else
  curl -fsSL "https://raw.githubusercontent.com/AFJY/-/$RepoBranch/scripts/oneclick/install-hermes-desktop.sh" | bash
fi
"@

$bashScript | wsl -e bash -s
if ($LASTEXITCODE -ne 0) {
    Write-Host "WSL 安装失败，退出码: $LASTEXITCODE" -ForegroundColor Red
    Read-Host "按 Enter 退出"
    exit $LASTEXITCODE
}

$shortcutScript = Join-Path $env:TEMP "Create-HermesShortcuts.ps1"
$raw = "https://raw.githubusercontent.com/AFJY/-/$RepoBranch/scripts/windows/Create-HermesShortcuts.ps1"
if ($PSScriptRoot) {
    $localShortcut = Join-Path $PSScriptRoot "..\windows\Create-HermesShortcuts.ps1"
    if (Test-Path $localShortcut) { $shortcutScript = $localShortcut }
}
if (-not (Test-Path $shortcutScript)) {
    try {
        Invoke-WebRequest -Uri $raw -OutFile $shortcutScript -UseBasicParsing
    } catch {
        $shortcutScript = $null
    }
}

if ($shortcutScript -and (Test-Path $shortcutScript)) {
    Write-Host ""
    Write-Host "==> 创建 Windows 桌面快捷方式 ..." -ForegroundColor Green
    & $shortcutScript
}

Write-Host ""
Write-Host "════════════════════════════════════════" -ForegroundColor Green
Write-Host " 安装完成" -ForegroundColor Green
Write-Host "════════════════════════════════════════" -ForegroundColor Green
Write-Host " Windows 桌面: Hermes Agent (DeepSeek) / Hermes 控制台"
Write-Host " WSL 终端:     wsl  →  hermes"
Write-Host " 诊断:         wsl -e bash -lc 'hermes doctor'"
Write-Host ""
Read-Host "按 Enter 关闭"
