# Create Windows desktop shortcuts that launch Hermes inside WSL.
# Usage: .\scripts\windows\Create-HermesShortcuts.ps1

$ErrorActionPreference = "Stop"

$desktop = [Environment]::GetFolderPath("Desktop")
$wsl = (Get-Command wsl.exe -ErrorAction SilentlyContinue).Source
if (-not $wsl) {
    Write-Host "未找到 wsl.exe，请先安装 WSL2: wsl --install"
    exit 1
}

$chatArgs = '-e bash -lc "export PATH=$HOME/.local/bin:$HOME/.npm-global/bin:$PATH; cd ~; exec hermes --tui"'
$dashArgs = '-e bash -lc "export PATH=$HOME/.local/bin:$HOME/.npm-global/bin:$PATH; PORT=9119; hermes dashboard --stop 2>/dev/null; nohup hermes dashboard --port $PORT --no-open --tui >/tmp/hermes-dashboard.log 2>&1 & sleep 2; cmd.exe /c start http://127.0.0.1:$PORT/"'

function New-HermesShortcut($name, $arguments, $comment) {
    $path = Join-Path $desktop "$name.lnk"
    $shell = New-Object -ComObject WScript.Shell
    $sc = $shell.CreateShortcut($path)
    $sc.TargetPath = $wsl
    $sc.Arguments = $arguments
    $sc.Description = $comment
    $sc.WorkingDirectory = $env:USERPROFILE
    $sc.Save()
    Write-Host "已创建: $path"
}

New-HermesShortcut "Hermes Agent (DeepSeek)" $chatArgs "Hermes AI 对话 (WSL)"
New-HermesShortcut "Hermes 控制台" $dashArgs "Hermes Web 管理面板 (WSL)"

Write-Host ""
Write-Host "请在 Windows 桌面查看快捷方式。首次使用需先在 WSL 内完成 install-local.sh。"
