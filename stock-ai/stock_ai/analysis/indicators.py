from __future__ import annotations

import pandas as pd
import ta


def add_indicators(df: pd.DataFrame) -> pd.DataFrame:
    """Add technical indicators used for ML features."""
    out = df.copy()
    close = out["close"]
    volume = out["volume"]

    out["rsi"] = ta.momentum.RSIIndicator(close, window=14).rsi()
    macd = ta.trend.MACD(close)
    out["macd"] = macd.macd()
    out["macd_signal"] = macd.macd_signal()
    out["macd_hist"] = macd.macd_diff()

    bb = ta.volatility.BollingerBands(close)
    out["bb_high"] = bb.bollinger_hband()
    out["bb_low"] = bb.bollinger_lband()
    out["bb_pct"] = (close - out["bb_low"]) / (out["bb_high"] - out["bb_low"])

    vol_sma = volume.rolling(20).mean()
    out["volume_sma_ratio"] = volume / vol_sma
    out["return_1d"] = close.pct_change()
    out["return_5d"] = close.pct_change(5)
    out["return_20d"] = close.pct_change(20)
    out["sma_20"] = close.rolling(20).mean()
    out["sma_50"] = close.rolling(50).mean()
    out["sma_ratio"] = out["sma_20"] / out["sma_50"]

    # Next-day direction label for supervised learning
    out["target_up"] = (out["return_1d"].shift(-1) > 0).astype(int)
    return out
