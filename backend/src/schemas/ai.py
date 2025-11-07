from pydantic import BaseModel, Field
from typing import List
from src.models.ticket import SentimentScore


class TopicClassification(BaseModel):
    """Topic classification result."""
    topic_name: str
    confidence: float = Field(..., ge=0.0, le=1.0)


class SentimentAnalysisResult(BaseModel):
    """Sentiment analysis result."""
    sentiment: SentimentScore
    confidence: float = Field(..., ge=0.0, le=1.0)
    reasoning: str | None = None


class TicketAnalysisResult(BaseModel):
    """Combined ticket analysis result."""
    sentiment: SentimentAnalysisResult
    topics: List[TopicClassification]
