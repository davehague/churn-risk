"""Ticket schemas for API requests and responses."""

from pydantic import BaseModel, ConfigDict
from datetime import datetime
from src.models.ticket import SentimentScore, TicketStatus


class CompanyResponse(BaseModel):
    """Company information in ticket response."""
    model_config = ConfigDict(from_attributes=True)

    id: str
    name: str


class ContactResponse(BaseModel):
    """Contact information in ticket response."""
    model_config = ConfigDict(from_attributes=True)

    id: str
    name: str
    email: str


class TicketResponse(BaseModel):
    """Schema for ticket response."""
    model_config = ConfigDict(from_attributes=True)

    id: str
    external_id: str
    subject: str
    content: str
    sentiment_score: SentimentScore | None
    sentiment_confidence: float | None
    sentiment_analyzed_at: datetime | None
    created_at: datetime  # When we imported the ticket
    hubspot_created_at: datetime | None  # When ticket was created in HubSpot
    hubspot_updated_at: datetime | None  # When ticket was last modified in HubSpot
    priority: str | None  # Ticket priority (HIGH, MEDIUM, LOW, etc.)
    status: TicketStatus
    company: CompanyResponse | None
    contact: ContactResponse | None
    external_url: str | None


class TicketListResponse(BaseModel):
    """Schema for paginated ticket list response."""
    tickets: list[TicketResponse]
    total: int


class ImportTicketsResponse(BaseModel):
    """Schema for ticket import response."""
    imported: int
    analyzed: int
    skipped: int
    failed: int
