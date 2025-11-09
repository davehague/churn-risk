"""Ticket API endpoints."""

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import select, func
from src.core.database import get_db
from src.api.dependencies import get_current_user
from src.models.user import User
from src.models.ticket import Ticket, SentimentScore
from src.schemas.ticket import (
    TicketResponse,
    TicketListResponse,
    ImportTicketsResponse,
    CompanyResponse,
    ContactResponse,
)
from src.services.ticket_import import import_and_analyze_tickets
import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/tickets", tags=["tickets"])


@router.post("/import", response_model=ImportTicketsResponse)
async def import_tickets(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Import tickets from HubSpot for the current tenant.

    Fetches tickets created in the last 7 days from HubSpot,
    stores them in the database, and analyzes sentiment for new tickets.

    Returns:
        ImportTicketsResponse with counts of imported, analyzed, skipped, and failed tickets
    """
    try:
        result = await import_and_analyze_tickets(
            tenant_id=current_user.tenant_id,
            db=db
        )
        return ImportTicketsResponse(
            imported=result.imported,
            analyzed=result.analyzed,
            skipped=result.skipped,
            failed=result.failed
        )
    except ValueError as e:
        error_msg = str(e)
        if "not found" in error_msg.lower():
            raise HTTPException(
                status_code=404,
                detail="HubSpot integration not found. Please connect HubSpot first."
            )
        elif "inactive" in error_msg.lower() or "status" in error_msg.lower():
            raise HTTPException(
                status_code=401,
                detail="HubSpot integration is not active. Please re-authenticate."
            )
        else:
            raise HTTPException(status_code=400, detail=error_msg)
    except Exception as e:
        logger.error(f"Failed to import tickets for tenant {current_user.tenant_id}: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to import tickets: {str(e)}"
        )


@router.get("", response_model=TicketListResponse)
async def list_tickets(
    sentiment: SentimentScore | None = Query(None, description="Filter by sentiment score"),
    limit: int = Query(100, ge=1, le=500, description="Number of tickets to return"),
    offset: int = Query(0, ge=0, description="Number of tickets to skip"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    List tickets for the current tenant with optional filtering.

    Args:
        sentiment: Optional sentiment filter (positive, negative, neutral, very_positive, very_negative)
        limit: Maximum number of tickets to return (default: 100, max: 500)
        offset: Number of tickets to skip for pagination (default: 0)

    Returns:
        TicketListResponse with list of tickets and total count
    """
    # Build base query
    query = select(Ticket).where(
        Ticket.tenant_id == current_user.tenant_id
    )

    # Apply sentiment filter if provided
    if sentiment:
        query = query.where(Ticket.sentiment_score == sentiment)

    # Get total count
    count_query = select(func.count()).select_from(query.subquery())
    total = db.execute(count_query).scalar_one()

    # Apply ordering, pagination
    query = query.order_by(Ticket.created_at.desc()).offset(offset).limit(limit)

    # Execute query
    result = db.execute(query)
    tickets = result.scalars().all()

    # Convert to response schema
    ticket_responses = []
    for ticket in tickets:
        # Build company response if exists
        company_response = None
        if ticket.company:
            company_response = CompanyResponse(
                id=str(ticket.company.id),
                name=ticket.company.name
            )

        # Build contact response if exists
        contact_response = None
        if ticket.contact:
            contact_response = ContactResponse(
                id=str(ticket.contact.id),
                name=ticket.contact.name,
                email=ticket.contact.email
            )

        ticket_responses.append(
            TicketResponse(
                id=str(ticket.id),
                external_id=ticket.external_id,
                subject=ticket.subject,
                content=ticket.content,
                sentiment_score=ticket.sentiment_score,
                sentiment_confidence=ticket.sentiment_confidence,
                sentiment_analyzed_at=ticket.sentiment_analyzed_at,
                created_at=ticket.created_at,
                status=ticket.status,
                company=company_response,
                contact=contact_response,
                external_url=ticket.external_url
            )
        )

    return TicketListResponse(
        tickets=ticket_responses,
        total=total
    )
