from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path


class EquityLogger:
    """Append equity snapshots for P&L curve on dashboard."""

    def __init__(self, log_file: Path, max_points: int = 2000):
        self.log_file = log_file
        self.max_points = max_points
        self.log_file.parent.mkdir(parents=True, exist_ok=True)

    def _load(self) -> list[dict]:
        if not self.log_file.exists():
            return []
        return json.loads(self.log_file.read_text(encoding="utf-8"))

    def append(self, equity: float, monthly_return_pct: float = 0.0) -> None:
        points = self._load()
        points.append({
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "equity": round(equity, 2),
            "monthly_return_pct": round(monthly_return_pct, 4),
        })
        if len(points) > self.max_points:
            points = points[-self.max_points :]
        self.log_file.write_text(json.dumps(points, indent=2), encoding="utf-8")

    def get_curve(self, limit: int = 500) -> list[dict]:
        return self._load()[-limit:]
