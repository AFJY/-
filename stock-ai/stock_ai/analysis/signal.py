from __future__ import annotations

from dataclasses import dataclass

import pandas as pd

from stock_ai.analysis.learner import SignalLearner
from stock_ai.data.news import NewsAnalyzer, NewsSentiment


@dataclass
class TradeSignal:
    symbol: str
    action: str  # buy | sell | hold
    confidence: float
    ml_action: str
    ml_confidence: float
    news_score: float
    reason: str


class SignalAggregator:
    """Combine ML technical signal with public news sentiment."""

    def __init__(
        self,
        learner: SignalLearner,
        news_analyzer: NewsAnalyzer | None,
        sentiment_weight: float = 0.15,
        min_confidence: float = 0.55,
    ):
        self.learner = learner
        self.news_analyzer = news_analyzer
        self.sentiment_weight = sentiment_weight
        self.min_confidence = min_confidence

    def generate(self, symbol: str, df: pd.DataFrame, news: NewsSentiment | None = None) -> TradeSignal:
        ml_action, ml_conf = self.learner.predict(symbol, df)
        news_score = 0.0
        if self.news_analyzer:
            news = news or self.news_analyzer.analyze()
            news_score = news.score

        # Adjust confidence: bullish news nudges buy, bearish nudges sell
        adjusted_conf = ml_conf
        action = ml_action
        if ml_action == "buy" and news_score > 0.1:
            adjusted_conf = min(1.0, ml_conf + self.sentiment_weight * news_score)
        elif ml_action == "sell" and news_score < -0.1:
            adjusted_conf = min(1.0, ml_conf + self.sentiment_weight * abs(news_score))
        elif ml_action == "buy" and news_score < -0.3:
            action = "hold"
            adjusted_conf = ml_conf * 0.8
        elif ml_action == "sell" and news_score > 0.3:
            action = "hold"
            adjusted_conf = ml_conf * 0.8

        if action != "hold" and adjusted_conf < self.min_confidence:
            action = "hold"

        reason = (
            f"ML={ml_action}({ml_conf:.2f}), news={news_score:+.2f}, "
            f"final={action}({adjusted_conf:.2f})"
        )
        return TradeSignal(
            symbol=symbol,
            action=action,
            confidence=adjusted_conf,
            ml_action=ml_action,
            ml_confidence=ml_conf,
            news_score=news_score,
            reason=reason,
        )
