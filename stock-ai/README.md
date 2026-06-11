# Stock AI — 实时盯盘 · 月度模拟交易

基于公开行情 + ML + **DeepSeek 新闻解读** 的 A 股/美股**模拟盘**系统。  
支持 Web 仪表盘、同花顺自选股桥接、止损止盈、收益曲线。

> **声明**：仅用于学习研究，模拟交易，不构成投资建议，不保证盈利。

## 功能

| 功能 | 说明 |
|------|------|
| 月度周期 | 月目标收益追踪（默认 8%，可改） |
| 实时盯盘 | WebSocket 推送 + 30s 轮询 |
| DeepSeek 新闻 | 读取 `DEEPSEEK_API_KEY` 解读 RSS 财经新闻 |
| 风控 | 止损 8% / 止盈 15% / 移动止盈 5% |
| 收益曲线 | 仪表盘 Canvas 实时绘制 |
| 同花顺自选股 | 桥接脚本自动读取并同步 watchlist |
| 交互 | 网页命令 / API / 与我（Cursor）协作改代码 |

## 本机部署

### Linux / macOS

```bash
cd stock-ai
bash scripts/install-local.sh
python3 main.py train
bash scripts/start-stock-ai.sh
# 或: python3 main.py serve
```

### Windows（推荐：同花顺在同台电脑）

```powershell
cd stock-ai
.\scripts\install-windows.ps1
python main.py train
python main.py serve
```

**另开终端 — 同花顺桥接（读自选股 + 推行情）：**

```powershell
cd bridge
python ths_agent.py --server ws://127.0.0.1:8765/ws/ths --sync-watchlist --ui
```

浏览器：**http://localhost:8765**

## 同花顺自选股

读取顺序：
1. `bridge/watchlist.json`（可手动编辑，参考 `watchlist.json.example`）
2. 扫描同花顺安装目录下的自选股文件
3. `--ui` 从同花顺窗口读取（需 `pip install pywinauto`）

```bash
# 仅查看能读到哪些自选股
python bridge/ths_watchlist.py --ui
```

## 常用命令

```bash
python main.py train          # 训练模型
python main.py serve          # 启动仪表盘
python main.py run            # 手动跑一轮
python main.py target 8       # 设置月目标 8%
python main.py status         # 查看持仓
```

网页/API：
- `POST /api/monthly/target` `{"target_return_pct": 8}`
- `POST /api/watchlist/sync` `{"symbols": ["600519.SS"]}`
- `POST /api/command` `{"command": "status"}`

## 配置

`config.yaml` 关键项：

```yaml
monthly:
  target_return_pct: 8.0

risk:
  stop_loss_pct: 0.08
  take_profit_pct: 0.15

news:
  llm_enabled: true    # DeepSeek，Key 来自环境变量或 ~/.hermes/.env
```

## 架构

```
同花顺桌面 ──ths_agent──► WebSocket /ws/ths
                              │
DeepSeek ◄── RSS 新闻 ────────┤
                              ▼
                         ML + 风控 + 月目标
                              ▼
                    模拟撮合 + 收益曲线
                              ▼
                      http://localhost:8765
```
