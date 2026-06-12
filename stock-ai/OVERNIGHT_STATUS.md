# Stock AI 夜间运行状态

> 自动生成供早上查看。服务在云端 VM 持续运行。

## 已自动处理

- [x] `main.py serve` 仪表盘 + 后台 30s 盯盘循环
- [x] 夜间守护 `scripts/overnight-watchdog.sh`（服务挂掉自动重启）
- [x] 每 5 分钟权益快照写入 `logs/overnight.log`
- [x] 月目标同步修复（config 8% 与状态文件一致）
- [x] Yahoo RSS 429 限流 → 已加 akshare A 股新闻备用源
- [x] DeepSeek 新闻情绪已验证可用
- [x] WebSocket 连接改为轻量 snapshot，避免卡顿

## 早上快速查看

```bash
# 最新权益
curl -s http://127.0.0.1:8765/api/status | python3 -m json.tool

# 夜间日志
tail -50 stock-ai/logs/overnight.log

# 收益曲线数据
cat stock-ai/data/equity_curve.json
```

浏览器（若端口已转发）: http://localhost:8765

---

## 需你本机处理（我无法在云端代做）

### 1. 同花顺远航版桥接 — 必须在你 Windows 桌面跑

云端服务**无法连接**你家里的同花顺软件。早上请在你电脑执行：

```powershell
cd stock-ai\bridge
python ths_agent.py --server ws://<云端IP或本机IP>:8765/ws/ths --sync-watchlist --ui
```

- 若服务跑在你本机：`ws://127.0.0.1:8765/ws/ths`
- 若服务在云端：需把 8765 端口映射到你本机，或用内网穿透

**没有桥接时**：A 股实时价走 yfinance 回退（有延迟，非真正盘面）。

### 2. akshare 全市场接口在云端不稳定

单标的查询可用；批量 `stock_zh_a_spot_em` 可能超时。已通过：
- 单标的 `stock_bid_ask_em`
- yfinance 回退
- 建议你本机跑 `ths_agent` 推行情

### 3. 非交易时段

夜间/周末 A 股休市，行情不更新、不会成交，属正常现象。

### 4. 模拟盘 ≠ 实盘

当前所有交易均为虚拟资金，未接券商。

---

## 配置文件

- 月目标：`config.yaml` → `monthly.target_return_pct: 8.0`
- 修改：`python main.py target 8`

---

*最后更新：服务启动时由 Agent 写入*
