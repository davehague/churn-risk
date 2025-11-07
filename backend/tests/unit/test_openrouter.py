import pytest
from unittest.mock import patch, AsyncMock, MagicMock
from src.services.openrouter import OpenRouterAnalyzer
from src.models.ticket import SentimentScore


@pytest.mark.asyncio
async def test_analyze_ticket_with_topics():
    """Test analyzing a ticket with available topics."""
    analyzer = OpenRouterAnalyzer(api_key="test-key")

    mock_response_data = {
        "choices": [{
            "message": {
                "content": """{
                    "sentiment": {
                        "score": "negative",
                        "confidence": 0.85,
                        "reasoning": "Customer is frustrated with API errors"
                    },
                    "topics": [
                        {"name": "API Errors", "confidence": 0.9},
                        {"name": "Integration Help", "confidence": 0.6}
                    ]
                }"""
            }
        }]
    }

    # Create a mock response object
    mock_response = MagicMock()
    mock_response.json.return_value = mock_response_data
    mock_response.raise_for_status = MagicMock()

    with patch("httpx.AsyncClient.post", new_callable=AsyncMock) as mock_post:
        mock_post.return_value = mock_response

        result = await analyzer.analyze_ticket(
            ticket_content="The API keeps returning 500 errors!",
            available_topics=["API Errors", "Integration Help", "Performance Issues"]
        )

        assert result.sentiment.sentiment == SentimentScore.NEGATIVE
        assert result.sentiment.confidence == 0.85
        assert len(result.topics) == 2
        assert result.topics[0].topic_name == "API Errors"
        assert result.topics[0].confidence == 0.9


@pytest.mark.asyncio
async def test_analyze_ticket_without_topics():
    """Test analyzing a ticket without predefined topics."""
    analyzer = OpenRouterAnalyzer(api_key="test-key")

    mock_response_data = {
        "choices": [{
            "message": {
                "content": """{
                    "sentiment": {
                        "score": "positive",
                        "confidence": 0.95,
                        "reasoning": "Customer is very happy with the support"
                    },
                    "topics": [
                        {"name": "Support Quality", "confidence": 0.9}
                    ]
                }"""
            }
        }]
    }

    # Create a mock response object
    mock_response = MagicMock()
    mock_response.json.return_value = mock_response_data
    mock_response.raise_for_status = MagicMock()

    with patch("httpx.AsyncClient.post", new_callable=AsyncMock) as mock_post:
        mock_post.return_value = mock_response

        result = await analyzer.analyze_ticket(
            ticket_content="Thank you for the excellent support!",
            available_topics=None
        )

        assert result.sentiment.sentiment == SentimentScore.POSITIVE
        assert result.sentiment.confidence == 0.95
        assert len(result.topics) == 1
        assert result.topics[0].topic_name == "Support Quality"
