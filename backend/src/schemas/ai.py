from pydantic import BaseModel, Field, ConfigDict
from typing import List
from src.models.ticket import SentimentScore


class TopicClassification(BaseModel):
    """Topic classification result."""
    model_config = ConfigDict(from_attributes=True)

    topic_name: str
    confidence: float = Field(..., ge=0.0, le=1.0)


class SentimentAnalysisResult(BaseModel):
    """Sentiment analysis result."""
    model_config = ConfigDict(from_attributes=True)

    sentiment: SentimentScore
    confidence: float = Field(..., ge=0.0, le=1.0)
    reasoning: str | None = None


class TicketAnalysisResult(BaseModel):
    """Combined ticket analysis result."""
    model_config = ConfigDict(from_attributes=True)

    sentiment: SentimentAnalysisResult
    topics: List[TopicClassification]
