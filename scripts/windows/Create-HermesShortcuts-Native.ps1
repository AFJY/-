# 仅创建 Windows 桌面快捷方式（Hermes 已安装后补建图标）
# 优先本机原生 Hermes.exe，其次 hermes desktop，最后 WSL。

$ErrorActionPreference = "Stop"

$desktop = [Environment]::GetFolderPath("Desktop")

function New-Shortcut($name, $target, $args, $comment) {
    $lnk = Join-Path $desktop "$name.lnk"
    $shell = New-Object -ComObject WScript.Shell
    $sc = $shell.CreateShortcut($lnk)
    $sc.TargetPath = $target
    $sc.Arguments = $args
    $sc.Description = $comment
    $sc.WorkingDirectory = $env:USERPROFILE
    $sc.Save()
    Write-Host "已创建: $lnk"
}

$hermesExe = "$env:LOCALAPPDATA\hermes\hermes-agent\apps\desktop\release\win-unpacked\Hermes.exe"
$hermesCmd = Get-Command hermes -ErrorAction SilentlyContinue

if (Test-Path $hermesExe) {
    New-Shortcut "Hermes Agent (DeepSeek)" $hermesExe "" "Hermes 原生桌面"
    if ($hermesCmd) {
        New-Shortcut "Hermes 控制台" "powershell.exe" '-NoExit -Command "hermes dashboard --port 9119"' "Web 管理面板"
    }
    Write-Host ""
    Write-Host "完成。请查看 Windows 桌面。" -ForegroundColor Green
    exit 0
}

if ($hermesCmd) {
    New-Shortcut "Hermes Agent (DeepSeek)" "powershell.exe" '-NoExit -Command "hermes desktop"' "Hermes 桌面 GUI"
    New-Shortcut "Hermes 终端" $hermesCmd.Source "" "Hermes 终端"
    New-Shortcut "Hermes 控制台" "powershell.exe" '-NoExit -Command "hermes dashboard --port 9119"' "Web 管理面板"
    Write-Host ""
    Write-Host "完成。请查看 Windows 桌面。" -ForegroundColor Green
    exit 0
}

if (Get-Command wsl.exe -ErrorAction SilentlyContinue) {
    & (Join-Path $PSScriptRoot "Create-HermesShortcuts.ps1")
    exit $LASTEXITCODE
}

Write-Host "未找到 hermes 或 WSL。请先运行 Install-HermesWindowsNative.ps1" -ForegroundColor Red
exit 1
