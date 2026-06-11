# Stock AI — 模拟盘自动交易

基于**公开行情数据**（yfinance）和**公开新闻 RSS** 的股票 AI 模拟交易系统。

> **重要声明**：本项目仅用于学习与研究，执行的是**模拟交易**，不连接任何真实券商，不构成投资建议。历史回测表现不代表未来收益。

## 功能

- 从 Yahoo Finance 拉取大盘指数 ETF 与个股日线数据
- 技术指标特征（RSI、MACD、布林带、成交量等）+ 梯度提升树学习涨跌方向
- 公开财经 RSS 新闻情绪辅助信号
- 模拟盘：虚拟资金、手续费、滑点、仓位限制
- 历史回测与状态持久化

## 快速开始

```bash
cd stock-ai
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

# 1. 用历史数据训练模型
python main.py train

# 2. 执行一轮模拟自动交易
python main.py run

# 3. 查看持仓状态
python main.py status

# 4. 单标的回测
python main.py backtest -s SPY
```

## 定时自动运行（可选）

```bash
# 每个交易日 16:30 运行（按服务器时区）
(crontab -l 2>/dev/null; echo "30 16 * * 1-5 cd /path/to/stock-ai && .venv/bin/python main.py run >> logs/cron.log 2>&1") | crontab -
```

## 配置

编辑 `config.yaml`：

- `market.indices` / `market.watchlist` — 交易标的
- `trading.initial_capital` — 模拟初始资金
- `trading.min_confidence` — 信号置信度阈值
- `news.rss_feeds` — 公开新闻源

## 架构

```
行情(yfinance) ──┐
                 ├── 特征工程 ── ML模型 ── 信号聚合 ── 模拟撮合 ── portfolio_state.json
新闻(RSS)     ───┘                              ↑
                                           新闻情绪权重
```

## 局限

- 免费行情有延迟，A 股覆盖有限
- 新闻情绪为词典法，精度有限
- ML 模型为简化版方向预测，不保证盈利
- 未含风控以外的合规、税务、实盘接入
