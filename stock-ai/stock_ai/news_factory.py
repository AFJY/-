from __future__ import annotations

from stock_ai.data.llm_news import DeepSeekNewsAnalyzer
from stock_ai.data.news import NewsAnalyzer


def build_news_analyzer(news_cfg: dict) -> NewsAnalyzer | None:
    if not news_cfg.get("enabled", True):
        return None
    feeds = news_cfg.get("rss_feeds", [])
    if news_cfg.get("llm_enabled", False):
        return DeepSeekNewsAnalyzer(
            feeds,
            model=news_cfg.get("llm_model", "deepseek-chat"),
        )
    return NewsAnalyzer(feeds)
