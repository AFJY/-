from __future__ import annotations

import asyncio
import json
import threading
from datetime import datetime, timezone
from typing import Any, Callable

from stock_ai.analysis.learner import SignalLearner
from stock_ai.analysis.signal import SignalAggregator, TradeSignal
from stock_ai.config import load_config, resolve_path
from stock_ai.data.fetcher import MarketDataFetcher
from stock_ai.data.realtime import QuoteStore, RealtimeDataFetcher, RealtimeQuote
from stock_ai.news_factory import build_news_analyzer
from stock_ai.runner import all_symbols
from stock_ai.trading.engine import PaperTradingEngine
from stock_ai.trading.equity_log import EquityLogger
from stock_ai.trading.monthly import MonthlyManager
from stock_ai.trading.portfolio import Portfolio
from stock_ai.trading.risk import RiskManager


class RealtimeMonitor:
    """Background real-time quote polling + optional auto paper trading."""

    def __init__(self, config_path: str = "config.yaml"):
        self.config_path = config_path
        self.config = load_config(config_path)
        self.quote_store = QuoteStore()
        self.rt_fetcher = RealtimeDataFetcher()
        self.hist_fetcher = MarketDataFetcher()
        self._running = False
        self._paused = False
        self._thread: threading.Thread | None = None
        self._subscribers: list[Callable[[dict], None]] = []
        self._loop: asyncio.AbstractEventLoop | None = None

        trading = self.config["trading"]
        monthly_cfg = self.config.get("monthly", {})
        self.monthly = MonthlyManager(
            resolve_path(monthly_cfg.get("state_file", "data/monthly_state.json"), self.config),
            target_return_pct=monthly_cfg.get("target_return_pct", 5.0),
        )
        state_file = resolve_path(self.config["runtime"]["state_file"], self.config)
        self.portfolio = Portfolio.load(state_file, trading["initial_capital"])
        self.engine = PaperTradingEngine(
            portfolio=self.portfolio,
            commission_rate=trading["commission_rate"],
            slippage_rate=trading["slippage_rate"],
            max_position_pct=trading["max_position_pct"],
        )
        self.learner = SignalLearner(resolve_path(self.config["runtime"]["model_dir"], self.config))
        news_cfg = self.config.get("news", {})
        news_analyzer = build_news_analyzer(news_cfg)
        risk_cfg = self.config.get("risk", {})
        self.risk = RiskManager(
            stop_loss_pct=risk_cfg.get("stop_loss_pct", 0.08),
            take_profit_pct=risk_cfg.get("take_profit_pct", 0.15),
            trailing_stop_pct=risk_cfg.get("trailing_stop_pct", 0.05),
        )
        self.equity_log = EquityLogger(
            resolve_path(self.config["runtime"].get("equity_log", "data/equity_curve.json"), self.config)
        )
        self.aggregator = SignalAggregator(
            learner=self.learner,
            news_analyzer=news_analyzer,
            sentiment_weight=news_cfg.get("sentiment_weight", 0.15),
            min_confidence=trading["min_confidence"],
        )
        self._last_signals: list[dict] = []
        self._last_news_score = 0.0

    def subscribe(self, callback: Callable[[dict], None]) -> None:
        self._subscribers.append(callback)

    def _broadcast(self, event: dict) -> None:
        for cb in self._subscribers:
            try:
                cb(event)
            except Exception:
                pass

    def ingest_ths_quote(self, payload: dict) -> RealtimeQuote:
        quote = RealtimeQuote(
            symbol=payload["symbol"],
            name=payload.get("name", payload["symbol"]),
            price=float(payload["price"]),
            change_pct=float(payload.get("change_pct", 0)),
            volume=float(payload.get("volume", 0)),
            timestamp=payload.get("timestamp", datetime.now(timezone.utc).isoformat()),
            source="ths_bridge",
        )
        self.quote_store.update(quote)
        return quote

    def _get_price(self, symbol: str, fallback: float | None = None) -> float:
        q = self.quote_store.get(symbol)
        if q:
            return q.price
        try:
            quote = self.rt_fetcher.fetch_quote(symbol)
            self.quote_store.update(quote)
            return quote.price
        except (ValueError, OSError, ImportError):
            return fallback or 0.0

    def tick(self) -> dict[str, Any]:
        symbols = all_symbols(self.config)
        quotes: list[RealtimeQuote] = []

        for sym in symbols:
            cached = self.quote_store.get(sym)
            if cached and cached.source == "ths_bridge":
                quotes.append(cached)
                continue
            try:
                q = self.rt_fetcher.fetch_quote(sym)
                self.quote_store.update(q)
                quotes.append(q)
            except (ValueError, OSError, ImportError):
                if cached:
                    quotes.append(cached)

        prices = {q.symbol: q.price for q in quotes}
        equity = self.portfolio.total_equity(prices)
        cycle = self.monthly.update_equity(equity)
        min_conf = self.monthly.adjust_confidence(
            self.config["trading"]["min_confidence"], cycle
        )
        self.aggregator.min_confidence = min_conf

        executed = []
        signals: list[TradeSignal] = []
        auto_trade = self.config.get("realtime", {}).get("auto_trade", True)

        if not self._paused and auto_trade:
            # Risk management: stop-loss / take-profit
            for sym, reason in self.risk.scan_portfolio(self.portfolio, prices):
                p = prices.get(sym, 0)
                if p > 0:
                    sig = TradeSignal(sym, "sell", 1.0, "sell", 1.0, 0.0, reason)
                    trade = self.engine.execute(sig, p, equity)
                    if trade:
                        executed.append(trade)

            news = None
            if self.aggregator.news_analyzer:
                news = self.aggregator.news_analyzer.analyze()
                self._last_news_score = news.score
            for sym in symbols:
                try:
                    df = self.hist_fetcher.fetch_history(
                        sym, days=self.config["learning"]["lookback_days"]
                    )
                    signal = self.aggregator.generate(sym, df, news=news)
                    signals.append(signal)
                    trade = self.engine.execute(signal, self._get_price(sym, prices.get(sym, 0)), equity)
                    if trade:
                        executed.append(trade)
                except (ValueError, OSError, FileNotFoundError):
                    continue
            if executed:
                cycle = self.monthly.update_equity(
                    self.portfolio.total_equity(prices), trades_delta=len(executed)
                )

        state_file = resolve_path(self.config["runtime"]["state_file"], self.config)
        self.portfolio.save(state_file)

        self._last_signals = [
            {"symbol": s.symbol, "action": s.action, "confidence": s.confidence, "reason": s.reason}
            for s in signals
        ]
        self.equity_log.append(equity, cycle.return_pct)

        payload = {
            "type": "tick",
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "quotes": [
                {
                    "symbol": q.symbol,
                    "name": q.name,
                    "price": q.price,
                    "change_pct": q.change_pct,
                    "source": q.source,
                }
                for q in quotes
            ],
            "portfolio": {
                "equity": equity,
                "cash": self.portfolio.cash,
                "positions": {s: p.shares for s, p in self.portfolio.positions.items()},
            },
            "monthly": cycle.to_dict(),
            "signals": self._last_signals,
            "executed": len(executed),
            "paused": self._paused,
            "ths_connected": self.quote_store.ths_connected,
            "news_score": self._last_news_score,
            "equity_curve": self.equity_log.get_curve(200),
        }
        self._broadcast(payload)
        return payload

    def reload_config(self) -> None:
        self.config = load_config(self.config_path)

    def set_monthly_target(self, pct: float) -> float:
        from stock_ai.config_manager import set_monthly_target
        set_monthly_target(pct, self.config_path)
        self.monthly.target_return_pct = pct
        self.reload_config()
        return pct

    def sync_watchlist(self, symbols: list[str]) -> list[str]:
        from stock_ai.config_manager import sync_watchlist
        result = sync_watchlist(symbols, self.config_path)
        self.reload_config()
        return result

    def _loop_run(self) -> None:
        interval = self.config.get("realtime", {}).get("poll_interval_sec", 30)
        while self._running:
            try:
                self.tick()
            except Exception as e:
                self._broadcast({"type": "error", "message": str(e)})
            threading.Event().wait(interval)

    def start(self) -> None:
        if self._running:
            return
        self._running = True
        self._thread = threading.Thread(target=self._loop_run, daemon=True)
        self._thread.start()

    def stop(self) -> None:
        self._running = False

    def pause(self) -> None:
        self._paused = True

    def resume(self) -> None:
        self._paused = False

    def handle_command(self, text: str) -> dict:
        """Interactive command interface for user / agent."""
        cmd = text.strip().lower()
        if cmd in ("status", "状态"):
            prices = {q.symbol: q.price for q in self.quote_store.all_quotes()}
            equity = self.portfolio.total_equity(prices) if prices else self.portfolio.cash
            cycle = self.monthly.ensure_cycle(equity)
            return {
                "ok": True,
                "message": f"权益 {equity:,.2f}，本月收益 {cycle.return_pct:+.2f}%（目标 {cycle.target_return_pct}%）",
                "data": {"equity": equity, "monthly": cycle.to_dict()},
            }
        if cmd in ("pause", "暂停"):
            self.pause()
            return {"ok": True, "message": "已暂停自动交易"}
        if cmd in ("resume", "继续", "恢复"):
            self.resume()
            return {"ok": True, "message": "已恢复自动交易"}
        if cmd in ("tick", "刷新"):
            return {"ok": True, "message": "已刷新", "data": self.tick()}
        if cmd.startswith("train") or cmd.startswith("训练"):
            from stock_ai.runner import train_all
            train_all(self.config)
            return {"ok": True, "message": "模型训练完成"}
        if cmd.startswith("target ") or cmd.startswith("月目标 "):
            try:
                pct = float(cmd.split()[-1].replace("%", ""))
                self.set_monthly_target(pct)
                return {"ok": True, "message": f"月目标已设为 {pct}%"}
            except ValueError:
                return {"ok": False, "message": "用法: target 8  (表示月目标 8%)"}
        if cmd in ("help", "帮助"):
            return {
                "ok": True,
                "message": "命令: status, pause, resume, tick, train, target 8, help",
            }
        return {"ok": False, "message": f"未知命令: {text}。输入 help 查看帮助。"}


# Singleton for web server
_monitor: RealtimeMonitor | None = None


def get_monitor(config_path: str = "config.yaml") -> RealtimeMonitor:
    global _monitor
    if _monitor is None:
        _monitor = RealtimeMonitor(config_path)
    return _monitor
