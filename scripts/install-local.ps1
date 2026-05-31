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

Write-Host ""
Write-Host "完成。在 WSL/Ubuntu 终端运行: hermes"
Write-Host "Windows 桌面快捷方式: 在 WSL 的 ~/Desktop 或运行 install-desktop-shortcuts.sh"
Write-Host "也可在资源管理器打开: \\wsl$\Ubuntu\home\你的用户名\Desktop"
