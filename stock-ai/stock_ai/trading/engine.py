from __future__ import annotations

from datetime import datetime, timezone

from stock_ai.analysis.signal import TradeSignal
from stock_ai.trading.portfolio import Portfolio, Position, TradeRecord


class PaperTradingEngine:
    """Simulated order execution — no real broker connection."""

    def __init__(
        self,
        portfolio: Portfolio,
        commission_rate: float = 0.0003,
        slippage_rate: float = 0.0005,
        max_position_pct: float = 0.25,
    ):
        self.portfolio = portfolio
        self.commission_rate = commission_rate
        self.slippage_rate = slippage_rate
        self.max_position_pct = max_position_pct

    def execute(self, signal: TradeSignal, price: float, equity: float) -> TradeRecord | None:
        if signal.action == "hold":
            return None

        ts = datetime.now(timezone.utc).isoformat()
        pos = self.portfolio.positions.get(signal.symbol)

        if signal.action == "buy":
            fill = price * (1 + self.slippage_rate)
            max_value = equity * self.max_position_pct
            current_value = self.portfolio.position_value(signal.symbol, fill)
            budget = min(self.portfolio.cash, max(0.0, max_value - current_value))
            if budget < fill * 10:
                return None
            shares = int(budget / fill)
            if shares <= 0:
                return None
            cost = shares * fill
            commission = cost * self.commission_rate
            total = cost + commission
            if total > self.portfolio.cash:
                return None
            self.portfolio.cash -= total
            if pos:
                new_shares = pos.shares + shares
                pos.avg_cost = (pos.avg_cost * pos.shares + fill * shares) / new_shares
                pos.shares = new_shares
            else:
                self.portfolio.positions[signal.symbol] = Position(
                    symbol=signal.symbol, shares=shares, avg_cost=fill
                )
            record = TradeRecord(
                timestamp=ts,
                symbol=signal.symbol,
                side="buy",
                shares=shares,
                price=fill,
                commission=commission,
                reason=signal.reason,
            )
            self.portfolio.trades.append(record)
            return record

        if signal.action == "sell" and pos and pos.shares > 0:
            fill = price * (1 - self.slippage_rate)
            shares = pos.shares
            proceeds = shares * fill
            commission = proceeds * self.commission_rate
            self.portfolio.cash += proceeds - commission
            del self.portfolio.positions[signal.symbol]
            record = TradeRecord(
                timestamp=ts,
                symbol=signal.symbol,
                side="sell",
                shares=shares,
                price=fill,
                commission=commission,
                reason=signal.reason,
            )
            self.portfolio.trades.append(record)
            return record

        return None
