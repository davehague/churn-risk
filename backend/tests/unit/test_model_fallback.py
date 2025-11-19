"""
Tests for model selection fallback behavior in OpenRouterAnalyzer.
"""

import pytest
from unittest.mock import patch, AsyncMock, MagicMock
from src.services.openrouter import OpenRouterAnalyzer
from src.core.config import settings


@pytest.mark.asyncio
async def test_model_fallback_uses_env_var():
    """Test that model falls back to OPENROUTER_MODEL from .env when not in prompt."""
    analyzer = OpenRouterAnalyzer(api_key="test-key")

    mock_response_data = {
        "choices": [{
            "message": {
                "content": """{
                    "sentiment": {
                        "score": "neutral",
                        "confidence": 0.5,
                        "reasoning": "Test"
                    },
                    "topics": [
                        {"name": "Test", "confidence": 0.5}
                    ]
                }"""
            }
        }]
    }

    mock_response = MagicMock()
    mock_response.json.return_value = mock_response_data
    mock_response.raise_for_status = MagicMock()

    with patch("httpx.AsyncClient.post", new_callable=AsyncMock) as mock_post:
        mock_post.return_value = mock_response

        await analyzer.analyze_ticket(
            ticket_content="Test ticket"
        )

        # Verify the call was made
        assert mock_post.called

        # Get the actual call and verify the model parameter
        call_kwargs = mock_post.call_args.kwargs
        model_used = call_kwargs['json']['model']

        # Should use the env var default (since prompts don't specify model anymore)
        assert model_used == settings.OPENROUTER_MODEL


@pytest.mark.asyncio
async def test_explicit_model_overrides_everything():
    """Test that explicit model passed to constructor overrides all defaults."""
    custom_model = "gpt-4o"
    analyzer = OpenRouterAnalyzer(api_key="test-key", model=custom_model)

    mock_response_data = {
        "choices": [{
            "message": {
                "content": """{
                    "sentiment": {
                        "score": "neutral",
                        "confidence": 0.5,
                        "reasoning": "Test"
                    },
                    "topics": [
                        {"name": "Test", "confidence": 0.5}
                    ]
                }"""
            }
        }]
    }

    mock_response = MagicMock()
    mock_response.json.return_value = mock_response_data
    mock_response.raise_for_status = MagicMock()

    with patch("httpx.AsyncClient.post", new_callable=AsyncMock) as mock_post:
        mock_post.return_value = mock_response

        await analyzer.analyze_ticket(
            ticket_content="Test ticket"
        )

        # Verify the explicit model was used
        call_kwargs = mock_post.call_args.kwargs
        model_used = call_kwargs['json']['model']

        assert model_used == custom_model


@pytest.mark.asyncio
async def test_model_priority_order():
    """Test the model selection priority: constructor > prompt metadata > env var."""
    # Case 1: No explicit model, should use env var default
    analyzer1 = OpenRouterAnalyzer(api_key="test-key")
    assert analyzer1.model == settings.OPENROUTER_MODEL

    # Case 2: Explicit model should be stored
    custom_model = "claude-3-opus"
    analyzer2 = OpenRouterAnalyzer(api_key="test-key", model=custom_model)
    assert analyzer2.model == custom_model
