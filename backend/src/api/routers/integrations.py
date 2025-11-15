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
    """Get HubSpot OAuth authorization URL with state parameter."""
    from src.core.config import settings
    import jwt
    from datetime import timedelta

    # Create state token with tenant_id
    state_payload = {
        "tenant_id": str(current_user.tenant_id),
        "user_id": str(current_user.id),
        "exp": datetime.utcnow() + timedelta(minutes=15)  # State expires in 15 minutes
    }
    state = jwt.encode(state_payload, settings.SECRET_KEY, algorithm="HS256")

    from urllib.parse import urlencode

    # URL-encode parameters properly
    params = {
        "client_id": settings.HUBSPOT_CLIENT_ID,
        "redirect_uri": settings.HUBSPOT_REDIRECT_URI,
        "scope": "crm.objects.contacts.read crm.objects.companies.read tickets sales-email-read",
        "state": state
    }
    auth_url = f"https://app.hubspot.com/oauth/authorize?{urlencode(params)}"

    return {"authorization_url": auth_url}


@router.get("/hubspot/callback")
async def hubspot_oauth_callback(
    code: str,
    state: str | None = None,
    db: Session = Depends(get_db)
):
    """
    Handle HubSpot OAuth callback.

    This endpoint is public (no auth required) because it's called by HubSpot's redirect.
    It uses the 'state' parameter to validate the request and identify the user's tenant.
    """
    from src.core.config import settings
    from src.models.tenant import Tenant
    from fastapi.responses import RedirectResponse
    import jwt
    from uuid import UUID

    try:
        # Validate state parameter
        if not state:
            raise HTTPException(status_code=400, detail="Missing state parameter")

        # Decode state to get tenant_id
        try:
            state_payload = jwt.decode(state, settings.SECRET_KEY, algorithms=["HS256"])
            tenant_id = UUID(state_payload["tenant_id"])
        except jwt.ExpiredSignatureError:
            raise HTTPException(status_code=400, detail="State token expired. Please try connecting again.")
        except (jwt.InvalidTokenError, KeyError, ValueError) as e:
            raise HTTPException(status_code=400, detail="Invalid state parameter")

        # Get the tenant
        tenant = db.query(Tenant).filter(Tenant.id == tenant_id).first()
        if not tenant:
            raise HTTPException(status_code=404, detail="Tenant not found")

        # Exchange code for access token
        token_data = await HubSpotClient.exchange_code_for_token(
            code=code,
            redirect_uri=settings.HUBSPOT_REDIRECT_URI
        )

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

        # Redirect to frontend dashboard with success
        frontend_url = settings.CORS_ORIGINS.split(",")[0] if settings.CORS_ORIGINS else "http://localhost:3000"
        return RedirectResponse(url=f"{frontend_url}/dashboard?hubspot=connected")

    except HTTPException:
        raise
    except Exception as e:
        # Redirect to frontend with error
        frontend_url = settings.CORS_ORIGINS.split(",")[0] if settings.CORS_ORIGINS else "http://localhost:3000"
        return RedirectResponse(url=f"{frontend_url}/dashboard?hubspot=error&message={str(e)}")


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
