# 一键安装包（本机 + 桌面）

## Windows 本机（推荐，无需 WSL）

在 **PowerShell** 中运行（先设置 API Key）：

```powershell
$env:DEEPSEEK_API_KEY = "sk-你的密钥"
Set-ExecutionPolicy -Scope Process Bypass
irm "https://raw.githubusercontent.com/AFJY/-/cursor/hermes-desktop-deploy-a460/scripts/windows/Install-HermesWindowsNative.ps1" | iex
```

或 **双击** `Install-HermesWindowsNative.bat`（同目录下）。

安装完成后在 **Windows 桌面** 会出现：
- `Hermes Agent (DeepSeek).lnk` — 原生 GUI
- `Hermes 控制台.lnk` — Web 管理面板

程序位置：`%LOCALAPPDATA%\hermes\` · 配置：`%USERPROFILE%\.hermes\`

> 安装结束后请 **关闭并重新打开** PowerShell，再运行 `hermes`。

### 仅补建桌面图标（已装好 Hermes）

**推荐（避免引号/管道报错）：**

```powershell
Set-ExecutionPolicy -Scope Process Bypass
$url = "https://raw.githubusercontent.com/AFJY/-/cursor/hermes-desktop-deploy-a460/scripts/windows/Create-HermesShortcuts-Native.ps1"
Invoke-WebRequest -Uri $url -OutFile "$env:TEMP\hermes-shortcuts.ps1" -UseBasicParsing
& "$env:TEMP\hermes-shortcuts.ps1"
```

> 若出现「不允许使用空管道元素」，不要用 `irm ... | iex`，请用上面三行；引号必须是英文直引号 `"`。

---

## Windows + WSL2（备选）

1. 下载本目录中的文件，或克隆仓库后进入 `scripts/oneclick/`
2. **双击** `Install-HermesDesktop.bat`
3. 按提示输入 `DEEPSEEK_API_KEY`（或在运行前设置环境变量）

### 一行命令（PowerShell，需 WSL2）

```powershell
$env:DEEPSEEK_API_KEY = "sk-你的密钥"
Set-ExecutionPolicy -Scope Process Bypass
irm "https://raw.githubusercontent.com/AFJY/-/cursor/hermes-desktop-deploy-a460/scripts/oneclick/Install-HermesDesktop.ps1" | iex
```

**前置：** 已安装 WSL2（`wsl --install` 后重启）。

---

## Linux / WSL 终端

```bash
export DEEPSEEK_API_KEY='sk-你的密钥'
curl -fsSL https://raw.githubusercontent.com/AFJY/-/cursor/hermes-desktop-deploy-a460/scripts/oneclick/install-hermes-desktop.sh | bash
```

---

## 安装结果

| 平台 | 桌面 |
|------|------|
| Windows | `Hermes Agent (DeepSeek).lnk`、`Hermes 控制台.lnk` |
| Linux | `~/Desktop` 或 `~/桌面` 下的 `.desktop` 图标 |

配置与数据目录：`~/.hermes/`

---

## 文件说明

| 文件 | 作用 |
|------|------|
| `Install-HermesDesktop.bat` | Windows 双击入口 |
| `Install-HermesDesktop.ps1` | Windows 主逻辑（WSL 安装 + 桌面快捷方式） |
| `install-hermes-desktop.sh` | Linux / WSL / macOS 主逻辑 |

可选环境变量：`HERMES_DEPLOY_REPO`、`HERMES_DEPLOY_BRANCH`、`HERMES_DEPLOY_DIR`
