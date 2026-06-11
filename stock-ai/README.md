# Stock AI — 实时盯盘 · 月度模拟交易

基于**公开行情** + **ML 学习** + **新闻情绪**的 A 股/美股**模拟盘**系统。  
支持 **Web 实时仪表盘**、**命令交互**、**同花顺桌面桥接**。

> **声明**：仅用于学习研究，模拟交易，不构成投资建议，不保证盈利。

## 功能一览

| 功能 | 说明 |
|------|------|
| 月度周期 | 每月初记录起始权益，追踪月目标收益率（默认 5%） |
| 实时盯盘 | 30 秒轮询行情，WebSocket 推送到仪表盘 |
| 实时模拟交易 | 基于实时价 + ML 信号自动模拟下单 |
| 与我交互 | 网页/API/WebSocket 发送命令：`status` `pause` `resume` `tick` `train` |
| 同花顺桥接 | Windows 桌面运行 `bridge/ths_agent.py` 推送行情 |

## 快速开始

```bash
cd stock-ai
pip install -r requirements.txt

python main.py train      # 训练模型
python main.py serve      # 启动实时仪表盘 (http://localhost:8765)
python main.py run        # 手动执行一轮
python main.py status     # 查看持仓
```

## 实时仪表盘

```bash
python main.py serve
```

浏览器打开 **http://localhost:8765**

- 实时行情表（涨跌幅、数据来源）
- 本月收益 vs 月目标进度
- 命令输入框（与 AI/系统交互）
- WebSocket 自动刷新

### API 交互

```bash
# 轻量状态
curl http://localhost:8765/api/status

# 完整刷新 + 交易
curl -X POST http://localhost:8765/api/tick

# 命令
curl -X POST http://localhost:8765/api/command \
  -H 'Content-Type: application/json' \
  -d '{"command":"status"}'
```

## 同花顺远航版桥接

同花顺**没有公开 API**。推荐方案：

1. 你在 **Windows 桌面**用同花顺看盘
2. 同时运行桥接脚本，把实时价推送到 Stock AI

```bash
# 在 Windows（与 Stock AI 服务同网或可访问的服务器 IP）
pip install websockets akshare
python bridge/ths_agent.py \
  --server ws://YOUR_SERVER_IP:8765/ws/ths \
  --symbols 600519,000001,399001,601318 \
  --interval 5
```

连接成功后，仪表盘显示 **同花顺: 已连接**，行情来源为 `ths_bridge`。

> 桥接脚本使用 akshare 获取 A 股实时价（与盘面一致的数据源）。你在同花顺看盘，Stock AI 用同一盘面数据做决策。

## 月度收益逻辑

- `config.yaml` → `monthly.target_return_pct`：月目标（默认 5%）
- 每月 1 日自动记录 `start_equity`
- 未达目标时，系统会**略微降低**信号阈值（更积极，仍在风控内）
- 月末可查看 `data/monthly_state.json`

## 配置要点

```yaml
monthly:
  target_return_pct: 5.0    # 月目标收益 %

realtime:
  poll_interval_sec: 30     # 盯盘间隔
  auto_trade: true          # 自动模拟交易

runtime:
  web_port: 8765
```

## 架构

```
┌─────────────┐     WebSocket      ┌──────────────────┐
│ 同花顺桌面   │ ─────────────────►│  Stock AI Server  │
│ ths_agent   │                    │  (FastAPI + WS)   │
└─────────────┘                    └────────┬─────────┘
                                          │
┌─────────────┐     akshare/yfinance      │
│ 云端行情源   │ ─────────────────────────►│
└─────────────┘                           ▼
                                   ML信号 + 月目标
                                          │
                                          ▼
                                   模拟撮合 (纸面)
```

## 局限

- **不保证月收益**：目标是追踪与策略参考，不是承诺
- A 股实时：云端 akshare 可能受限，建议用桌面桥接
- 同花顺：无法直接操控软件下单，仅行情桥接
- 实盘需自行对接券商，风险自负
