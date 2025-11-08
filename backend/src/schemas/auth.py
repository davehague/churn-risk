from pydantic import BaseModel, EmailStr, Field, field_validator
import re


class RegisterRequest(BaseModel):
    """Request schema for user registration."""
    email: EmailStr
    password: str = Field(..., min_length=8)
    name: str = Field(..., min_length=2, max_length=255)
    company_name: str = Field(..., min_length=2, max_length=255)
    subdomain: str = Field(..., min_length=3, max_length=63)

    @field_validator('subdomain')
    @classmethod
    def validate_subdomain(cls, v: str) -> str:
        """Validate subdomain format."""
        if not re.match(r'^[a-z0-9][a-z0-9-]*[a-z0-9]$', v):
            raise ValueError(
                'Subdomain must be lowercase alphanumeric with hyphens, '
                'and cannot start or end with a hyphen'
            )
        return v


class RegisterResponse(BaseModel):
    """Response schema for successful registration."""
    message: str
    email: str


class CheckSubdomainRequest(BaseModel):
    """Request schema for subdomain availability check."""
    subdomain: str = Field(..., min_length=3, max_length=63)


class CheckSubdomainResponse(BaseModel):
    """Response schema for subdomain availability check."""
    available: bool
    subdomain: str
