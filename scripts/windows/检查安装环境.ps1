# 检查 Windows 能否安装 Hermes（30 秒内应有输出）
Write-Host ""
Write-Host "=== Hermes 安装环境检查 ===" -ForegroundColor Cyan
Write-Host "时间: $(Get-Date)"
Write-Host ""

Write-Host "[1] PowerShell 版本: $($PSVersionTable.PSVersion)" -ForegroundColor Green

Write-Host "[2] 测试访问 GitHub ..."
try {
    $r = Invoke-WebRequest -Uri "https://raw.githubusercontent.com" -Method Head -TimeoutSec 15 -UseBasicParsing
    Write-Host "    OK ($($r.StatusCode))" -ForegroundColor Green
} catch {
    Write-Host "    失败: $($_.Exception.Message)" -ForegroundColor Red
    Write-Host "    提示: 可能需要代理/VPN，或改用手机热点" -ForegroundColor Yellow
}

Write-Host "[3] 测试下载 Hermes 安装脚本 ..."
$test = "$env:TEMP\hermes-download-test.ps1"
try {
    Invoke-WebRequest -Uri "https://raw.githubusercontent.com/NousResearch/hermes-agent/main/scripts/install.ps1" `
        -OutFile $test -TimeoutSec 60 -UseBasicParsing
    $kb = [math]::Round((Get-Item $test).Length / 1KB, 1)
    Write-Host "    OK (${kb} KB) -> $test" -ForegroundColor Green
} catch {
    Write-Host "    失败: $($_.Exception.Message)" -ForegroundColor Red
}

Write-Host "[4] 是否已安装 Hermes ..."
$paths = @(
    "$env:LOCALAPPDATA\hermes\bin\hermes.cmd",
    "$env:USERPROFILE\.hermes\config.yaml"
)
foreach ($p in $paths) {
    if (Test-Path $p) { Write-Host "    已存在: $p" -ForegroundColor Green }
    else { Write-Host "    未找到: $p" -ForegroundColor DarkGray }
}

$hermes = Get-Command hermes -ErrorAction SilentlyContinue
if ($hermes) { Write-Host "    hermes 命令: $($hermes.Source)" -ForegroundColor Green }

Write-Host ""
Write-Host "若 [2][3] 为 OK，可运行完整安装脚本。" -ForegroundColor Cyan
Read-Host "按 Enter 关闭"
