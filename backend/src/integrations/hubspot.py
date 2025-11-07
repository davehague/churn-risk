import httpx
from typing import Dict, List, Any
from datetime import datetime
from src.core.config import settings


class HubSpotClient:
    """Client for interacting with HubSpot API."""

    BASE_URL = "https://api.hubapi.com"

    def __init__(self, access_token: str):
        self.access_token = access_token
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

    async def get_tickets(
        self,
        limit: int = 100,
        after: str | None = None,
        properties: List[str] | None = None
    ) -> Dict[str, Any]:
        """
        Fetch tickets from HubSpot.

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
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{self.BASE_URL}/crm/v3/objects/companies",
                headers=self.headers,
                params={"limit": min(limit, 100)},
                timeout=30.0
            )
            response.raise_for_status()
            return response.json()

    async def get_contacts(self, limit: int = 100) -> Dict[str, Any]:
        """Fetch contacts from HubSpot."""
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{self.BASE_URL}/crm/v3/objects/contacts",
                headers=self.headers,
                params={"limit": min(limit, 100)},
                timeout=30.0
            )
            response.raise_for_status()
            return response.json()

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
