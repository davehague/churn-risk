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


@router.post("/hubspot/callback")
async def hubspot_oauth_callback(
    request: HubSpotOAuthCallbackRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin)
):
    """Handle HubSpot OAuth callback."""
    try:
        # Exchange code for access token
        token_data = await HubSpotClient.exchange_code_for_token(
            code=request.code,
            redirect_uri=request.redirect_uri
        )

        # Check if integration already exists
        existing = db.query(Integration).filter(
            Integration.tenant_id == current_user.tenant_id,
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
                tenant_id=current_user.tenant_id,
                type=IntegrationType.HUBSPOT,
                status=IntegrationStatus.ACTIVE,
                credentials=token_data
            )
            db.add(integration)

        db.commit()
        db.refresh(integration)

        return IntegrationResponse(
            id=str(integration.id),
            type=integration.type,
            status=integration.status,
            last_synced_at=integration.last_synced_at,
            created_at=integration.created_at
        )

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
