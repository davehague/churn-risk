import httpx
from typing import Dict, List, Any
from datetime import datetime
from src.core.config import settings


class HubSpotClient:
    """Client for interacting with HubSpot API."""

    BASE_URL = "https://api.hubapi.com"

    def __init__(self, access_token: str):
        """
        Initialize HubSpot client with OAuth access token.

        Args:
            access_token: OAuth access token from authorization flow
        """
        self.headers = {
            "Authorization": f"Bearer {access_token}",
            "Content-Type": "application/json",
        }

    @classmethod
    async def exchange_code_for_token(cls, code: str, redirect_uri: str) -> Dict[str, Any]:
        """
        Exchange OAuth authorization code for access token.

        Returns:
            Dict with 'access_token', 'refresh_token', 'expires_in'
        """
        async with httpx.AsyncClient() as client:
            response = await client.post(
                "https://api.hubapi.com/oauth/v1/token",
                data={
                    "grant_type": "authorization_code",
                    "client_id": settings.HUBSPOT_CLIENT_ID,
                    "client_secret": settings.HUBSPOT_CLIENT_SECRET,
                    "redirect_uri": redirect_uri,
                    "code": code,
                },
            )
            response.raise_for_status()
            return response.json()

    @classmethod
    async def refresh_access_token(cls, refresh_token: str) -> Dict[str, Any]:
        """
        Refresh an expired access token.

        Returns:
            Dict with new 'access_token', 'refresh_token', 'expires_in'
        """
        async with httpx.AsyncClient() as client:
            response = await client.post(
                "https://api.hubapi.com/oauth/v1/token",
                data={
                    "grant_type": "refresh_token",
                    "client_id": settings.HUBSPOT_CLIENT_ID,
                    "client_secret": settings.HUBSPOT_CLIENT_SECRET,
                    "refresh_token": refresh_token,
                },
            )
            response.raise_for_status()
            return response.json()

    async def search_tickets(
        self,
        limit: int = 100,
        sort_by: str = "createdate",
        sort_direction: str = "DESCENDING",
        properties: List[str] | None = None
    ) -> Dict[str, Any]:
        """
        Search tickets from HubSpot with sorting.

        Uses the HubSpot Search API to fetch tickets sorted by a specified property.
        This is the preferred method for getting recent tickets.

        Args:
            limit: Number of tickets to fetch (max 100)
            sort_by: Property to sort by (default: "createdate")
            sort_direction: "ASCENDING" or "DESCENDING" (default: "DESCENDING")
            properties: List of properties to fetch

        Returns:
            Dict with 'results' and 'paging' keys
        """
        default_properties = [
            "subject",
            "content",
            "hs_ticket_id",
            "hs_ticket_priority",
            "hs_pipeline_stage",
            "createdate",
            "hs_lastmodifieddate",
        ]

        request_body = {
            "limit": min(limit, 100),
            "properties": properties or default_properties,
            "sorts": [
                {
                    "propertyName": sort_by,
                    "direction": sort_direction
                }
            ]
        }

        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{self.BASE_URL}/crm/v3/objects/tickets/search",
                headers=self.headers,
                json=request_body,
                timeout=30.0
            )
            response.raise_for_status()
            return response.json()

    async def get_tickets(
        self,
        limit: int = 100,
        after: str | None = None,
        properties: List[str] | None = None
    ) -> Dict[str, Any]:
        """
        Fetch tickets from HubSpot.

        Note: This method does not support sorting. For sorted results,
        use search_tickets() instead.

        Args:
            limit: Number of tickets to fetch (max 100)
            after: Pagination cursor
            properties: List of properties to fetch

        Returns:
            Dict with 'results' and 'paging' keys
        """
        default_properties = [
            "subject",
            "content",
            "hs_ticket_id",
            "hs_ticket_priority",
            "hs_pipeline_stage",
            "createdate",
            "hs_lastmodifieddate",
        ]

        params = {
            "limit": min(limit, 100),
            "properties": properties or default_properties,
        }

        if after:
            params["after"] = after

        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{self.BASE_URL}/crm/v3/objects/tickets",
                headers=self.headers,
                params=params,
                timeout=30.0
            )
            response.raise_for_status()
            return response.json()

    async def get_ticket(self, ticket_id: str) -> Dict[str, Any]:
        """Fetch a single ticket by ID."""
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{self.BASE_URL}/crm/v3/objects/tickets/{ticket_id}",
                headers=self.headers,
                timeout=30.0
            )
            response.raise_for_status()
            return response.json()

    async def get_companies(self, limit: int = 100) -> Dict[str, Any]:
        """Fetch companies from HubSpot."""
        params = {"limit": min(limit, 100)}

        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{self.BASE_URL}/crm/v3/objects/companies",
                headers=self.headers,
                params=params,
                timeout=30.0
            )
            response.raise_for_status()
            return response.json()

    async def get_contacts(self, limit: int = 100) -> Dict[str, Any]:
        """Fetch contacts from HubSpot."""
        params = {"limit": min(limit, 100)}

        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{self.BASE_URL}/crm/v3/objects/contacts",
                headers=self.headers,
                params=params,
                timeout=30.0
            )
            response.raise_for_status()
            return response.json()

    async def get_ticket_associations(
        self,
        ticket_id: str,
        association_type: str = "emails"
    ) -> Dict[str, Any]:
        """
        Get associations for a ticket (emails, calls, notes, etc.).

        Args:
            ticket_id: HubSpot ticket ID
            association_type: Type of association (default: "emails")

        Returns:
            Dict with 'results' containing association IDs
        """
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{self.BASE_URL}/crm/v4/objects/tickets/{ticket_id}/associations/{association_type}",
                headers=self.headers,
                timeout=30.0
            )
            response.raise_for_status()
            return response.json()

    async def get_email(self, email_id: str) -> Dict[str, Any]:
        """
        Fetch a single email engagement by ID.

        Args:
            email_id: HubSpot email engagement ID

        Returns:
            Dict with email properties including subject, text, html, etc.
        """
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{self.BASE_URL}/crm/v3/objects/emails/{email_id}",
                headers=self.headers,
                params={
                    "properties": [
                        "hs_email_subject",
                        "hs_email_text",
                        "hs_email_html",
                        "hs_timestamp",
                        "hs_email_direction",
                        "hs_email_from",
                        "hs_email_to"
                    ]
                },
                timeout=30.0
            )
            response.raise_for_status()
            return response.json()

    async def get_ticket_email_thread(self, ticket_id: str) -> List[Dict[str, Any]]:
        """
        Fetch all emails associated with a ticket, sorted by timestamp.

        This retrieves the complete email conversation thread for a ticket,
        which provides full context for sentiment analysis.

        Args:
            ticket_id: HubSpot ticket ID

        Returns:
            List of email dicts sorted by timestamp (oldest first)
        """
        # Get associated email IDs
        try:
            associations_response = await self.get_ticket_associations(ticket_id, "emails")
        except httpx.HTTPStatusError as e:
            if e.response.status_code == 404:
                # No associations found
                return []
            raise

        email_ids = [
            result["toObjectId"]
            for result in associations_response.get("results", [])
        ]

        if not email_ids:
            return []

        # Fetch each email's details
        emails = []
        for email_id in email_ids:
            try:
                email_data = await self.get_email(email_id)
                emails.append(email_data)
            except httpx.HTTPStatusError as e:
                # Log but continue if individual email fetch fails
                import logging
                logger = logging.getLogger(__name__)
                logger.warning(f"Failed to fetch email {email_id}: {e}")
                continue

        # Sort by timestamp (oldest first for chronological thread)
        emails.sort(
            key=lambda e: e.get("properties", {}).get("hs_timestamp", "0")
        )

        return emails

    async def create_webhook_subscription(
        self,
        webhook_url: str,
        subscription_type: str = "ticket.creation"
    ) -> Dict[str, Any]:
        """
        Create a webhook subscription for real-time events.

        Args:
            webhook_url: URL to receive webhook events
            subscription_type: Type of event (e.g., "ticket.creation", "ticket.propertyChange")
        """
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{self.BASE_URL}/webhooks/v3/{settings.HUBSPOT_CLIENT_ID}/subscriptions",
                headers=self.headers,
                json={
                    "enabled": True,
                    "subscriptionDetails": {
                        "subscriptionType": subscription_type,
                        "propertyName": None,
                    },
                    "webhookUrl": webhook_url,
                },
                timeout=30.0
            )
            response.raise_for_status()
            return response.json()
