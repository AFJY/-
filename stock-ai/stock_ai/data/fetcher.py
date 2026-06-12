from __future__ import annotations

from datetime import datetime, timedelta

import pandas as pd
import yfinance as yf


class MarketDataFetcher:
    """Fetch OHLCV market data via yfinance (free, public)."""

    def fetch_history(
        self,
        symbol: str,
        days: int = 365,
        interval: str = "1d",
    ) -> pd.DataFrame:
        end = datetime.utcnow()
        start = end - timedelta(days=days + 30)
        ticker = yf.Ticker(symbol)
        df = ticker.history(start=start, end=end, interval=interval, auto_adjust=True)
        if df.empty:
            raise ValueError(f"No market data for {symbol}")
        df = df.rename(columns=str.lower)
        df.index = pd.to_datetime(df.index).tz_localize(None)
        return df.sort_index()

    def fetch_latest_price(self, symbol: str) -> float:
        df = self.fetch_history(symbol, days=5)
        return float(df["close"].iloc[-1])

    def fetch_multiple(
        self, symbols: list[str], days: int = 365
    ) -> dict[str, pd.DataFrame]:
        result: dict[str, pd.DataFrame] = {}
        for sym in symbols:
            try:
                result[sym] = self.fetch_history(sym, days=days)
            except ValueError:
                continue
        return result
