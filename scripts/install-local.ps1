# Hermes Agent local deploy on Windows (via WSL2).
# Run in PowerShell: irm ... | iex   OR   .\scripts\install-local.ps1

$ErrorActionPreference = "Stop"

Write-Host "=============================================="
Write-Host " Hermes Agent 本机部署 (DeepSeek) - Windows"
Write-Host "=============================================="

if (-not (Get-Command wsl -ErrorAction SilentlyContinue)) {
    Write-Host "未检测到 WSL。请先安装:"
    Write-Host "  wsl --install"
    Write-Host "重启后，在 Ubuntu (WSL) 终端中运行 Linux 安装脚本。"
    exit 1
}

$key = $env:DEEPSEEK_API_KEY
if (-not $key) {
    $key = Read-Host "请输入 DEEPSEEK_API_KEY (sk-...)"
}
if (-not $key) {
    Write-Host "错误: 需要 DEEPSEEK_API_KEY"
    exit 1
}

$repoBranch = "cursor/hermes-desktop-deploy-a460"
$installCmd = @"
set -e
export DEEPSEEK_API_KEY='$($key.Replace("'", "'\''"))'
cd ~
if [ ! -d hermes-deploy ]; then
  git clone https://github.com/AFJY/-.git hermes-deploy
fi
cd hermes-deploy
git fetch origin
git checkout $repoBranch 2>/dev/null || git checkout cursor/hermes-desktop-ebbd
bash scripts/install-local.sh
"@

Write-Host ""
Write-Host "正在 WSL 内安装（首次可能需几分钟）..."
wsl -e bash -lc $installCmd

$shortcutScript = Join-Path $PSScriptRoot "windows\Create-HermesShortcuts.ps1"
if (Test-Path $shortcutScript) {
    Write-Host ""
    Write-Host "==> 创建 Windows 桌面快捷方式 ..."
    & $shortcutScript
}

Write-Host ""
Write-Host "完成。"
Write-Host "  WSL 终端: wsl  然后运行  hermes"
Write-Host "  Windows 桌面: Hermes Agent (DeepSeek) / Hermes 控制台"
