# 同花顺 → Stock AI 云端桥接（无需 Git）
# 右键 → 使用 PowerShell 运行，或在 PowerShell 里：
#   Set-ExecutionPolicy -Scope CurrentUser RemoteSigned
#   cd 桌面\bridge文件夹
#   .\安装并连接.ps1

$ErrorActionPreference = "Stop"
$Server = "wss://rare-cats-bake.loca.lt/ws/ths"

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "  同花顺 连接 Stock AI 云端" -ForegroundColor Cyan
Write-Host "  请先打开同花顺远航版" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# 找 Python
$Py = $null
foreach ($cmd in @("py", "python", "python3")) {
    if (Get-Command $cmd -ErrorAction SilentlyContinue) {
        $ver = & $cmd --version 2>&1
        if ($LASTEXITCODE -eq 0) {
            $Py = $cmd
            Write-Host "找到 Python: $cmd ($ver)" -ForegroundColor Green
            break
        }
    }
}
if (-not $Py) {
    Write-Host "未安装 Python！" -ForegroundColor Red
    Write-Host "请打开: https://www.python.org/downloads/" -ForegroundColor Yellow
    Write-Host "安装时务必勾选 [Add python.exe to PATH]" -ForegroundColor Yellow
    Write-Host "或微软商店搜索 Python 3.12 安装" -ForegroundColor Yellow
    Read-Host "按回车退出"
    exit 1
}

$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location $ScriptDir

Write-Host "安装依赖 websockets akshare ..."
& $Py -m pip install --user websockets akshare

Write-Host ""
Write-Host "读取同花顺自选股..."
& $Py ths_watchlist.py --ui 2>$null

Write-Host ""
Write-Host "连接云端: $Server" -ForegroundColor Green
Write-Host "看到 Connected 即成功，请勿关闭本窗口" -ForegroundColor Yellow
Write-Host ""

& $Py ths_agent.py --server $Server --sync-watchlist --ui

Read-Host "按回车退出"
