from __future__ import annotations

from dataclasses import dataclass

import pandas as pd

from stock_ai.analysis.indicators import add_indicators
from stock_ai.analysis.learner import SignalLearner
from stock_ai.trading.engine import PaperTradingEngine
from stock_ai.trading.portfolio import Portfolio


@dataclass
class BacktestResult:
    symbol: str
    initial_capital: float
    final_equity: float
    return_pct: float
    trade_count: int
    max_drawdown_pct: float


def run_backtest(
    symbol: str,
    df: pd.DataFrame,
    learner: SignalLearner,
    initial_capital: float = 100000.0,
    min_confidence: float = 0.55,
) -> BacktestResult:
    """Walk-forward style backtest on historical data."""
    enriched = add_indicators(df)
    portfolio = Portfolio(cash=initial_capital, initial_capital=initial_capital)
    engine = PaperTradingEngine(portfolio=portfolio, max_position_pct=0.5)

    model_path = learner.model_dir / f"{symbol.replace('.', '_')}.joblib"
    if not model_path.exists():
        learner.train(symbol, df)

    equity_curve: list[float] = []
    start_idx = 60

    for i in range(start_idx, len(enriched) - 1):
        window = enriched.iloc[: i + 1]
        price = float(enriched["close"].iloc[i])
        try:
            action, conf = learner.predict(symbol, window)
        except FileNotFoundError:
            learner.train(symbol, window)
            action, conf = learner.predict(symbol, window)

        from stock_ai.analysis.signal import TradeSignal

        signal = TradeSignal(
            symbol=symbol,
            action=action if conf >= min_confidence else "hold",
            confidence=conf,
            ml_action=action,
            ml_confidence=conf,
            news_score=0.0,
            reason="backtest",
        )
        equity = portfolio.total_equity({symbol: price})
        engine.execute(signal, price, equity)
        equity_curve.append(portfolio.total_equity({symbol: price}))

    final_price = float(enriched["close"].iloc[-1])
    final_equity = portfolio.total_equity({symbol: final_price})
    ret = (final_equity / initial_capital - 1.0) * 100.0

    max_dd = 0.0
    if equity_curve:
        peak = equity_curve[0]
        for eq in equity_curve:
            peak = max(peak, eq)
            dd = (peak - eq) / peak * 100.0 if peak else 0.0
            max_dd = max(max_dd, dd)

    return BacktestResult(
        symbol=symbol,
        initial_capital=initial_capital,
        final_equity=final_equity,
        return_pct=ret,
        trade_count=len(portfolio.trades),
        max_drawdown_pct=max_dd,
    )
