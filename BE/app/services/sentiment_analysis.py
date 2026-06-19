"""
Sentiment analysis service.

Aggregates sentiment scores from news sources and market indicators.
"""

from typing import Any


class SentimentAnalysisService:
    """Analyses market sentiment from news articles and other signals."""

    def __init__(self) -> None:
        from app.data_sources.news_api import NewsAPIConnector

        self.news_client = NewsAPIConnector()

    async def analyze_news(
        self,
        symbol: str,
        max_articles: int = 20,
    ) -> list[dict[str, Any]]:
        """
        Fetch recent news for *symbol* and compute per-article sentiment.

        Returns a list of dicts with headline, source, date, and sentiment score.
        """
        try:
            articles = await self.news_client.search_news(query=symbol, max_results=max_articles)
        except Exception:
            articles = []

        results: list[dict[str, Any]] = []
        for article in articles:
            # Simplified sentiment heuristic — replace with NLP model
            headline = article.get("title", "")
            score = self._simple_sentiment(headline)
            results.append(
                {
                    "headline": headline,
                    "source": article.get("source", ""),
                    "published_at": article.get("published_at", ""),
                    "sentiment_score": score,
                    "sentiment_label": self._score_to_label(score),
                }
            )
        return results

    async def get_market_sentiment(self, symbol: str) -> dict[str, Any]:
        """
        Return an overall market sentiment summary for *symbol*.
        """
        articles = await self.analyze_news(symbol)
        if not articles:
            return {
                "symbol": symbol.upper(),
                "overall_score": 0.0,
                "label": "neutral",
                "article_count": 0,
            }

        avg_score = sum(a["sentiment_score"] for a in articles) / len(articles)
        return {
            "symbol": symbol.upper(),
            "overall_score": round(avg_score, 3),
            "label": self._score_to_label(avg_score),
            "article_count": len(articles),
        }

    async def aggregate_sentiment(
        self,
        symbols: list[str],
    ) -> dict[str, dict[str, Any]]:
        """
        Aggregate sentiment across multiple symbols.

        Returns a dict keyed by symbol with sentiment summaries.
        """
        results: dict[str, dict[str, Any]] = {}
        for symbol in symbols:
            results[symbol.upper()] = await self.get_market_sentiment(symbol)
        return results

    # ── Private helpers ─────────────────────────────────────────────────
    @staticmethod
    def _simple_sentiment(text: str) -> float:
        """Naïve keyword-based sentiment scorer (–1 to +1)."""
        positive_words = {
            "surge", "gain", "rally", "rise", "bull", "up", "profit",
            "growth", "record", "beat", "high", "strong", "boost",
        }
        negative_words = {
            "crash", "drop", "fall", "bear", "down", "loss", "decline",
            "low", "weak", "miss", "cut", "fear", "risk", "sell",
        }
        words = text.lower().split()
        pos = sum(1 for w in words if w in positive_words)
        neg = sum(1 for w in words if w in negative_words)
        total = pos + neg
        if total == 0:
            return 0.0
        return round((pos - neg) / total, 3)

    @staticmethod
    def _score_to_label(score: float) -> str:
        if score > 0.2:
            return "positive"
        elif score < -0.2:
            return "negative"
        return "neutral"
