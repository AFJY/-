from __future__ import annotations

from stock_ai.trading.portfolio import Portfolio, Position


class RiskManager:
    """Stop-loss, take-profit, and trailing checks."""

    def __init__(
        self,
        stop_loss_pct: float = 0.08,
        take_profit_pct: float = 0.15,
        trailing_stop_pct: float = 0.05,
    ):
        self.stop_loss_pct = stop_loss_pct
        self.take_profit_pct = take_profit_pct
        self.trailing_stop_pct = trailing_stop_pct
        self._high_water: dict[str, float] = {}

    def check(self, symbol: str, position: Position, price: float) -> str | None:
        """Return 'sell' if risk rule triggered, else None."""
        if position.shares <= 0 or position.avg_cost <= 0:
            return None

        pnl_pct = (price - position.avg_cost) / position.avg_cost
        if pnl_pct <= -self.stop_loss_pct:
            return "sell"

        if pnl_pct >= self.take_profit_pct:
            return "sell"

        hw = self._high_water.get(symbol, price)
        if price > hw:
            self._high_water[symbol] = price
            hw = price
        if hw > position.avg_cost:
            drop = (hw - price) / hw
            if drop >= self.trailing_stop_pct and pnl_pct > 0:
                return "sell"

        return None

    def scan_portfolio(self, portfolio: Portfolio, prices: dict[str, float]) -> list[tuple[str, str]]:
        triggered = []
        for sym, pos in portfolio.positions.items():
            price = prices.get(sym)
            if not price:
                continue
            action = self.check(sym, pos, price)
            if action:
                triggered.append((sym, f"risk:{action}"))
        return triggered
