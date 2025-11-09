from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from src.core.database import get_db
from src.api.dependencies import get_current_user, require_admin
from src.models.user import User
from src.models.integration import Integration, IntegrationType, IntegrationStatus
from src.schemas.integration import IntegrationResponse, HubSpotOAuthCallbackRequest
from src.integrations.hubspot import HubSpotClient
from datetime import datetime

router = APIRouter(prefix="/integrations", tags=["integrations"])


@router.get("", response_model=list[IntegrationResponse])
async def list_integrations(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """List all integrations for the current tenant."""
    integrations = db.query(Integration).filter(
        Integration.tenant_id == current_user.tenant_id
    ).all()

    return [
        IntegrationResponse(
            id=str(integration.id),
            type=integration.type,
            status=integration.status,
            last_synced_at=integration.last_synced_at,
            created_at=integration.created_at
        )
        for integration in integrations
    ]


@router.get("/hubspot/authorize")
async def hubspot_authorize_url(
    current_user: User = Depends(require_admin)
):
    """Get HubSpot OAuth authorization URL."""
    from src.core.config import settings

    auth_url = (
        f"https://app.hubspot.com/oauth/authorize"
        f"?client_id={settings.HUBSPOT_CLIENT_ID}"
        f"&redirect_uri={settings.HUBSPOT_REDIRECT_URI}"
        f"&scope=crm.objects.contacts.read crm.objects.companies.read tickets"
    )

    return {"authorization_url": auth_url}


@router.get("/hubspot/callback")
async def hubspot_oauth_callback(
    code: str,
    state: str | None = None,
    db: Session = Depends(get_db)
):
    """
    Handle HubSpot OAuth callback.

    NOTE: This endpoint is public (no auth required) because it's called by HubSpot's redirect.
    In production, you should:
    1. Use the 'state' parameter to validate the request and identify the user
    2. Redirect back to the frontend with success/error status

    For development/testing, we'll create a test tenant if none exists.
    """
    from src.core.config import settings
    from src.models.tenant import Tenant, PlanTier

    try:
        # Exchange code for access token
        token_data = await HubSpotClient.exchange_code_for_token(
            code=code,
            redirect_uri=settings.HUBSPOT_REDIRECT_URI
        )

        # For development: Get or create a test tenant
        # In production, this should use the state parameter to identify the user's tenant
        tenant = db.query(Tenant).first()
        if not tenant:
            tenant = Tenant(
                name="Test Tenant",
                subdomain="test",
                plan_tier=PlanTier.STARTER
            )
            db.add(tenant)
            db.commit()
            db.refresh(tenant)

        # Check if integration already exists for this tenant
        existing = db.query(Integration).filter(
            Integration.tenant_id == tenant.id,
            Integration.type == IntegrationType.HUBSPOT
        ).first()

        if existing:
            # Update existing integration
            existing.credentials = token_data
            existing.status = IntegrationStatus.ACTIVE
            existing.error_message = None
            integration = existing
        else:
            # Create new integration
            integration = Integration(
                tenant_id=tenant.id,
                type=IntegrationType.HUBSPOT,
                status=IntegrationStatus.ACTIVE,
                credentials=token_data
            )
            db.add(integration)

        db.commit()
        db.refresh(integration)

        # Return success message (in production, redirect to frontend)
        return {
            "success": True,
            "message": "HubSpot connected successfully!",
            "integration_id": str(integration.id),
            "tenant_id": str(tenant.id)
        }

    except Exception as e:
        raise HTTPException(
            status_code=400,
            detail=f"Failed to connect to HubSpot: {str(e)}"
        )


@router.delete("/{integration_id}")
async def delete_integration(
    integration_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin)
):
    """Delete an integration."""
    from uuid import UUID

    integration = db.query(Integration).filter(
        Integration.id == UUID(integration_id),
        Integration.tenant_id == current_user.tenant_id
    ).first()

    if not integration:
        raise HTTPException(status_code=404, detail="Integration not found")

    db.delete(integration)
    db.commit()

    return {"message": "Integration deleted successfully"}
