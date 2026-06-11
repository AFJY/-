from __future__ import annotations

import json
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from pathlib import Path


@dataclass
class Position:
    symbol: str
    shares: float
    avg_cost: float

    @property
    def market_value(self) -> float:
        return self.shares * self.avg_cost  # updated externally with price


@dataclass
class TradeRecord:
    timestamp: str
    symbol: str
    side: str
    shares: float
    price: float
    commission: float
    reason: str


@dataclass
class Portfolio:
    cash: float
    positions: dict[str, Position] = field(default_factory=dict)
    trades: list[TradeRecord] = field(default_factory=list)
    initial_capital: float = 0.0

    def total_equity(self, prices: dict[str, float]) -> float:
        holdings = sum(
            pos.shares * prices.get(sym, pos.avg_cost)
            for sym, pos in self.positions.items()
        )
        return self.cash + holdings

    def position_value(self, symbol: str, price: float) -> float:
        pos = self.positions.get(symbol)
        return pos.shares * price if pos else 0.0

    def save(self, path: Path) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        payload = {
            "cash": self.cash,
            "initial_capital": self.initial_capital,
            "positions": {k: asdict(v) for k, v in self.positions.items()},
            "trades": [asdict(t) for t in self.trades],
            "updated_at": datetime.now(timezone.utc).isoformat(),
        }
        path.write_text(json.dumps(payload, indent=2), encoding="utf-8")

    @classmethod
    def load(cls, path: Path, initial_capital: float) -> Portfolio:
        if not path.exists():
            return cls(cash=initial_capital, initial_capital=initial_capital)
        data = json.loads(path.read_text(encoding="utf-8"))
        positions = {
            k: Position(**v) for k, v in data.get("positions", {}).items()
        }
        trades = [TradeRecord(**t) for t in data.get("trades", [])]
        return cls(
            cash=float(data.get("cash", initial_capital)),
            positions=positions,
            trades=trades,
            initial_capital=float(data.get("initial_capital", initial_capital)),
        )
