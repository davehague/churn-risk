from pydantic import BaseModel, HttpUrl
from datetime import datetime
from src.models.integration import IntegrationType, IntegrationStatus


class IntegrationBase(BaseModel):
    """Base integration schema."""
    type: IntegrationType


class IntegrationCreate(IntegrationBase):
    """Schema for creating an integration."""
    pass


class IntegrationResponse(IntegrationBase):
    """Schema for integration response."""
    id: str
    status: IntegrationStatus
    last_synced_at: datetime | None
    created_at: datetime

    class Config:
        from_attributes = True


class HubSpotOAuthCallbackRequest(BaseModel):
    """Schema for HubSpot OAuth callback."""
    code: str
    redirect_uri: str
