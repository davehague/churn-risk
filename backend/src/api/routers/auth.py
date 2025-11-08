from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from firebase_admin import auth
from src.core.database import get_db
from src.schemas.auth import (
    RegisterRequest,
    RegisterResponse,
    CheckSubdomainRequest,
    CheckSubdomainResponse
)
from src.models.tenant import Tenant, PlanTier
from src.models.user import User, UserRole

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/check-subdomain", response_model=CheckSubdomainResponse)
async def check_subdomain(
    request: CheckSubdomainRequest,
    db: Session = Depends(get_db)
):
    """Check if subdomain is available."""
    existing = db.query(Tenant).filter(
        Tenant.subdomain == request.subdomain
    ).first()

    return CheckSubdomainResponse(
        available=existing is None,
        subdomain=request.subdomain
    )


@router.post("/register", response_model=RegisterResponse, status_code=201)
async def register(
    request: RegisterRequest,
    db: Session = Depends(get_db)
):
    """Register a new user and create tenant."""
    # Check subdomain availability
    existing_tenant = db.query(Tenant).filter(
        Tenant.subdomain == request.subdomain
    ).first()

    if existing_tenant:
        raise HTTPException(
            status_code=400,
            detail="Subdomain already taken. Please choose another."
        )

    try:
        # Create Firebase user
        firebase_user = auth.create_user(
            email=request.email,
            password=request.password,
            display_name=request.name
        )

        # Create tenant
        tenant = Tenant(
            name=request.company_name,
            subdomain=request.subdomain,
            plan_tier=PlanTier.STARTER
        )
        db.add(tenant)
        db.flush()  # Get tenant ID before creating user

        # Create user
        user = User(
            tenant_id=tenant.id,
            firebase_uid=firebase_user.uid,
            email=request.email,
            name=request.name,
            role=UserRole.ADMIN
        )
        db.add(user)
        db.commit()

        return RegisterResponse(
            message="Registration successful. Please log in.",
            email=request.email
        )

    except auth.EmailAlreadyExistsError:
        db.rollback()
        raise HTTPException(
            status_code=400,
            detail="Email already registered. Please log in."
        )
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=500,
            detail=f"Registration failed: {str(e)}"
        )
