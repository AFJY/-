from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

import joblib
import numpy as np
import pandas as pd
from sklearn.ensemble import GradientBoostingClassifier
from sklearn.metrics import accuracy_score
from sklearn.model_selection import train_test_split

from stock_ai.analysis.indicators import add_indicators

FEATURE_COLUMNS = [
    "rsi",
    "macd",
    "macd_signal",
    "macd_hist",
    "bb_pct",
    "volume_sma_ratio",
    "return_5d",
    "return_20d",
    "sma_ratio",
]


class SignalLearner:
    """Train a classifier on historical patterns; predict next-day direction."""

    def __init__(self, model_dir: Path):
        self.model_dir = Path(model_dir)
        self.model_dir.mkdir(parents=True, exist_ok=True)

    def _prepare(self, df: pd.DataFrame) -> tuple[pd.DataFrame, pd.Series]:
        enriched = add_indicators(df)
        features = enriched[FEATURE_COLUMNS].replace([np.inf, -np.inf], np.nan)
        labels = enriched["target_up"]
        mask = features.notna().all(axis=1) & labels.notna()
        return features[mask], labels[mask].astype(int)

    def train(self, symbol: str, df: pd.DataFrame) -> dict:
        x, y = self._prepare(df)
        if len(x) < 80:
            raise ValueError(f"Insufficient data to train {symbol}: {len(x)} rows")

        x_train, x_test, y_train, y_test = train_test_split(
            x, y, test_size=0.2, shuffle=False
        )
        model = GradientBoostingClassifier(
            n_estimators=120,
            max_depth=4,
            learning_rate=0.05,
            random_state=42,
        )
        model.fit(x_train, y_train)
        acc = accuracy_score(y_test, model.predict(x_test)) if len(x_test) else 0.0

        model_path = self.model_dir / f"{symbol.replace('.', '_')}.joblib"
        meta_path = self.model_dir / f"{symbol.replace('.', '_')}.json"
        joblib.dump(model, model_path)
        meta = {
            "symbol": symbol,
            "trained_at": datetime.now(timezone.utc).isoformat(),
            "samples": int(len(x)),
            "test_accuracy": round(float(acc), 4),
            "features": FEATURE_COLUMNS,
        }
        meta_path.write_text(json.dumps(meta, indent=2), encoding="utf-8")
        return meta

    def predict(self, symbol: str, df: pd.DataFrame) -> tuple[str, float]:
        model_path = self.model_dir / f"{symbol.replace('.', '_')}.joblib"
        if not model_path.exists():
            raise FileNotFoundError(f"No trained model for {symbol}. Run train first.")

        model = joblib.load(model_path)
        enriched = add_indicators(df)
        latest = enriched[FEATURE_COLUMNS].iloc[-1:]
        if latest.isna().any().any():
            return "hold", 0.5

        proba = model.predict_proba(latest)[0]
        up_prob = float(proba[1])
        if up_prob >= 0.55:
            return "buy", up_prob
        if up_prob <= 0.45:
            return "sell", 1.0 - up_prob
        return "hold", max(up_prob, 1.0 - up_prob)
