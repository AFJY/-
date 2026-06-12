from __future__ import annotations

import os
import re
from pathlib import Path

import requests

from stock_ai.data.news import NewsAnalyzer, NewsSentiment


def _load_deepseek_key() -> str | None:
    key = os.environ.get("DEEPSEEK_API_KEY")
    if key:
        return key
    hermes_env = Path.home() / ".hermes" / ".env"
    if hermes_env.exists():
        for line in hermes_env.read_text(encoding="utf-8").splitlines():
            if line.startswith("DEEPSEEK_API_KEY="):
                return line.split("=", 1)[1].strip().strip("'\"")
    return None


class DeepSeekNewsAnalyzer(NewsAnalyzer):
    """RSS headlines + DeepSeek sentiment (falls back to lexicon)."""

    def __init__(
        self,
        rss_feeds: list[str],
        timeout: int = 15,
        model: str = "deepseek-chat",
    ):
        super().__init__(rss_feeds, timeout)
        self.api_key = _load_deepseek_key()
        self.model = model

    def _llm_score(self, headlines: list[str]) -> float | None:
        if not self.api_key or not headlines:
            return None
        sample = "\n".join(f"- {h}" for h in headlines[:15])
        prompt = (
            "你是财经新闻情绪分析师。根据以下新闻标题，评估对 A 股/大盘短期情绪影响。\n"
            "只回复一个 -1 到 1 之间的小数，负数看空，正数看多，0 中性。不要解释。\n\n"
            f"{sample}"
        )
        try:
            resp = requests.post(
                "https://api.deepseek.com/chat/completions",
                headers={
                    "Authorization": f"Bearer {self.api_key}",
                    "Content-Type": "application/json",
                },
                json={
                    "model": self.model,
                    "messages": [{"role": "user", "content": prompt}],
                    "temperature": 0.1,
                    "max_tokens": 16,
                },
                timeout=self.timeout,
            )
            resp.raise_for_status()
            text = resp.json()["choices"][0]["message"]["content"].strip()
            m = re.search(r"-?\d+\.?\d*", text)
            if m:
                return max(-1.0, min(1.0, float(m.group())))
        except (requests.RequestException, OSError, KeyError, ValueError):
            pass
        return None

    def analyze(self) -> NewsSentiment:
        headlines = self._fetch_headlines()
        if not headlines:
            return NewsSentiment(score=0.0, headline_count=0, sample_headlines=[])

        llm = self._llm_score(headlines)
        if llm is not None:
            return NewsSentiment(
                score=llm,
                headline_count=len(headlines),
                sample_headlines=headlines[:5],
            )
        return super().analyze()
