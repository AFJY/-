# Hermes Agent + DeepSeek 部署

本仓库提供在 Linux 上安装 **最新版 [Hermes Agent](https://github.com/NousResearch/hermes-agent)**，并将 **DeepSeek** 配置为推理后端的脚本与说明。

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
