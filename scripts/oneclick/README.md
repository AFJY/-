# 一键安装包（本机 + 桌面）

## Windows（推荐：双击）

1. 下载本目录中的文件，或克隆仓库后进入 `scripts/oneclick/`
2. **双击** `Install-HermesDesktop.bat`
3. 按提示输入 `DEEPSEEK_API_KEY`（或在运行前设置环境变量）

### 一行命令（PowerShell）

```powershell
$env:DEEPSEEK_API_KEY = "sk-你的密钥"
Set-ExecutionPolicy -Scope Process Bypass
irm https://raw.githubusercontent.com/AFJY/-/cursor/hermes-desktop-deploy-a460/scripts/oneclick/Install-HermesDesktop.ps1 | iex
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
