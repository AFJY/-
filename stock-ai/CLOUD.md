# Stock AI 云端部署指南

服务运行在 **Cursor 云端 VM**，你的电脑通过端口转发访问。

## 一、打开仪表盘

1. 在 Cursor 左侧打开 **Ports（端口）** 面板
2. 找到 **8765**，点击 **Open in Browser**
3. 或手动访问：`http://localhost:8765`（端口已转发时）

## 二、同花顺桥接（你电脑上操作）

同花顺在你本机，行情需由本机推到云端。

### 前提

- Cursor 已转发云端 **8765** 端口到你本机
- 同花顺远航版已打开

### Windows 步骤

```powershell
# 进入项目 bridge 目录（需先 git clone 仓库到本机，或只复制 bridge 文件夹）
cd stock-ai\bridge
pip install websockets akshare

# 端口已转发时用本机地址即可
python ths_agent.py --server ws://127.0.0.1:8765/ws/ths --sync-watchlist --ui
```

或双击：`bridge\连接同花顺-云端.bat`

### 自选股

桥接会自动读取同花顺自选股；读不到则编辑 `bridge\watchlist.json`：

```json
["600519.SS", "000001.SZ", "601318.SS"]
```

### 连上标志

- 终端显示 `Connected: ...`
- 仪表盘右上角：**同花顺: 已连接**
- 行情来源变为 `ths_bridge`

## 三、云端常用命令（Agent / 终端）

```bash
cd /workspace/stock-ai
bash scripts/stock-ai.sh status    # 查看状态
bash scripts/stock-ai.sh morning   # 状态 + 日志
bash scripts/stock-ai.sh start     # 启动（若停了）
```

## 四、API（端口转发后本机可访问）

```bash
curl http://localhost:8765/api/health
curl http://localhost:8765/api/status
```

## 五、说明

| 项目 | 云端 | 你本机 |
|------|------|--------|
| Stock AI 服务 | 已部署运行 | 仅浏览器 + 桥接脚本 |
| 同花顺看盘 | — | 你打开 |
| 行情推送 | 接收 | ths_agent 发送 |
| 模拟交易 | 云端执行 | 仪表盘查看 |

> 云端 VM 重启后服务可能停止，让 Agent 执行 `bash scripts/stock-ai.sh start` 即可恢复。
