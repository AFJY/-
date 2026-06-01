# =============================================================================
# Hermes Agent + DeepSeek — Windows 本机原生安装（无需 WSL）
# 用法:
#   $env:DEEPSEEK_API_KEY = "sk-..."
#   irm "https://raw.githubusercontent.com/AFJY/-/cursor/hermes-desktop-deploy-a460/scripts/windows/Install-HermesWindowsNative.ps1" | iex
# =============================================================================

$ErrorActionPreference = "Stop"

function Write-Banner {
    Write-Host ""
    Write-Host "╔══════════════════════════════════════════════════════════╗" -ForegroundColor Cyan
    Write-Host "║  Hermes Agent + DeepSeek  Windows 本机安装（原生）        ║" -ForegroundColor Cyan
    Write-Host "╚══════════════════════════════════════════════════════════╝" -ForegroundColor Cyan
    Write-Host ""
}

function Get-DeepSeekKey {
    $k = $env:DEEPSEEK_API_KEY
    if (-not $k) { $k = Read-Host "请输入 DeepSeek API Key (sk-...)" }
    if (-not $k) { throw "需要 DEEPSEEK_API_KEY" }
    return $k.Trim()
}

function Set-DeepSeekConfig {
    param([string]$Key)
    $hermesHome = Join-Path $env:USERPROFILE ".hermes"
    if (-not (Test-Path $hermesHome)) {
        New-Item -ItemType Directory -Force -Path $hermesHome | Out-Null
    }
    $envFile = Join-Path $hermesHome ".env"
    $line = "DEEPSEEK_API_KEY=$Key"
    if (-not (Test-Path $envFile)) {
        Set-Content -Path $envFile -Value $line -Encoding UTF8
        return
    }
    $content = Get-Content $envFile -Raw -ErrorAction SilentlyContinue
    if ($content -match '(?m)^DEEPSEEK_API_KEY=') {
        $content = $content -replace '(?m)^DEEPSEEK_API_KEY=.*', $line
        Set-Content -Path $envFile -Value $content.TrimEnd() -Encoding UTF8 -NoNewline
    } else {
        Add-Content -Path $envFile -Value $line -Encoding UTF8
    }
}

function Find-HermesExe {
    $candidates = @(
        "$env:LOCALAPPDATA\hermes\hermes-agent\apps\desktop\release\win-unpacked\Hermes.exe",
        "$env:LOCALAPPDATA\hermes\bin\hermes.cmd",
        "$env:LOCALAPPDATA\hermes\bin\hermes.exe"
    )
    foreach ($p in $candidates) {
        if (Test-Path $p) { return $p }
    }
    return $null
}

function New-DesktopShortcut {
    param(
        [string]$Name,
        [string]$Target,
        [string]$Arguments = "",
        [string]$Comment = ""
    )
    $desktop = [Environment]::GetFolderPath("Desktop")
    $lnk = Join-Path $desktop "$Name.lnk"
    $shell = New-Object -ComObject WScript.Shell
    $sc = $shell.CreateShortcut($lnk)
    $sc.TargetPath = $Target
    $sc.Arguments = $Arguments
    $sc.Description = $Comment
    $sc.WorkingDirectory = $env:USERPROFILE
    $sc.Save()
    Write-Host "已创建桌面快捷方式: $lnk" -ForegroundColor Green
}

Write-Banner

$key = Get-DeepSeekKey
Set-DeepSeekConfig -Key $key

Write-Host "==> [1/3] 安装 Hermes Agent（官方 Windows 安装器）..." -ForegroundColor Green
Write-Host "    首次约 5–15 分钟，请保持网络畅通。" -ForegroundColor DarkGray

$installUrl = "https://raw.githubusercontent.com/NousResearch/hermes-agent/main/scripts/install.ps1"
$installScript = Join-Path $env:TEMP "hermes-official-install.ps1"
$ProgressPreference = "SilentlyContinue"
Invoke-WebRequest -Uri $installUrl -OutFile $installScript -UseBasicParsing
& $installScript -SkipSetup -NonInteractive -IncludeDesktop

# 刷新 PATH（当前会话）
$env:Path = [Environment]::GetEnvironmentVariable("Path", "User") + ";" +
            [Environment]::GetEnvironmentVariable("Path", "Machine")

Write-Host ""
Write-Host "==> [2/3] 配置 DeepSeek ..." -ForegroundColor Green

$hermesCmd = Get-Command hermes -ErrorAction SilentlyContinue
if ($hermesCmd) {
    hermes config set model.provider deepseek 2>$null
    hermes config set model.default deepseek-v4-pro 2>$null
    hermes config set model.base_url "https://api.deepseek.com/v1" 2>$null
    hermes config set DEEPSEEK_API_KEY $key 2>$null
    hermes config set web.search_backend ddgs 2>$null
    Write-Host "DeepSeek 已写入配置" -ForegroundColor Green
} else {
    Write-Host "WARN: 当前窗口找不到 hermes 命令。请关闭并重新打开 PowerShell 后运行:" -ForegroundColor Yellow
    Write-Host "  hermes config set DEEPSEEK_API_KEY `"$key`"" -ForegroundColor Yellow
}

Write-Host ""
Write-Host "==> [3/3] 创建 Windows 桌面快捷方式 ..." -ForegroundColor Green

$hermesExe = Find-HermesExe
if ($hermesExe -and $hermesExe -like "*.exe" -and (Split-Path $hermesExe -Leaf) -eq "Hermes.exe") {
    New-DesktopShortcut "Hermes Agent (DeepSeek)" $hermesExe "" "Hermes 原生桌面 (DeepSeek)"
} elseif ($hermesCmd) {
    $hermesPath = $hermesCmd.Source
    New-DesktopShortcut "Hermes Agent (DeepSeek)" "powershell.exe" "-NoExit -Command `"hermes desktop`"" "Hermes 桌面 GUI (DeepSeek)"
    New-DesktopShortcut "Hermes 终端" $hermesPath "" "Hermes 终端对话 (DeepSeek)"
} else {
    Write-Host "WARN: 未能自动创建快捷方式。安装完成后请新开 PowerShell 运行:" -ForegroundColor Yellow
    Write-Host "  irm .../scripts/windows/Create-HermesShortcuts.ps1 | iex" -ForegroundColor Yellow
}

# Web 控制台快捷方式
if ($hermesCmd) {
    $dashArgs = '-NoExit -Command "hermes dashboard --port 9119"'
    New-DesktopShortcut "Hermes 控制台" "powershell.exe" $dashArgs "Hermes Web 管理面板"
}

Write-Host ""
Write-Host "════════════════════════════════════════" -ForegroundColor Green
Write-Host " 安装完成" -ForegroundColor Green
Write-Host "════════════════════════════════════════" -ForegroundColor Green
Write-Host ""
Write-Host " 安装位置:" -ForegroundColor Cyan
Write-Host "   程序: %LOCALAPPDATA%\hermes\hermes-agent"
Write-Host "   配置: %USERPROFILE%\.hermes\"
Write-Host ""
Write-Host " 使用方式（请先关闭并重新打开 PowerShell）:" -ForegroundColor Cyan
Write-Host "   桌面双击: Hermes Agent (DeepSeek)"
Write-Host "   终端:     hermes"
Write-Host "   桌面 GUI: hermes desktop"
Write-Host "   诊断:     hermes doctor"
Write-Host ""
Read-Host "按 Enter 关闭"
