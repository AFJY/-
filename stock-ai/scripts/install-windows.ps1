# Stock AI 本机部署 (Windows) — 服务端 + 同花顺桥接
# 以管理员身份运行 PowerShell:
#   Set-ExecutionPolicy -Scope CurrentUser RemoteSigned
#   .\scripts\install-windows.ps1

$Root = Split-Path -Parent (Split-Path -Parent $MyInvocation.MyCommand.Path)
Set-Location $Root

Write-Host "==> Stock AI Windows 安装" -ForegroundColor Cyan

python -m pip install --upgrade pip
python -m pip install -r requirements.txt

New-Item -ItemType Directory -Force -Path data, models, logs | Out-Null

# 自选股示例
$wlExample = Join-Path $Root "bridge\watchlist.json.example"
$wl = Join-Path $Root "bridge\watchlist.json"
if (-not (Test-Path $wl)) {
    Copy-Item $wlExample $wl
    Write-Host "已创建 bridge\watchlist.json — 请替换为你的自选股" -ForegroundColor Yellow
}

Write-Host ""
Write-Host "1) 启动 Stock AI 服务:" -ForegroundColor Green
Write-Host "   python main.py train"
Write-Host "   python main.py serve"
Write-Host ""
Write-Host "2) 启动同花顺桥接 (另开终端, 保持同花顺远航版打开):" -ForegroundColor Green
Write-Host "   cd bridge"
Write-Host "   python ths_agent.py --server ws://127.0.0.1:8765/ws/ths --sync-watchlist --ui"
Write-Host ""
Write-Host "3) 浏览器: http://localhost:8765" -ForegroundColor Green
