"""Unit tests for ticket import service."""

import os
import pytest
from datetime import datetime, timedelta, timezone
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from src.models.base import Base
from src.models.tenant import Tenant
from src.models.integration import Integration, IntegrationType, IntegrationStatus
from src.models.ticket import Ticket, SentimentScore
from src.services.ticket_import import TicketImportService, ImportResult, import_and_analyze_tickets
from src.schemas.ai import SentimentAnalysisResult, TopicClassification, TicketAnalysisResult


@pytest.fixture
def db_session():
    """Create test database session using DATABASE_URL env var."""
    # Use DATABASE_URL from environment (SQLite for CI/CD, PostgreSQL for local)
    database_url = os.getenv("DATABASE_URL", "postgresql://postgres:password@localhost:5432/churn_risk_dev")
    engine = create_engine(database_url)

    # Create tables for SQLite (for CI/CD)
    if database_url.startswith("sqlite"):
        Base.metadata.create_all(engine)

    Session = sessionmaker(bind=engine)
    session = Session()
    yield session
    session.rollback()
    session.close()


@pytest.fixture
def test_tenant(db_session):
    """Create a test tenant."""
    tenant = Tenant(
        name="Test Tenant",
        subdomain=f"test-{uuid4().hex[:8]}"
    )
    db_session.add(tenant)
    db_session.commit()
    return tenant


@pytest.fixture
def hubspot_integration(db_session, test_tenant):
    """Create a test HubSpot integration."""
    integration = Integration(
        tenant_id=test_tenant.id,
        type=IntegrationType.HUBSPOT,
        status=IntegrationStatus.ACTIVE,
        credentials={"access_token": "test-access-token"}
    )
    db_session.add(integration)
    db_session.commit()
    return integration


@pytest.fixture
def mock_analyzer():
    """Create a mock AI analyzer."""
    analyzer = MagicMock()
    analyzer.analyze_ticket = AsyncMock(return_value=TicketAnalysisResult(
        sentiment=SentimentAnalysisResult(
            sentiment=SentimentScore.NEGATIVE,
            confidence=0.85,
            reasoning="Customer is frustrated"
        ),
        topics=[
            TopicClassification(topic_name="API Errors", confidence=0.9)
        ]
    ))
    return analyzer


@pytest.fixture
def sample_hubspot_tickets():
    """Sample HubSpot ticket data."""
    now = datetime.now(timezone.utc)
    return [
        {
            "id": "12345",
            "properties": {
                "subject": "Cannot login",
                "content": "I've been trying to login for the past hour",
                "createdate": now.isoformat(),
                "hs_pipeline_stage": "new"
            }
        },
        {
            "id": "12346",
            "properties": {
                "subject": "Great service",
                "content": "Thank you for the excellent support",
                "createdate": (now - timedelta(days=2)).isoformat(),
                "hs_pipeline_stage": "open"
            }
        },
        {
            "id": "12347",
            "properties": {
                "subject": "Old ticket",
                "content": "This ticket is too old",
                "createdate": (now - timedelta(days=10)).isoformat(),
                "hs_pipeline_stage": "closed"
            }
        }
    ]


@pytest.mark.asyncio
async def test_import_and_analyze_tickets_success(
    db_session,
    test_tenant,
    hubspot_integration,
    mock_analyzer,
    sample_hubspot_tickets
):
    """Test successful import and analysis of tickets."""
    service = TicketImportService(db_session, mock_analyzer)

    # Mock HubSpot client
    with patch("src.services.ticket_import.HubSpotClient") as MockClient:
        mock_client = MockClient.return_value
        mock_client.search_tickets = AsyncMock(return_value={
            "results": sample_hubspot_tickets
        })

        result = await service.import_and_analyze_tickets(test_tenant.id, days_back=7)

        # Should import only the 2 recent tickets (last 7 days)
        assert result.imported == 2
        assert result.analyzed == 2
        assert result.skipped == 0
        assert result.failed == 0

        # Verify tickets in database
        tickets = db_session.query(Ticket).filter_by(tenant_id=test_tenant.id).all()
        assert len(tickets) == 2

        # Verify sentiment analysis was performed
        for ticket in tickets:
            assert ticket.sentiment_score == SentimentScore.NEGATIVE
            assert ticket.sentiment_confidence == 0.85
            assert ticket.sentiment_analyzed_at is not None


@pytest.mark.asyncio
async def test_import_and_analyze_tickets_skip_existing(
    db_session,
    test_tenant,
    hubspot_integration,
    mock_analyzer,
    sample_hubspot_tickets
):
    """Test that existing tickets with sentiment are skipped."""
    service = TicketImportService(db_session, mock_analyzer)

    # Create existing ticket with sentiment
    existing_ticket = Ticket(
        tenant_id=test_tenant.id,
        external_id="12345",
        subject="Cannot login",
        content="I've been trying to login for the past hour",
        sentiment_score=SentimentScore.NEUTRAL,
        sentiment_confidence=0.5,
        sentiment_analyzed_at=datetime.now(timezone.utc)
    )
    db_session.add(existing_ticket)
    db_session.commit()

    # Mock HubSpot client to return only the first ticket
    with patch("src.services.ticket_import.HubSpotClient") as MockClient:
        mock_client = MockClient.return_value
        mock_client.search_tickets = AsyncMock(return_value={
            "results": [sample_hubspot_tickets[0]]
        })

        result = await service.import_and_analyze_tickets(test_tenant.id, days_back=7)

        # Should skip the existing ticket
        assert result.imported == 0
        assert result.analyzed == 0
        assert result.skipped == 1
        assert result.failed == 0

        # Verify sentiment was NOT updated
        db_session.refresh(existing_ticket)
        assert existing_ticket.sentiment_score == SentimentScore.NEUTRAL
        assert existing_ticket.sentiment_confidence == 0.5


@pytest.mark.asyncio
async def test_import_and_analyze_tickets_update_existing_without_sentiment(
    db_session,
    test_tenant,
    hubspot_integration,
    mock_analyzer,
    sample_hubspot_tickets
):
    """Test that existing tickets without sentiment are analyzed."""
    service = TicketImportService(db_session, mock_analyzer)

    # Create existing ticket WITHOUT sentiment
    existing_ticket = Ticket(
        tenant_id=test_tenant.id,
        external_id="12345",
        subject="Old Subject",
        content="Old content",
        sentiment_score=None,
        sentiment_confidence=None,
        sentiment_analyzed_at=None
    )
    db_session.add(existing_ticket)
    db_session.commit()
    ticket_id = existing_ticket.id

    # Mock HubSpot client
    with patch("src.services.ticket_import.HubSpotClient") as MockClient:
        mock_client = MockClient.return_value
        mock_client.search_tickets = AsyncMock(return_value={
            "results": [sample_hubspot_tickets[0]]
        })

        result = await service.import_and_analyze_tickets(test_tenant.id, days_back=7)

        # Should update existing ticket and analyze
        assert result.imported == 0  # Not a new import
        assert result.analyzed == 1
        assert result.skipped == 0
        assert result.failed == 0

        # Verify ticket was updated
        db_session.refresh(existing_ticket)
        assert existing_ticket.id == ticket_id  # Same ticket
        assert existing_ticket.subject == "Cannot login"
        assert existing_ticket.sentiment_score == SentimentScore.NEGATIVE
        assert existing_ticket.sentiment_confidence == 0.85


@pytest.mark.asyncio
async def test_import_and_analyze_tickets_no_integration(db_session, test_tenant):
    """Test error when HubSpot integration not found."""
    service = TicketImportService(db_session)

    with pytest.raises(ValueError, match="HubSpot integration not found"):
        await service.import_and_analyze_tickets(test_tenant.id)


@pytest.mark.asyncio
async def test_import_and_analyze_tickets_inactive_integration(
    db_session,
    test_tenant,
    hubspot_integration
):
    """Test error when HubSpot integration is inactive."""
    service = TicketImportService(db_session)

    # Mark integration as inactive
    hubspot_integration.status = IntegrationStatus.DISCONNECTED
    db_session.commit()

    with pytest.raises(ValueError, match="HubSpot integration is"):
        await service.import_and_analyze_tickets(test_tenant.id)


@pytest.mark.asyncio
async def test_import_and_analyze_tickets_missing_access_token(
    db_session,
    test_tenant,
    hubspot_integration
):
    """Test error when access token is missing."""
    service = TicketImportService(db_session)

    # Remove access token
    hubspot_integration.credentials = {}
    db_session.commit()

    with pytest.raises(ValueError, match="access token not found"):
        await service.import_and_analyze_tickets(test_tenant.id)


@pytest.mark.asyncio
async def test_import_and_analyze_tickets_hubspot_api_error(
    db_session,
    test_tenant,
    hubspot_integration
):
    """Test error handling when HubSpot API fails."""
    service = TicketImportService(db_session)

    with patch("src.services.ticket_import.HubSpotClient") as MockClient:
        mock_client = MockClient.return_value
        mock_client.search_tickets = AsyncMock(side_effect=Exception("HubSpot API error"))

        with pytest.raises(Exception, match="HubSpot API error"):
            await service.import_and_analyze_tickets(test_tenant.id)


@pytest.mark.asyncio
async def test_import_and_analyze_tickets_analysis_failure(
    db_session,
    test_tenant,
    hubspot_integration,
    sample_hubspot_tickets
):
    """Test partial failure when AI analysis fails."""
    # Create analyzer that fails
    failing_analyzer = MagicMock()
    failing_analyzer.analyze_ticket = AsyncMock(side_effect=Exception("AI service error"))

    service = TicketImportService(db_session, failing_analyzer)

    with patch("src.services.ticket_import.HubSpotClient") as MockClient:
        mock_client = MockClient.return_value
        # Return only first 2 tickets (recent ones)
        mock_client.search_tickets = AsyncMock(return_value={
            "results": sample_hubspot_tickets[:2]
        })

        result = await service.import_and_analyze_tickets(test_tenant.id, days_back=7)

        # Should import tickets but fail analysis
        assert result.imported == 2
        assert result.analyzed == 0
        assert result.failed == 2

        # Verify tickets were saved without sentiment
        tickets = db_session.query(Ticket).filter_by(tenant_id=test_tenant.id).all()
        assert len(tickets) == 2
        for ticket in tickets:
            assert ticket.sentiment_score is None


@pytest.mark.asyncio
async def test_import_and_analyze_tickets_empty_content(
    db_session,
    test_tenant,
    hubspot_integration,
    mock_analyzer
):
    """Test handling of tickets with empty content."""
    service = TicketImportService(db_session, mock_analyzer)

    tickets_with_empty_content = [{
        "id": "12345",
        "properties": {
            "subject": "No content",
            "content": "",  # Empty content
            "createdate": datetime.now(timezone.utc).isoformat(),
            "hs_pipeline_stage": "new"
        }
    }]

    with patch("src.services.ticket_import.HubSpotClient") as MockClient:
        mock_client = MockClient.return_value
        mock_client.search_tickets = AsyncMock(return_value={
            "results": tickets_with_empty_content
        })

        result = await service.import_and_analyze_tickets(test_tenant.id, days_back=7)

        # Should import but skip analysis (no content)
        assert result.imported == 1
        assert result.analyzed == 0
        assert result.skipped == 0
        assert result.failed == 0


@pytest.mark.asyncio
async def test_import_and_analyze_tickets_date_filtering(
    db_session,
    test_tenant,
    hubspot_integration,
    mock_analyzer,
    sample_hubspot_tickets
):
    """Test that only tickets from last N days are imported."""
    service = TicketImportService(db_session, mock_analyzer)

    with patch("src.services.ticket_import.HubSpotClient") as MockClient:
        mock_client = MockClient.return_value
        mock_client.search_tickets = AsyncMock(return_value={
            "results": sample_hubspot_tickets
        })

        # Import with 7 days filter
        result = await service.import_and_analyze_tickets(test_tenant.id, days_back=7)

        # Only 2 tickets should be imported (3rd is 10 days old)
        assert result.imported == 2

        # Import with 1 day filter
        db_session.query(Ticket).delete()
        db_session.commit()

        result = await service.import_and_analyze_tickets(test_tenant.id, days_back=1)

        # Only 1 ticket should be imported (today)
        assert result.imported == 1


@pytest.mark.asyncio
async def test_ticket_status_mapping(db_session, test_tenant, hubspot_integration, mock_analyzer):
    """Test correct mapping of HubSpot status to our enum."""
    service = TicketImportService(db_session, mock_analyzer)

    status_test_cases = [
        ("new", "new"),
        ("New", "new"),
        ("open", "open"),
        ("In Progress", "open"),
        ("waiting", "waiting"),
        ("pending", "waiting"),
        ("Waiting on customer", "waiting"),
        ("closed", "closed"),
        ("resolved", "closed"),
        ("Closed and resolved", "closed"),
    ]

    for hubspot_status, expected_status in status_test_cases:
        ticket_data = {
            "id": f"test-{hubspot_status}",
            "properties": {
                "subject": f"Test {hubspot_status}",
                "content": "Test content",
                "createdate": datetime.now(timezone.utc).isoformat(),
                "hs_pipeline_stage": hubspot_status
            }
        }

        with patch("src.services.ticket_import.HubSpotClient") as MockClient:
            mock_client = MockClient.return_value
            mock_client.search_tickets = AsyncMock(return_value={
                "results": [ticket_data]
            })

            await service.import_and_analyze_tickets(test_tenant.id, days_back=7)

            ticket = db_session.query(Ticket).filter_by(
                tenant_id=test_tenant.id,
                external_id=f"test-{hubspot_status}"
            ).first()

            assert ticket is not None
            assert ticket.status.value == expected_status


@pytest.mark.asyncio
async def test_convenience_function(
    db_session,
    test_tenant,
    hubspot_integration,
    mock_analyzer,
    sample_hubspot_tickets
):
    """Test the convenience function import_and_analyze_tickets."""
    with patch("src.services.ticket_import.HubSpotClient") as MockClient:
        mock_client = MockClient.return_value
        mock_client.search_tickets = AsyncMock(return_value={
            "results": sample_hubspot_tickets[:2]
        })

        result = await import_and_analyze_tickets(
            tenant_id=test_tenant.id,
            db=db_session,
            days_back=7,
            analyzer=mock_analyzer
        )

        assert result.imported == 2
        assert result.analyzed == 2


@pytest.mark.asyncio
async def test_idempotency(
    db_session,
    test_tenant,
    hubspot_integration,
    mock_analyzer,
    sample_hubspot_tickets
):
    """Test that calling import multiple times is safe."""
    service = TicketImportService(db_session, mock_analyzer)

    with patch("src.services.ticket_import.HubSpotClient") as MockClient:
        mock_client = MockClient.return_value
        mock_client.search_tickets = AsyncMock(return_value={
            "results": sample_hubspot_tickets[:1]
        })

        # First import
        result1 = await service.import_and_analyze_tickets(test_tenant.id, days_back=7)
        assert result1.imported == 1
        assert result1.analyzed == 1

        # Second import (should skip)
        result2 = await service.import_and_analyze_tickets(test_tenant.id, days_back=7)
        assert result2.imported == 0
        assert result2.analyzed == 0
        assert result2.skipped == 1

        # Verify only one ticket in database
        tickets = db_session.query(Ticket).filter_by(tenant_id=test_tenant.id).all()
        assert len(tickets) == 1
