from fastapi import FastAPI, Depends
from fastapi.middleware.cors import CORSMiddleware
from src.core.config import settings
from src.api.dependencies import get_current_user
from src.api.routers import integrations, auth
from src.models.user import User

app = FastAPI(
    title="Churn Risk API",
    version="0.1.0",
    docs_url=f"{settings.API_V1_PREFIX}/docs",
    openapi_url=f"{settings.API_V1_PREFIX}/openapi.json",
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.get_cors_origins_list(),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(integrations.router, prefix=settings.API_V1_PREFIX)
app.include_router(auth.router, prefix=settings.API_V1_PREFIX)


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy", "environment": settings.ENVIRONMENT}


@app.get(f"{settings.API_V1_PREFIX}/")
async def root():
    """API root endpoint."""
    return {"message": "Churn Risk API", "version": "0.1.0"}


@app.get(f"{settings.API_V1_PREFIX}/me")
async def get_me(current_user: User = Depends(get_current_user)):
    """Get current authenticated user."""
    return {
        "id": str(current_user.id),
        "email": current_user.email,
        "name": current_user.name,
        "role": current_user.role.value,
        "tenant_id": str(current_user.tenant_id)
    }
