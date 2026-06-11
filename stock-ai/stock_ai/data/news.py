from __future__ import annotations

import re
from dataclasses import dataclass

import feedparser
import requests


POSITIVE_WORDS = {
    "surge", "rally", "gain", "rise", "bull", "growth", "profit", "beat",
    "strong", "upgrade", "record", "boom", "上涨", "利好", "突破", "增长",
}
NEGATIVE_WORDS = {
    "fall", "drop", "decline", "crash", "bear", "loss", "miss", "weak",
    "downgrade", "recession", "slump", "plunge", "下跌", "利空", "暴跌", "亏损",
}


@dataclass
class NewsSentiment:
    score: float  # -1.0 .. 1.0
    headline_count: int
    sample_headlines: list[str]


class NewsAnalyzer:
    """Simple lexicon-based sentiment from public RSS feeds."""

    def __init__(self, rss_feeds: list[str], timeout: int = 15):
        self.rss_feeds = rss_feeds
        self.timeout = timeout

    def _fetch_headlines(self) -> list[str]:
        headlines: list[str] = []
        for url in self.rss_feeds:
            try:
                resp = requests.get(url, timeout=self.timeout)
                if resp.status_code == 429:
                    continue
                resp.raise_for_status()
                feed = feedparser.parse(resp.content)
                for entry in feed.entries[:20]:
                    title = getattr(entry, "title", "")
                    if title:
                        headlines.append(title)
            except (requests.RequestException, OSError):
                continue
        if not headlines:
            headlines.extend(self._fetch_ashare_headlines())
        return headlines

    def _fetch_ashare_headlines(self) -> list[str]:
        """Fallback: akshare/em headlines when RSS rate-limited."""
        try:
            import akshare as ak
            df = ak.stock_news_em(symbol="600519")
            if df is not None and not df.empty and "新闻标题" in df.columns:
                return [str(t) for t in df["新闻标题"].head(15).tolist()]
        except (ImportError, ValueError, OSError, KeyError):
            pass
        return []

    @staticmethod
    def _score_text(text: str) -> float:
        tokens = set(re.findall(r"[a-zA-Z\u4e00-\u9fff]+", text.lower()))
        pos = sum(1 for w in POSITIVE_WORDS if w in tokens or w in text.lower())
        neg = sum(1 for w in NEGATIVE_WORDS if w in tokens or w in text.lower())
        total = pos + neg
        if total == 0:
            return 0.0
        return (pos - neg) / total

    def analyze(self) -> NewsSentiment:
        headlines = self._fetch_headlines()
        if not headlines:
            return NewsSentiment(score=0.0, headline_count=0, sample_headlines=[])
        scores = [self._score_text(h) for h in headlines]
        avg = sum(scores) / len(scores)
        return NewsSentiment(
            score=max(-1.0, min(1.0, avg)),
            headline_count=len(headlines),
            sample_headlines=headlines[:5],
        )
