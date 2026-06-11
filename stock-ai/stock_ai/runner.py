from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

from rich.console import Console
from rich.table import Table

from stock_ai.analysis.learner import SignalLearner
from stock_ai.analysis.signal import SignalAggregator
from stock_ai.config import load_config, resolve_path
from stock_ai.data.fetcher import MarketDataFetcher
from stock_ai.data.news import NewsAnalyzer
from stock_ai.trading.engine import PaperTradingEngine
from stock_ai.trading.monthly import MonthlyManager
from stock_ai.trading.portfolio import Portfolio

console = Console()


def all_symbols(config: dict) -> list[str]:
    indices = [i["symbol"] for i in config["market"]["indices"]]
    watchlist = list(config["market"]["watchlist"])
    return list(dict.fromkeys(indices + watchlist))


def train_all(config: dict) -> list[dict]:
    fetcher = MarketDataFetcher()
    learner = SignalLearner(resolve_path(config["runtime"]["model_dir"], config))
    days = config["learning"]["lookback_days"]
    results = []
    for sym in all_symbols(config):
        try:
            df = fetcher.fetch_history(sym, days=days)
            meta = learner.train(sym, df)
            results.append(meta)
            console.print(f"[green]✓[/] Trained {sym} — accuracy {meta['test_accuracy']:.2%}")
        except (ValueError, OSError) as e:
            console.print(f"[yellow]⚠[/] Skip {sym}: {e}")
    return results


def run_paper_trading(config: dict) -> dict:
    fetcher = MarketDataFetcher()
    model_dir = resolve_path(config["runtime"]["model_dir"], config)
    state_file = resolve_path(config["runtime"]["state_file"], config)
    log_dir = resolve_path(config["runtime"]["log_dir"], config)
    log_dir.mkdir(parents=True, exist_ok=True)

    learner = SignalLearner(model_dir)
    news_cfg = config.get("news", {})
    news_analyzer = None
    if news_cfg.get("enabled", True):
        news_analyzer = NewsAnalyzer(news_cfg.get("rss_feeds", []))
    min_confidence = config["trading"]["min_confidence"]
    aggregator = SignalAggregator(
        learner=learner,
        news_analyzer=news_analyzer,
        sentiment_weight=news_cfg.get("sentiment_weight", 0.15),
        min_confidence=min_confidence,
    )

    trading = config["trading"]
    monthly_cfg = config.get("monthly", {})
    monthly = MonthlyManager(
        resolve_path(monthly_cfg.get("state_file", "data/monthly_state.json"), config),
        target_return_pct=monthly_cfg.get("target_return_pct", 5.0),
    )
    portfolio = Portfolio.load(state_file, trading["initial_capital"])
    engine = PaperTradingEngine(
        portfolio=portfolio,
        commission_rate=trading["commission_rate"],
        slippage_rate=trading["slippage_rate"],
        max_position_pct=trading["max_position_pct"],
    )

    news = news_analyzer.analyze() if news_analyzer else None
    symbols = all_symbols(config)
    prices: dict[str, float] = {}
    signals = []
    executed = []

    for sym in symbols:
        try:
            df = fetcher.fetch_history(sym, days=min(30, config["learning"]["lookback_days"]))
            prices[sym] = float(df["close"].iloc[-1])
        except (ValueError, OSError):
            pass
    pre_equity = portfolio.total_equity(prices) if prices else portfolio.cash
    cycle = monthly.ensure_cycle(pre_equity)
    aggregator.min_confidence = monthly.adjust_confidence(min_confidence, cycle)

    for sym in symbols:
        try:
            df = fetcher.fetch_history(sym, days=config["learning"]["lookback_days"])
            model_path = model_dir / f"{sym.replace('.', '_')}.joblib"
            if not model_path.exists():
                learner.train(sym, df)
            price = float(df["close"].iloc[-1])
            prices[sym] = price
            signal = aggregator.generate(sym, df, news=news)
            signals.append(signal)
            equity = portfolio.total_equity(prices)
            trade = engine.execute(signal, price, equity)
            if trade:
                executed.append(trade)
        except (ValueError, OSError, FileNotFoundError) as e:
            console.print(f"[yellow]⚠[/] {sym}: {e}")

    equity = portfolio.total_equity(prices)
    cycle = monthly.update_equity(equity, trades_delta=len(executed))
    portfolio.save(state_file)
    summary = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "equity": equity,
        "cash": portfolio.cash,
        "monthly": cycle.to_dict(),
        "positions": {s: p.shares for s, p in portfolio.positions.items()},
        "signals": [
            {"symbol": s.symbol, "action": s.action, "confidence": s.confidence, "reason": s.reason}
            for s in signals
        ],
        "executed_trades": len(executed),
        "news_score": news.score if news else 0.0,
    }
    log_file = log_dir / f"run_{datetime.now(timezone.utc).strftime('%Y%m%d_%H%M%S')}.json"
    log_file.write_text(json.dumps(summary, indent=2), encoding="utf-8")
    return summary


def print_status(summary: dict, config: dict) -> None:
    table = Table(title="Stock AI 模拟盘运行结果")
    table.add_column("项目")
    table.add_column("值", justify="right")
    table.add_row("总权益", f"{summary['equity']:,.2f}")
    table.add_row("现金", f"{summary['cash']:,.2f}")
    table.add_row("本次成交", str(summary["executed_trades"]))
    table.add_row("新闻情绪", f"{summary['news_score']:+.2f}")
    if "monthly" in summary:
        m = summary["monthly"]
        table.add_row("本月收益", f"{m['return_pct']:+.2f}%")
        table.add_row("月目标进度", f"{m['progress_pct']:.0f}%")
    console.print(table)

    sig_table = Table(title="交易信号")
    sig_table.add_column("代码")
    sig_table.add_column("动作")
    sig_table.add_column("置信度")
    sig_table.add_column("说明")
    for s in summary["signals"]:
        sig_table.add_row(s["symbol"], s["action"], f"{s['confidence']:.2f}", s["reason"][:60])
    console.print(sig_table)
