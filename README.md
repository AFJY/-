# Hermes Agent + DeepSeek 部署

本仓库提供在 Linux 上安装 **最新版 [Hermes Agent](https://github.com/NousResearch/hermes-agent)**，并将 **DeepSeek** 配置为推理后端的脚本与说明。

## 一键安装包（桌面）

| 平台 | 文件 / 命令 |
|------|-------------|
| **Windows** | 双击 [`scripts/oneclick/Install-HermesDesktop.bat`](scripts/oneclick/Install-HermesDesktop.bat) |
| **Windows 一行** | `irm .../Install-HermesDesktop.ps1 \| iex`（见 [oneclick/README.md](scripts/oneclick/README.md)） |
| **Linux** | `curl -fsSL .../install-hermes-desktop.sh \| bash` |

详细说明：[scripts/oneclick/README.md](scripts/oneclick/README.md)

## 本机一键部署（在你自己的电脑上）

> **说明：** Cursor Cloud 远程环境里的桌面图标不会出现在你家电脑桌面上，必须在本机/WSL 执行下列命令。

### Linux 或 WSL2（Ubuntu）

```bash
git clone https://github.com/AFJY/-.git hermes-deploy
cd hermes-deploy
git checkout cursor/hermes-desktop-deploy-a460   # 或 cursor/hermes-desktop-ebbd
export DEEPSEEK_API_KEY='sk-你的密钥'
bash scripts/install-local.sh
source ~/.bashrc
```

完成后在 **`~/Desktop`** 或 **`~/桌面`** 双击 **Hermes Agent** / **Hermes 控制台**。

### Windows（PowerShell，通过 WSL 安装）

**前置：** 已安装 [WSL2](https://learn.microsoft.com/zh-cn/windows/wsl/install)（`wsl --install` 后重启）。

```powershell
git clone https://github.com/AFJY/-.git hermes-deploy
cd hermes-deploy
git checkout cursor/hermes-desktop-deploy-a460
$env:DEEPSEEK_API_KEY = "sk-你的密钥"
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
.\scripts\install-local.ps1
```

安装结束后，**Windows 桌面**会出现 **Hermes Agent (DeepSeek)** 和 **Hermes 控制台** 快捷方式（通过 WSL 启动）。

仅补建桌面图标（已装好 Hermes 时）：

```powershell
cd hermes-deploy
.\scripts\windows\Create-HermesShortcuts.ps1
```

### macOS

```bash
git clone https://github.com/AFJY/-.git hermes-deploy && cd hermes-deploy
git checkout cursor/hermes-desktop-deploy-a460
export DEEPSEEK_API_KEY='sk-你的密钥'
bash scripts/install-local.sh
source ~/.bashrc && hermes
```

## 环境要求

- Linux（Ubuntu/Debian 等）或 WSL2
- Git、curl
- 约 2GB 磁盘（不含本地大模型）
- [DeepSeek API Key](https://platform.deepseek.com/)

## 一键安装（DeepSeek）

```bash
export DEEPSEEK_API_KEY='sk-你的密钥'
bash scripts/install-hermes-deepseek.sh
source ~/.bashrc
hermes
```

## 完整安装（所有可自动安装的依赖）

```bash
bash scripts/install-hermes-full.sh
source ~/.bashrc
hermes doctor
```

会额外安装：全部 lazy Python 包（Telegram、Discord、Slack、Matrix、FAL、Exa 等）、Playwright Chromium、Docker、`ddgs` 免费网页搜索、Codex CLI、Skills Hub 初始化。

以下仍需你自行配置密钥（见 `.env.example`）：`DEEPSEEK_API_KEY`、`FAL_KEY`、各消息平台 Bot Token、`OPENROUTER_API_KEY`、`XAI_API_KEY` 等。`computer_use` 仅支持 macOS。

## 手动配置 API Key

```bash
hermes config set DEEPSEEK_API_KEY 'sk-你的密钥'
hermes config edit
```

> 内置 `deepseek` 提供商只读取 `DEEPSEEK_API_KEY`（`~/.hermes/.env`），不使用 `config.yaml` 里的 `api_key` 字段。

## 常用命令

| 命令 | 说明 |
|------|------|
| `hermes` | 交互式对话 |
| `hermes doctor` | 诊断环境与密钥 |
| `hermes gateway start` | 消息网关（需先 `gateway setup`） |

## 参考

- [Hermes 文档](https://hermes-agent.nousresearch.com/docs/)
- [DeepSeek × Hermes](https://api-docs.deepseek.com/quick_start/agent_integrations/hermes)
