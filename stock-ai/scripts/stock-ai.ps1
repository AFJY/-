# Stock AI 一键脚本 (Windows)
# 用法:
#   .\scripts\stock-ai.ps1 start
#   .\scripts\stock-ai.ps1 status
#   .\scripts\stock-ai.ps1 stop
#   .\scripts\stock-ai.ps1 bridge   # 启动同花顺桥接

param(
    [Parameter(Position = 0)]
    [ValidateSet("start", "stop", "status", "morning", "bridge")]
    [string]$Action = "start"
)

$Root = Split-Path -Parent (Split-Path -Parent $MyInvocation.MyCommand.Path)
Set-Location $Root
$Port = if ($env:STOCK_AI_PORT) { $env:STOCK_AI_PORT } else { 8765 }
$HostAddr = if ($env:STOCK_AI_HOST) { $env:STOCK_AI_HOST } else { "127.0.0.1" }
$Log = Join-Path $Root "logs\overnight.log"

New-Item -ItemType Directory -Force -Path (Join-Path $Root "data"), (Join-Path $Root "logs") | Out-Null

function Test-Running {
    try {
        $r = Invoke-RestMethod -Uri "http://${HostAddr}:${Port}/api/health" -TimeoutSec 3
        return $r.ok -eq $true
    } catch { return $false }
}

function Start-StockAI {
    Write-Host "==> Stock AI 启动" -ForegroundColor Cyan

    python -m pip install -q -r requirements.txt 2>$null

    if (-not (Test-Path (Join-Path $Root "models\SPY.joblib")) -and
        -not (Test-Path (Join-Path $Root "models\000001_SS.joblib"))) {
        Write-Host "首次运行，训练模型..."
        python main.py train
    }

    if (Test-Running) {
        Write-Host "服务已在运行: http://${HostAddr}:${Port}" -ForegroundColor Green
    } else {
        Write-Host "启动 serve..."
        Start-Process python -ArgumentList "main.py serve" -WindowStyle Hidden -WorkingDirectory $Root
        Start-Sleep -Seconds 5
        if (Test-Running) {
            Write-Host "OK  http://${HostAddr}:${Port}" -ForegroundColor Green
        } else {
            Write-Host "启动失败，请手动运行: python main.py serve" -ForegroundColor Red
        }
    }

    Write-Host ""
    Write-Host "同花顺桥接:" -ForegroundColor Yellow
    Write-Host "  .\scripts\stock-ai.ps1 bridge"
    Write-Host ""
    Show-Status
}

function Stop-StockAI {
    Write-Host "==> 停止 Stock AI"
    Get-Process python -ErrorAction SilentlyContinue | Where-Object {
        $_.CommandLine -like "*main.py serve*"
    } | Stop-Process -Force -ErrorAction SilentlyContinue
    Write-Host "已停止"
}

function Show-Status {
    Write-Host "==> Stock AI 状态  $(Get-Date)" -ForegroundColor Cyan
    if (Test-Running) {
        try {
            $d = Invoke-RestMethod -Uri "http://${HostAddr}:${Port}/api/status" -TimeoutSec 10
            $m = $d.monthly
            Write-Host "  服务:     运行中  http://${HostAddr}:${Port}"
            Write-Host ("  总权益:   {0:N2}" -f $d.equity)
            Write-Host ("  本月收益: {0:+0.00;-0.00}%  (目标 $($m.target_return_pct)%)" -f $m.return_pct)
            Write-Host ("  同花顺:   $(if ($d.ths_connected) { '已连接' } else { '未连接' })")
            Write-Host "  行情数:   $($d.quotes.Count)"
        } catch {
            Write-Host "  状态获取失败: $_"
        }
    } else {
        Write-Host "  服务: 未运行"
        Write-Host "  启动: .\scripts\stock-ai.ps1 start"
    }
}

function Show-Morning {
    Show-Status
    Write-Host ""
    Write-Host "==> 最近日志"
    if (Test-Path $Log) { Get-Content $Log -Tail 20 } else { Write-Host "  (暂无)" }
}

function Start-Bridge {
    Write-Host "==> 启动同花顺桥接" -ForegroundColor Cyan
    Set-Location (Join-Path $Root "bridge")
    python ths_agent.py --server "ws://${HostAddr}:${Port}/ws/ths" --sync-watchlist --ui
}

switch ($Action) {
    "start"   { Start-StockAI }
    "stop"    { Stop-StockAI }
    "status"  { Show-Status }
    "morning" { Show-Morning }
    "bridge"  { Start-Bridge }
}
