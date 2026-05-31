# Hermes Agent + DeepSeek 部署

本仓库提供在 Linux 上安装 **最新版 [Hermes Agent](https://github.com/NousResearch/hermes-agent)**，并将 **DeepSeek** 配置为推理后端的脚本与说明。

## 环境要求

- Linux（Ubuntu/Debian 等）或 WSL2
- Git、curl
- 约 2GB 磁盘（不含本地大模型）
- [DeepSeek API Key](https://platform.deepseek.com/)

## 一键安装

```bash
export DEEPSEEK_API_KEY='sk-你的密钥'
bash scripts/install-hermes-deepseek.sh
source ~/.bashrc
hermes
```

安装脚本会：

1. 通过官方 `install.sh` 安装 Hermes（当前主线约 v0.15.x）
2. `git pull` 同步 `~/.hermes/hermes-agent` 到最新 `main`
3. 将 `model.provider` 设为 `deepseek`，默认模型 `deepseek-v4-pro`，API 地址 `https://api.deepseek.com/v1`

## 手动配置 API Key

若未在安装时提供密钥：

```bash
hermes config set DEEPSEEK_API_KEY 'sk-你的密钥'
# 或编辑
hermes config edit   # 修改 ~/.hermes/.env
```

> 内置 `deepseek` 提供商只读取环境变量 `DEEPSEEK_API_KEY`（写入 `~/.hermes/.env`），不会使用 `config.yaml` 里的 `api_key` 字段。

## 常用命令

| 命令 | 说明 |
|------|------|
| `hermes` | 交互式对话 |
| `hermes update` | 更新到最新版（需可交互确认 upstream） |
| `hermes doctor` | 诊断环境与密钥 |
| `hermes model` | 切换模型 |
| `hermes gateway start` | 启动 Telegram/Discord 等网关 |

## 可选：systemd 网关服务

将 `scripts/hermes-gateway.service` 复制到系统目录并启用（将 `ubuntu` 换成你的用户名）：

```bash
sudo cp scripts/hermes-gateway.service /etc/systemd/system/hermes-gateway@.service
sudo systemctl daemon-reload
sudo systemctl enable --now hermes-gateway@ubuntu
```

需先在 `~/.hermes/.env` 中配置 `DEEPSEEK_API_KEY`，并完成 `hermes gateway setup`。

## 当前实例状态（Cloud Agent）

本环境已完成：

- Hermes Agent **v0.15.1** 安装于 `~/.hermes/hermes-agent`
- `~/.hermes/config.yaml` 已设置：`provider: deepseek`，`default: deepseek-v4-pro`

待你提供 `DEEPSEEK_API_KEY` 后即可直接运行 `hermes`。

## 参考

- [Hermes 文档](https://hermes-agent.nousresearch.com/docs/)
- [DeepSeek × Hermes 集成说明](https://api-docs.deepseek.com/quick_start/agent_integrations/hermes)
