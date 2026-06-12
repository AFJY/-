from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml

from stock_ai.config import DEFAULT_CONFIG, ROOT, load_config


def save_config(config: dict[str, Any], path: Path | str | None = None) -> None:
    cfg_path = Path(path) if path else DEFAULT_CONFIG
    with cfg_path.open("w", encoding="utf-8") as f:
        yaml.safe_dump(config, f, allow_unicode=True, default_flow_style=False, sort_keys=False)


def set_monthly_target(pct: float, path: Path | str | None = None) -> float:
    config = load_config(path)
    config.setdefault("monthly", {})["target_return_pct"] = float(pct)
    save_config(config, path)
    return float(pct)


def sync_watchlist(symbols: list[str], path: Path | str | None = None) -> list[str]:
    """Replace market.watchlist with normalized symbols."""
    config = load_config(path)
    normalized = []
    for sym in symbols:
        s = sym.strip().upper()
        if not s:
            continue
        if "." not in s and s.isdigit() and len(s) == 6:
            s = f"{s}.SS" if s.startswith("6") else f"{s}.SZ"
        normalized.append(s)
    config.setdefault("market", {})["watchlist"] = list(dict.fromkeys(normalized))
    save_config(config, path)
    return config["market"]["watchlist"]
