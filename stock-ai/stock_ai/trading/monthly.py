from __future__ import annotations

import json
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path


@dataclass
class MonthlyCycle:
    month: str  # YYYY-MM
    start_equity: float
    target_return_pct: float
    current_equity: float
    trades_count: int = 0

    @property
    def return_pct(self) -> float:
        if self.start_equity <= 0:
            return 0.0
        return (self.current_equity / self.start_equity - 1.0) * 100.0

    @property
    def target_equity(self) -> float:
        return self.start_equity * (1.0 + self.target_return_pct / 100.0)

    @property
    def progress_pct(self) -> float:
        """Progress toward monthly target (can exceed 100%)."""
        gain = self.current_equity - self.start_equity
        target_gain = self.target_equity - self.start_equity
        if target_gain <= 0:
            return 100.0
        return (gain / target_gain) * 100.0

    @property
    def on_track(self) -> bool:
        return self.return_pct >= self.target_return_pct

    def to_dict(self) -> dict:
        d = asdict(self)
        d.update({
            "return_pct": round(self.return_pct, 4),
            "target_equity": round(self.target_equity, 2),
            "progress_pct": round(self.progress_pct, 2),
            "on_track": self.on_track,
        })
        return d


class MonthlyManager:
    def __init__(self, state_file: Path, target_return_pct: float = 5.0):
        self.state_file = state_file
        self.target_return_pct = target_return_pct
        self.state_file.parent.mkdir(parents=True, exist_ok=True)

    def _current_month(self) -> str:
        return datetime.now(timezone.utc).strftime("%Y-%m")

    def load_history(self) -> dict:
        if not self.state_file.exists():
            return {"cycles": [], "current": None}
        return json.loads(self.state_file.read_text(encoding="utf-8"))

    def save_history(self, data: dict) -> None:
        self.state_file.write_text(json.dumps(data, indent=2), encoding="utf-8")

    def ensure_cycle(self, current_equity: float) -> MonthlyCycle:
        data = self.load_history()
        month = self._current_month()
        current = data.get("current")

        if not current or current.get("month") != month:
            if current:
                data.setdefault("cycles", []).append(current)
            current = MonthlyCycle(
                month=month,
                start_equity=current_equity,
                target_return_pct=self.target_return_pct,
                current_equity=current_equity,
            ).to_dict()
            data["current"] = current
            self.save_history(data)

        cycle = MonthlyCycle(
            month=current["month"],
            start_equity=current["start_equity"],
            target_return_pct=current["target_return_pct"],
            current_equity=current_equity,
            trades_count=current.get("trades_count", 0),
        )
        return cycle

    def update_equity(self, current_equity: float, trades_delta: int = 0) -> MonthlyCycle:
        data = self.load_history()
        cycle = self.ensure_cycle(current_equity)
        cycle.current_equity = current_equity
        cycle.trades_count += trades_delta
        data["current"] = cycle.to_dict()
        self.save_history(data)
        return cycle

    def adjust_confidence(self, base_confidence: float, cycle: MonthlyCycle) -> float:
        """Slightly lower threshold when behind monthly target (more active)."""
        if cycle.on_track:
            return base_confidence
        deficit = cycle.target_return_pct - cycle.return_pct
        if deficit > 2.0:
            return max(0.50, base_confidence - 0.05)
        if deficit > 0.5:
            return max(0.52, base_confidence - 0.02)
        return base_confidence
