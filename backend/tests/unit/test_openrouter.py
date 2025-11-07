import pytest
import httpx
from unittest.mock import patch, AsyncMock, MagicMock
from tenacity import RetryError
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


@pytest.mark.asyncio
async def test_analyze_ticket_http_error():
    """Test handling of HTTP errors with retry logic."""
    analyzer = OpenRouterAnalyzer(api_key="test-key")

    with patch("httpx.AsyncClient.post", new_callable=AsyncMock) as mock_post:
        # Simulate HTTP error that will be retried 3 times
        mock_post.side_effect = httpx.HTTPError("Connection failed")

        with pytest.raises(RetryError):
            await analyzer.analyze_ticket(
                ticket_content="Test ticket",
                available_topics=["API Errors"]
            )

        # Verify retry logic attempted 3 times
        assert mock_post.call_count == 3


@pytest.mark.asyncio
async def test_analyze_ticket_malformed_json():
    """Test handling of malformed JSON response."""
    analyzer = OpenRouterAnalyzer(api_key="test-key")

    mock_response_data = {
        "choices": [{
            "message": {
                "content": "This is not valid JSON{{{}"
            }
        }]
    }

    mock_response = MagicMock()
    mock_response.json.return_value = mock_response_data
    mock_response.raise_for_status = MagicMock()

    with patch("httpx.AsyncClient.post", new_callable=AsyncMock) as mock_post:
        mock_post.return_value = mock_response

        with pytest.raises(RetryError) as exc_info:
            await analyzer.analyze_ticket(
                ticket_content="Test ticket",
                available_topics=["API Errors"]
            )

        # Verify the underlying exception is ValueError with the correct message
        assert exc_info.value.last_attempt.exception() is not None
        assert isinstance(exc_info.value.last_attempt.exception(), ValueError)
        assert "Failed to parse LLM response as JSON" in str(exc_info.value.last_attempt.exception())
