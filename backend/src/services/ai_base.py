from abc import ABC, abstractmethod
from typing import List
from src.schemas.ai import SentimentAnalysisResult, TopicClassification, TicketAnalysisResult


class SentimentAnalyzer(ABC):
    """Abstract base class for sentiment analysis."""

    @abstractmethod
    async def analyze_sentiment(self, ticket_content: str) -> SentimentAnalysisResult:
        """Analyze sentiment of ticket content."""
        pass


class TopicClassifier(ABC):
    """Abstract base class for topic classification."""

    @abstractmethod
    async def classify_topics(
        self,
        ticket_content: str,
        available_topics: List[str],
        training_rules: List[str] | None = None
    ) -> List[TopicClassification]:
        """Classify ticket into topics."""
        pass


class TicketAnalyzer(ABC):
    """Abstract base class for combined ticket analysis."""

    @abstractmethod
    async def analyze_ticket(
        self,
        ticket_content: str,
        available_topics: List[str] | None = None,
        training_rules: List[str] | None = None
    ) -> TicketAnalysisResult:
        """Analyze ticket for both sentiment and topics."""
        pass
