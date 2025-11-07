import pytest
from unittest.mock import patch, AsyncMock, MagicMock
from src.integrations.hubspot import HubSpotClient


@pytest.mark.asyncio
async def test_exchange_code_for_token():
    """Test exchanging OAuth code for access token."""
    mock_response = {
        "access_token": "test-access-token",
        "refresh_token": "test-refresh-token",
        "expires_in": 21600
    }

    mock_resp = MagicMock()
    mock_resp.json = MagicMock(return_value=mock_response)
    mock_resp.raise_for_status = MagicMock()

    with patch("httpx.AsyncClient") as mock_client:
        mock_client.return_value.__aenter__.return_value.post = AsyncMock(return_value=mock_resp)

        result = await HubSpotClient.exchange_code_for_token(
            code="test-code",
            redirect_uri="http://localhost:8000/callback"
        )

        assert result["access_token"] == "test-access-token"
        assert result["refresh_token"] == "test-refresh-token"
        assert result["expires_in"] == 21600


@pytest.mark.asyncio
async def test_refresh_access_token():
    """Test refreshing an access token."""
    mock_response = {
        "access_token": "new-access-token",
        "refresh_token": "new-refresh-token",
        "expires_in": 21600
    }

    mock_resp = MagicMock()
    mock_resp.json = MagicMock(return_value=mock_response)
    mock_resp.raise_for_status = MagicMock()

    with patch("httpx.AsyncClient") as mock_client:
        mock_client.return_value.__aenter__.return_value.post = AsyncMock(return_value=mock_resp)

        result = await HubSpotClient.refresh_access_token(
            refresh_token="old-refresh-token"
        )

        assert result["access_token"] == "new-access-token"
        assert result["refresh_token"] == "new-refresh-token"


@pytest.mark.asyncio
async def test_get_tickets():
    """Test fetching tickets from HubSpot."""
    client = HubSpotClient(access_token="test-token")

    mock_response = {
        "results": [
            {
                "id": "123",
                "properties": {
                    "subject": "Test ticket",
                    "content": "This is a test",
                    "hs_ticket_id": "123"
                }
            },
            {
                "id": "456",
                "properties": {
                    "subject": "Another ticket",
                    "content": "This is another test",
                    "hs_ticket_id": "456"
                }
            }
        ],
        "paging": {
            "next": {
                "after": "789"
            }
        }
    }

    mock_resp = MagicMock()
    mock_resp.json = MagicMock(return_value=mock_response)
    mock_resp.raise_for_status = MagicMock()

    with patch("httpx.AsyncClient") as mock_client:
        mock_client.return_value.__aenter__.return_value.get = AsyncMock(return_value=mock_resp)

        result = await client.get_tickets(limit=10)

        assert len(result["results"]) == 2
        assert result["results"][0]["id"] == "123"
        assert result["results"][0]["properties"]["subject"] == "Test ticket"
        assert result["results"][1]["id"] == "456"


@pytest.mark.asyncio
async def test_get_ticket():
    """Test fetching a single ticket by ID."""
    client = HubSpotClient(access_token="test-token")

    mock_response = {
        "id": "123",
        "properties": {
            "subject": "Test ticket",
            "content": "This is a test",
            "hs_ticket_id": "123"
        }
    }

    mock_resp = MagicMock()
    mock_resp.json = MagicMock(return_value=mock_response)
    mock_resp.raise_for_status = MagicMock()

    with patch("httpx.AsyncClient") as mock_client:
        mock_client.return_value.__aenter__.return_value.get = AsyncMock(return_value=mock_resp)

        result = await client.get_ticket(ticket_id="123")

        assert result["id"] == "123"
        assert result["properties"]["subject"] == "Test ticket"


@pytest.mark.asyncio
async def test_get_companies():
    """Test fetching companies from HubSpot."""
    client = HubSpotClient(access_token="test-token")

    mock_response = {
        "results": [
            {
                "id": "123",
                "properties": {
                    "name": "Acme Corp",
                    "domain": "acme.com"
                }
            },
            {
                "id": "456",
                "properties": {
                    "name": "Widget Inc",
                    "domain": "widget.com"
                }
            }
        ],
        "paging": {}
    }

    mock_resp = MagicMock()
    mock_resp.json = MagicMock(return_value=mock_response)
    mock_resp.raise_for_status = MagicMock()

    with patch("httpx.AsyncClient") as mock_client:
        mock_client.return_value.__aenter__.return_value.get = AsyncMock(return_value=mock_resp)

        result = await client.get_companies(limit=50)

        assert len(result["results"]) == 2
        assert result["results"][0]["properties"]["name"] == "Acme Corp"
        assert result["results"][1]["properties"]["name"] == "Widget Inc"


@pytest.mark.asyncio
async def test_get_contacts():
    """Test fetching contacts from HubSpot."""
    client = HubSpotClient(access_token="test-token")

    mock_response = {
        "results": [
            {
                "id": "123",
                "properties": {
                    "email": "john@acme.com",
                    "firstname": "John",
                    "lastname": "Doe"
                }
            },
            {
                "id": "456",
                "properties": {
                    "email": "jane@widget.com",
                    "firstname": "Jane",
                    "lastname": "Smith"
                }
            }
        ],
        "paging": {}
    }

    mock_resp = MagicMock()
    mock_resp.json = MagicMock(return_value=mock_response)
    mock_resp.raise_for_status = MagicMock()

    with patch("httpx.AsyncClient") as mock_client:
        mock_client.return_value.__aenter__.return_value.get = AsyncMock(return_value=mock_resp)

        result = await client.get_contacts(limit=50)

        assert len(result["results"]) == 2
        assert result["results"][0]["properties"]["email"] == "john@acme.com"
        assert result["results"][1]["properties"]["email"] == "jane@widget.com"


@pytest.mark.asyncio
async def test_create_webhook_subscription():
    """Test creating a webhook subscription."""
    client = HubSpotClient(access_token="test-token")

    mock_response = {
        "id": "sub-123",
        "enabled": True,
        "subscriptionType": "ticket.creation",
        "webhookUrl": "https://example.com/webhook"
    }

    mock_resp = MagicMock()
    mock_resp.json = MagicMock(return_value=mock_response)
    mock_resp.raise_for_status = MagicMock()

    with patch("httpx.AsyncClient") as mock_client:
        mock_client.return_value.__aenter__.return_value.post = AsyncMock(return_value=mock_resp)

        result = await client.create_webhook_subscription(
            webhook_url="https://example.com/webhook",
            subscription_type="ticket.creation"
        )

        assert result["id"] == "sub-123"
        assert result["enabled"] is True
        assert result["subscriptionType"] == "ticket.creation"


@pytest.mark.asyncio
async def test_get_tickets_with_pagination():
    """Test fetching tickets with pagination cursor."""
    client = HubSpotClient(access_token="test-token")

    mock_response = {
        "results": [
            {
                "id": "789",
                "properties": {
                    "subject": "Paginated ticket",
                    "content": "This is paginated"
                }
            }
        ],
        "paging": {}
    }

    mock_resp = MagicMock()
    mock_resp.json = MagicMock(return_value=mock_response)
    mock_resp.raise_for_status = MagicMock()

    with patch("httpx.AsyncClient") as mock_client:
        mock_client.return_value.__aenter__.return_value.get = AsyncMock(return_value=mock_resp)

        result = await client.get_tickets(limit=10, after="previous-cursor")

        assert len(result["results"]) == 1
        assert result["results"][0]["id"] == "789"
