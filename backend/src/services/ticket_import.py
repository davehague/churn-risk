"""Ticket import service for fetching and analyzing HubSpot tickets."""

import logging
from datetime import datetime, timedelta, timezone
from typing import Dict, Any
from uuid import UUID
from pydantic import BaseModel
from sqlalchemy.orm import Session
from sqlalchemy import select

from src.models.ticket import Ticket, TicketStatus
from src.models.integration import Integration, IntegrationType, IntegrationStatus
from src.models.company import Company
from src.models.contact import Contact
from src.integrations.hubspot import HubSpotClient
from src.services.openrouter import OpenRouterAnalyzer


logger = logging.getLogger(__name__)


class ImportResult(BaseModel):
    """Result of ticket import operation."""
    imported: int = 0  # New tickets added to DB
    analyzed: int = 0  # Tickets analyzed with AI
    skipped: int = 0   # Already had sentiment
    failed: int = 0    # Analysis failures


class TicketImportService:
    """Service for importing and analyzing tickets from HubSpot."""

    def __init__(self, db: Session, analyzer: OpenRouterAnalyzer | None = None):
        """
        Initialize ticket import service.

        Args:
            db: Database session
            analyzer: AI analyzer (defaults to OpenRouterAnalyzer)
        """
        self.db = db
        self.analyzer = analyzer or OpenRouterAnalyzer()

    async def import_and_analyze_tickets(
        self,
        tenant_id: UUID,
        days_back: int = 7
    ) -> ImportResult:
        """
        Import tickets from HubSpot and analyze with AI.

        Fetches tickets created in the last N days, upserts to database,
        and performs sentiment analysis on new tickets.

        Args:
            tenant_id: Tenant ID to import tickets for
            days_back: Number of days to look back (default: 7)

        Returns:
            ImportResult with counts of imported, analyzed, skipped, and failed tickets

        Raises:
            ValueError: If HubSpot integration not found or inactive
        """
        result = ImportResult()

        # 1. Get HubSpot integration for tenant
        integration = await self._get_hubspot_integration(tenant_id)
        if not integration:
            raise ValueError("HubSpot integration not found")

        if integration.status != IntegrationStatus.ACTIVE:
            raise ValueError(f"HubSpot integration is {integration.status}")

        # 2. Initialize HubSpot client
        access_token = integration.credentials.get("access_token")
        if not access_token:
            raise ValueError("HubSpot access token not found in integration credentials")

        client = HubSpotClient(access_token)

        # 3. Fetch tickets from last N days
        logger.info(f"Fetching tickets for tenant {tenant_id}, {days_back} days back...")
        try:
            tickets_data = await self._fetch_recent_tickets(client, integration, days_back)
        except Exception as e:
            logger.error(f"Failed to fetch tickets from HubSpot: {e}")
            raise

        logger.info(f"Fetched {len(tickets_data)} tickets from HubSpot for tenant {tenant_id}")

        # 4. Process each ticket
        for i, ticket_data in enumerate(tickets_data, 1):
            try:
                logger.info(f"[Ticket Import] Processing ticket {i}/{len(tickets_data)}: {ticket_data.get('id')}")
                await self._process_ticket(tenant_id, ticket_data, result, integration)
            except Exception as e:
                logger.error(f"[Ticket Import] Failed to process ticket {ticket_data.get('id')}: {e}", exc_info=True)
                result.failed += 1

        # 5. Commit all changes
        logger.info(f"[Ticket Import] Committing {result.imported} imported, {result.analyzed} analyzed tickets...")
        try:
            self.db.commit()
            logger.info(f"[Ticket Import] Commit successful!")
        except Exception as e:
            logger.error(f"[Ticket Import] Failed to commit ticket import transaction: {e}", exc_info=True)
            self.db.rollback()
            raise

        logger.info(f"[Ticket Import] Import complete: {result}")
        return result

    async def _get_hubspot_integration(self, tenant_id: UUID) -> Integration | None:
        """Get HubSpot integration for tenant."""
        stmt = select(Integration).where(
            Integration.tenant_id == tenant_id,
            Integration.type == IntegrationType.HUBSPOT
        )
        result = self.db.execute(stmt)
        return result.scalar_one_or_none()

    async def _fetch_recent_tickets(
        self,
        client: HubSpotClient,
        integration: Integration,
        days_back: int
    ) -> list[Dict[str, Any]]:
        """
        Fetch the most recent tickets from HubSpot using Search API.

        Uses HubSpot Search API with sorting by creation date descending
        to get the most recently created tickets.

        Args:
            client: HubSpot API client
            integration: Integration record for token refresh
            days_back: Not used currently (kept for API compatibility)

        Returns:
            List of ticket data from HubSpot
        """
        import httpx
        from src.integrations.hubspot import HubSpotClient as HSClient

        # Fetch tickets sorted by creation date (newest first) using Search API
        try:
            response = await client.search_tickets(
                limit=20,
                sort_by="createdate",
                sort_direction="DESCENDING"
            )
        except httpx.HTTPStatusError as e:
            if e.response.status_code == 401:
                # Token expired, refresh and retry
                logger.info("Access token expired, refreshing...")
                refresh_token = integration.credentials.get("refresh_token")
                if not refresh_token:
                    raise ValueError("No refresh token available")

                # Refresh the token
                new_tokens = await HSClient.refresh_access_token(refresh_token)

                # Update integration credentials
                integration.credentials = new_tokens
                integration.last_synced_at = datetime.now(timezone.utc)
                self.db.commit()

                logger.info("Token refreshed successfully")

                # Create new client with fresh token and retry
                client = HubSpotClient(access_token=new_tokens["access_token"])
                response = await client.search_tickets(
                    limit=20,
                    sort_by="createdate",
                    sort_direction="DESCENDING"
                )
            else:
                raise

        tickets = response.get("results", [])
        logger.info(f"Fetched {len(tickets)} most recent tickets from HubSpot (sorted by createdate DESC)")

        # Log the date range for debugging
        if tickets:
            first_date = tickets[0].get("properties", {}).get("createdate")
            last_date = tickets[-1].get("properties", {}).get("createdate") if len(tickets) > 0 else None
            logger.info(f"Date range: {first_date} to {last_date}")

        return tickets

    async def _process_ticket(
        self,
        tenant_id: UUID,
        ticket_data: Dict[str, Any],
        result: ImportResult,
        integration: Integration
    ) -> None:
        """
        Process a single ticket: upsert to DB and analyze if needed.

        Args:
            tenant_id: Tenant ID
            ticket_data: Raw ticket data from HubSpot
            result: ImportResult to update with counts
            integration: HubSpot integration with credentials
        """
        properties = ticket_data.get("properties", {})
        external_id = ticket_data.get("id")

        if not external_id:
            logger.warning(f"Ticket missing ID, skipping: {ticket_data}")
            result.failed += 1
            return

        # Extract ticket fields
        subject = properties.get("subject", "No Subject")
        content = properties.get("content", "")
        status_str = properties.get("hs_pipeline_stage", "new")
        priority = properties.get("hs_ticket_priority")  # Can be None, HIGH, MEDIUM, LOW, etc.

        # Map HubSpot status to our enum
        status = self._map_ticket_status(status_str)

        # Parse HubSpot creation date
        hubspot_created_at = None
        createdate_str = properties.get("createdate")
        if createdate_str:
            # HubSpot returns ISO 8601 format
            hubspot_created_at = datetime.fromisoformat(createdate_str.replace("Z", "+00:00"))

        # Parse HubSpot last modified date
        hubspot_updated_at = None
        updated_str = properties.get("hs_lastmodifieddate")
        if updated_str:
            hubspot_updated_at = datetime.fromisoformat(updated_str.replace("Z", "+00:00"))

        # Build external URL
        # HubSpot URL format: https://app.hubspot.com/help-desk/{portalId}/view/search/ticket/{ticketId}/
        hub_id = integration.credentials.get("hub_id")
        if hub_id:
            external_url = f"https://app.hubspot.com/help-desk/{hub_id}/view/search/ticket/{external_id}/"
        else:
            # Fallback to basic URL if hub_id not available
            external_url = f"https://app.hubspot.com/contacts/ticket/{external_id}"

        # Check if ticket already exists
        existing_ticket = self._get_ticket_by_external_id(tenant_id, external_id)

        if existing_ticket:
            # Update existing ticket
            existing_ticket.subject = subject
            existing_ticket.content = content
            existing_ticket.status = status
            existing_ticket.hubspot_created_at = hubspot_created_at
            existing_ticket.hubspot_updated_at = hubspot_updated_at
            existing_ticket.priority = priority
            existing_ticket.external_url = external_url
            existing_ticket.source_metadata = properties

            ticket = existing_ticket
        else:
            # Create new ticket
            ticket = Ticket(
                tenant_id=tenant_id,
                external_id=external_id,
                subject=subject,
                content=content,
                status=status,
                hubspot_created_at=hubspot_created_at,
                hubspot_updated_at=hubspot_updated_at,
                priority=priority,
                external_url=external_url,
                source_metadata=properties
            )
            self.db.add(ticket)
            result.imported += 1

        # Flush to get ticket ID for relationships
        self.db.flush()

        # Analyze sentiment if not already done
        if ticket.sentiment_score is None and content:
            try:
                analysis_result = await self.analyzer.analyze_ticket(
                    ticket_content=f"Subject: {subject}\n\n{content}"
                )

                # Update sentiment fields
                ticket.sentiment_score = analysis_result.sentiment.sentiment
                ticket.sentiment_confidence = analysis_result.sentiment.confidence
                ticket.sentiment_analyzed_at = datetime.now(timezone.utc)

                result.analyzed += 1
                logger.info(
                    f"Analyzed ticket {external_id}: "
                    f"{analysis_result.sentiment.sentiment} "
                    f"(confidence: {analysis_result.sentiment.confidence:.2f})"
                )
            except Exception as e:
                logger.error(f"Failed to analyze ticket {external_id}: {e}")
                result.failed += 1
        else:
            if ticket.sentiment_score is not None:
                result.skipped += 1
                logger.debug(f"Skipping analysis for ticket {external_id} (already analyzed)")

    def _get_ticket_by_external_id(
        self,
        tenant_id: UUID,
        external_id: str
    ) -> Ticket | None:
        """Get ticket by tenant_id and external_id."""
        stmt = select(Ticket).where(
            Ticket.tenant_id == tenant_id,
            Ticket.external_id == external_id
        )
        result = self.db.execute(stmt)
        return result.scalar_one_or_none()

    def _map_ticket_status(self, hubspot_status: str) -> TicketStatus:
        """
        Map HubSpot ticket status to our enum.

        HubSpot uses pipeline stages, we map to simplified status.
        """
        status_lower = hubspot_status.lower()

        if "new" in status_lower:
            return TicketStatus.NEW
        elif "waiting" in status_lower or "pending" in status_lower:
            return TicketStatus.WAITING
        elif "closed" in status_lower or "resolved" in status_lower:
            return TicketStatus.CLOSED
        else:
            return TicketStatus.OPEN


async def import_and_analyze_tickets(
    tenant_id: UUID,
    db: Session,
    days_back: int = 7,
    analyzer: OpenRouterAnalyzer | None = None
) -> ImportResult:
    """
    Convenience function for importing and analyzing tickets.

    Note: This function manages its own database transaction. It will commit all
    changes on success or rollback on failure. The caller should not commit the
    session after calling this function.

    Args:
        tenant_id: Tenant ID to import tickets for
        db: Database session
        days_back: Number of days to look back (default: 7)
        analyzer: AI analyzer (defaults to OpenRouterAnalyzer)

    Returns:
        ImportResult with counts of imported, analyzed, skipped, and failed tickets

    Raises:
        ValueError: If HubSpot integration not found or inactive
        Exception: If transaction commit fails (session will be rolled back)
    """
    service = TicketImportService(db, analyzer)
    return await service.import_and_analyze_tickets(tenant_id, days_back)
