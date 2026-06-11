from __future__ import annotations

import re
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any

import pandas as pd
import yfinance as yf

try:
    import akshare as ak
except ImportError:
    ak = None  # type: ignore


@dataclass
class RealtimeQuote:
    symbol: str
    name: str
    price: float
    change_pct: float
    volume: float
    timestamp: str
    source: str  # akshare | yfinance | ths_bridge


@dataclass
class QuoteStore:
    """Thread-safe-ish in-memory quote cache with THS bridge overlay."""

    quotes: dict[str, RealtimeQuote] = field(default_factory=dict)
    ths_connected: bool = False
    ths_last_seen: str | None = None

    def update(self, quote: RealtimeQuote) -> None:
        self.quotes[quote.symbol] = quote
        if quote.source == "ths_bridge":
            self.ths_connected = True
            self.ths_last_seen = quote.timestamp

    def get(self, symbol: str) -> RealtimeQuote | None:
        return self.quotes.get(symbol)

    def all_quotes(self) -> list[RealtimeQuote]:
        return list(self.quotes.values())


def is_a_share(symbol: str) -> bool:
    s = symbol.upper()
    return s.endswith(".SS") or s.endswith(".SZ") or re.fullmatch(r"\d{6}", symbol) is not None


def to_ak_code(symbol: str) -> str:
    """Convert yfinance-style or plain code to akshare symbol."""
    s = symbol.upper()
    if re.fullmatch(r"\d{6}", s):
        return s
    if s.endswith(".SS"):
        return s.split(".")[0]
    if s.endswith(".SZ"):
        return s.split(".")[0]
    return symbol


class RealtimeDataFetcher:
    """Fetch near-real-time quotes from akshare (A-share) or yfinance (US)."""

    def fetch_quote(self, symbol: str) -> RealtimeQuote:
        if is_a_share(symbol):
            try:
                return self._fetch_ashare(symbol)
            except (ValueError, OSError, ImportError, KeyError):
                return self._fetch_yfinance(symbol)
        return self._fetch_yfinance(symbol)

    def fetch_quotes(self, symbols: list[str]) -> list[RealtimeQuote]:
        results: list[RealtimeQuote] = []
        for sym in symbols:
            try:
                results.append(self.fetch_quote(sym))
            except (ValueError, OSError, KeyError):
                continue
        return results

    def _fetch_ashare(self, symbol: str) -> RealtimeQuote:
        if ak is None:
            raise ImportError("akshare not installed — pip install akshare")
        code = to_ak_code(symbol)
        # Lightweight single-symbol bid/ask (faster than full-market spot table)
        try:
            df = ak.stock_bid_ask_em(symbol=code)
            price_row = df[df["item"] == "最新"]
            if not price_row.empty:
                price = float(price_row.iloc[0]["value"])
                chg_row = df[df["item"] == "涨幅"]
                chg = float(chg_row.iloc[0]["value"]) if not chg_row.empty else 0.0
                return RealtimeQuote(
                    symbol=symbol,
                    name=code,
                    price=price,
                    change_pct=chg,
                    volume=0.0,
                    timestamp=datetime.now(timezone.utc).isoformat(),
                    source="akshare",
                )
        except (ValueError, OSError, KeyError, TypeError):
            pass
        raise ValueError(f"akshare quote unavailable for {symbol}")

    def _fetch_yfinance(self, symbol: str) -> RealtimeQuote:
        ticker = yf.Ticker(symbol)
        info = ticker.fast_info
        price = float(getattr(info, "last_price", 0) or 0)
        if not price:
            hist = ticker.history(period="1d", interval="1m")
            if hist.empty:
                raise ValueError(f"No US quote for {symbol}")
            price = float(hist["Close"].iloc[-1])
        prev = float(getattr(info, "previous_close", price) or price)
        chg = ((price - prev) / prev * 100.0) if prev else 0.0
        return RealtimeQuote(
            symbol=symbol,
            name=symbol,
            price=price,
            change_pct=chg,
            volume=0.0,
            timestamp=datetime.now(timezone.utc).isoformat(),
            source="yfinance",
        )

    def fetch_intraday_bars(self, symbol: str, period: str = "1d", interval: str = "1m") -> pd.DataFrame:
        if is_a_share(symbol) and ak is not None:
            code = to_ak_code(symbol)
            df = ak.stock_zh_a_hist_min_em(symbol=code, period="1")
            df = df.rename(columns={
                "时间": "datetime",
                "开盘": "open",
                "收盘": "close",
                "最高": "high",
                "最低": "low",
                "成交量": "volume",
            })
            df["datetime"] = pd.to_datetime(df["datetime"])
            return df.set_index("datetime").sort_index()
        ticker = yf.Ticker(symbol)
        df = ticker.history(period=period, interval=interval)
        if df.empty:
            raise ValueError(f"No intraday data for {symbol}")
        df = df.rename(columns=str.lower)
        return df.sort_index()
