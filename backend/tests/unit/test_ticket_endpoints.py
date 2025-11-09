"""Unit tests for ticket API endpoints."""

import pytest
from datetime import datetime, timezone
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4
from fastapi import HTTPException
from fastapi.testclient import TestClient

from src.main import app
from src.models.user import User, UserRole
from src.models.tenant import Tenant
from src.models.ticket import Ticket, SentimentScore, TicketStatus
from src.models.company import Company
from src.models.contact import Contact
from src.services.ticket_import import ImportResult


@pytest.fixture
def mock_db():
    """Create a mock database session."""
    return MagicMock()


@pytest.fixture
def test_user():
    """Create a test user."""
    return User(
        id=uuid4(),
        tenant_id=uuid4(),
        firebase_uid="test-uid-123",
        email="test@example.com",
        name="Test User",
        role=UserRole.MEMBER
    )


@pytest.fixture
def test_ticket(test_user):
    """Create a test ticket."""
    return Ticket(
        id=uuid4(),
        tenant_id=test_user.tenant_id,
        external_id="12345",
        subject="Cannot login",
        content="I've been trying to login for the past hour",
        sentiment_score=SentimentScore.NEGATIVE,
        sentiment_confidence=0.87,
        sentiment_analyzed_at=datetime.now(timezone.utc),
        created_at=datetime.now(timezone.utc),
        status=TicketStatus.OPEN,
        external_url="https://app.hubspot.com/contacts/ticket/12345"
    )


@pytest.fixture
def test_company(test_user):
    """Create a test company."""
    return Company(
        id=uuid4(),
        tenant_id=test_user.tenant_id,
        external_id="comp-123",
        name="Acme Corp"
    )


@pytest.fixture
def test_contact(test_user, test_company):
    """Create a test contact."""
    return Contact(
        id=uuid4(),
        tenant_id=test_user.tenant_id,
        company_id=test_company.id,
        external_id="contact-123",
        name="John Doe",
        email="john@acme.com"
    )


@pytest.mark.asyncio
async def test_import_tickets_success(mock_db, test_user):
    """Test successful ticket import."""
    # Mock the import service
    mock_result = ImportResult(
        imported=15,
        analyzed=12,
        skipped=3,
        failed=0
    )

    with patch("src.api.routers.tickets.import_and_analyze_tickets", new_callable=AsyncMock) as mock_import:
        mock_import.return_value = mock_result

        # Import the endpoint function
        from src.api.routers.tickets import import_tickets

        # Call the endpoint
        result = await import_tickets(db=mock_db, current_user=test_user)

        # Verify
        assert result.imported == 15
        assert result.analyzed == 12
        assert result.skipped == 3
        assert result.failed == 0

        mock_import.assert_called_once_with(
            tenant_id=test_user.tenant_id,
            db=mock_db
        )


@pytest.mark.asyncio
async def test_import_tickets_no_integration(mock_db, test_user):
    """Test import tickets when HubSpot integration not found."""
    with patch("src.api.routers.tickets.import_and_analyze_tickets", new_callable=AsyncMock) as mock_import:
        mock_import.side_effect = ValueError("HubSpot integration not found")

        from src.api.routers.tickets import import_tickets

        with pytest.raises(HTTPException) as exc_info:
            await import_tickets(db=mock_db, current_user=test_user)

        assert exc_info.value.status_code == 404
        assert "HubSpot integration not found" in exc_info.value.detail


@pytest.mark.asyncio
async def test_import_tickets_inactive_integration(mock_db, test_user):
    """Test import tickets when HubSpot integration is inactive."""
    with patch("src.api.routers.tickets.import_and_analyze_tickets", new_callable=AsyncMock) as mock_import:
        mock_import.side_effect = ValueError("HubSpot integration is inactive")

        from src.api.routers.tickets import import_tickets

        with pytest.raises(HTTPException) as exc_info:
            await import_tickets(db=mock_db, current_user=test_user)

        assert exc_info.value.status_code == 401
        assert "not active" in exc_info.value.detail


@pytest.mark.asyncio
async def test_import_tickets_generic_error(mock_db, test_user):
    """Test import tickets with generic error."""
    with patch("src.api.routers.tickets.import_and_analyze_tickets", new_callable=AsyncMock) as mock_import:
        mock_import.side_effect = Exception("API timeout")

        from src.api.routers.tickets import import_tickets

        with pytest.raises(HTTPException) as exc_info:
            await import_tickets(db=mock_db, current_user=test_user)

        assert exc_info.value.status_code == 500
        assert "Failed to import tickets" in exc_info.value.detail


@pytest.mark.asyncio
async def test_list_tickets_all(mock_db, test_user, test_ticket):
    """Test listing all tickets."""
    # Setup mock query chain
    mock_query = MagicMock()
    mock_subquery = MagicMock()
    mock_count_result = MagicMock()
    mock_count_result.scalar_one.return_value = 1

    # Mock the select statement and where clause
    with patch("src.api.routers.tickets.select") as mock_select, \
         patch("src.api.routers.tickets.func") as mock_func:

        # Setup query result
        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = [test_ticket]

        mock_db.execute.side_effect = [mock_count_result, mock_result]

        from src.api.routers.tickets import list_tickets

        # Call endpoint
        result = await list_tickets(
            sentiment=None,
            limit=100,
            offset=0,
            db=mock_db,
            current_user=test_user
        )

        # Verify response
        assert result.total == 1
        assert len(result.tickets) == 1
        assert result.tickets[0].id == str(test_ticket.id)
        assert result.tickets[0].external_id == "12345"
        assert result.tickets[0].subject == "Cannot login"
        assert result.tickets[0].sentiment_score == SentimentScore.NEGATIVE


@pytest.mark.asyncio
async def test_list_tickets_with_sentiment_filter(mock_db, test_user, test_ticket):
    """Test listing tickets filtered by sentiment."""
    mock_count_result = MagicMock()
    mock_count_result.scalar_one.return_value = 1

    with patch("src.api.routers.tickets.select") as mock_select, \
         patch("src.api.routers.tickets.func") as mock_func:

        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = [test_ticket]

        mock_db.execute.side_effect = [mock_count_result, mock_result]

        from src.api.routers.tickets import list_tickets

        result = await list_tickets(
            sentiment=SentimentScore.NEGATIVE,
            limit=100,
            offset=0,
            db=mock_db,
            current_user=test_user
        )

        assert result.total == 1
        assert len(result.tickets) == 1
        assert result.tickets[0].sentiment_score == SentimentScore.NEGATIVE


@pytest.mark.asyncio
async def test_list_tickets_with_pagination(mock_db, test_user):
    """Test listing tickets with pagination."""
    mock_count_result = MagicMock()
    mock_count_result.scalar_one.return_value = 100

    with patch("src.api.routers.tickets.select") as mock_select, \
         patch("src.api.routers.tickets.func") as mock_func:

        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = []

        mock_db.execute.side_effect = [mock_count_result, mock_result]

        from src.api.routers.tickets import list_tickets

        result = await list_tickets(
            sentiment=None,
            limit=10,
            offset=20,
            db=mock_db,
            current_user=test_user
        )

        assert result.total == 100
        assert len(result.tickets) == 0


@pytest.mark.asyncio
async def test_list_tickets_with_company_and_contact(mock_db, test_user, test_ticket, test_company, test_contact):
    """Test listing tickets with company and contact information."""
    # Link company and contact to ticket
    test_ticket.company = test_company
    test_ticket.contact = test_contact

    mock_count_result = MagicMock()
    mock_count_result.scalar_one.return_value = 1

    with patch("src.api.routers.tickets.select") as mock_select, \
         patch("src.api.routers.tickets.func") as mock_func:

        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = [test_ticket]

        mock_db.execute.side_effect = [mock_count_result, mock_result]

        from src.api.routers.tickets import list_tickets

        result = await list_tickets(
            sentiment=None,
            limit=100,
            offset=0,
            db=mock_db,
            current_user=test_user
        )

        # Verify company and contact are included
        assert result.tickets[0].company is not None
        assert result.tickets[0].company.id == str(test_company.id)
        assert result.tickets[0].company.name == "Acme Corp"

        assert result.tickets[0].contact is not None
        assert result.tickets[0].contact.id == str(test_contact.id)
        assert result.tickets[0].contact.name == "John Doe"
        assert result.tickets[0].contact.email == "john@acme.com"


@pytest.mark.asyncio
async def test_list_tickets_empty_result(mock_db, test_user):
    """Test listing tickets when no tickets exist."""
    mock_count_result = MagicMock()
    mock_count_result.scalar_one.return_value = 0

    with patch("src.api.routers.tickets.select") as mock_select, \
         patch("src.api.routers.tickets.func") as mock_func:

        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = []

        mock_db.execute.side_effect = [mock_count_result, mock_result]

        from src.api.routers.tickets import list_tickets

        result = await list_tickets(
            sentiment=None,
            limit=100,
            offset=0,
            db=mock_db,
            current_user=test_user
        )

        assert result.total == 0
        assert len(result.tickets) == 0


@pytest.mark.asyncio
async def test_list_tickets_without_sentiment(mock_db, test_user):
    """Test listing tickets that haven't been analyzed yet."""
    ticket_without_sentiment = Ticket(
        id=uuid4(),
        tenant_id=test_user.tenant_id,
        external_id="99999",
        subject="New ticket",
        content="Just imported",
        sentiment_score=None,
        sentiment_confidence=None,
        sentiment_analyzed_at=None,
        created_at=datetime.now(timezone.utc),
        status=TicketStatus.NEW,
        external_url="https://app.hubspot.com/contacts/ticket/99999"
    )

    mock_count_result = MagicMock()
    mock_count_result.scalar_one.return_value = 1

    with patch("src.api.routers.tickets.select") as mock_select, \
         patch("src.api.routers.tickets.func") as mock_func:

        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = [ticket_without_sentiment]

        mock_db.execute.side_effect = [mock_count_result, mock_result]

        from src.api.routers.tickets import list_tickets

        result = await list_tickets(
            sentiment=None,
            limit=100,
            offset=0,
            db=mock_db,
            current_user=test_user
        )

        # Verify ticket is returned with None sentiment fields
        assert result.total == 1
        assert len(result.tickets) == 1
        assert result.tickets[0].sentiment_score is None
        assert result.tickets[0].sentiment_confidence is None
        assert result.tickets[0].sentiment_analyzed_at is None


@pytest.mark.asyncio
async def test_list_tickets_limit_validation(mock_db, test_user):
    """Test that limit parameter is validated correctly."""
    from src.api.routers.tickets import list_tickets

    # Test with valid limits
    valid_limits = [1, 100, 500]
    for limit in valid_limits:
        mock_count_result = MagicMock()
        mock_count_result.scalar_one.return_value = 0

        with patch("src.api.routers.tickets.select") as mock_select, \
             patch("src.api.routers.tickets.func") as mock_func:

            mock_result = MagicMock()
            mock_result.scalars.return_value.all.return_value = []

            mock_db.execute.side_effect = [mock_count_result, mock_result]

            result = await list_tickets(
                sentiment=None,
                limit=limit,
                offset=0,
                db=mock_db,
                current_user=test_user
            )
            assert result.total == 0
