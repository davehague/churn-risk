import pytest
from pydantic import ValidationError
from src.schemas.auth import RegisterRequest, CheckSubdomainRequest


def test_register_request_valid():
    """Test valid registration request."""
    data = {
        "email": "test@example.com",
        "password": "SecurePass123",
        "name": "John Doe",
        "company_name": "Acme Corp",
        "subdomain": "acme"
    }
    request = RegisterRequest(**data)
    assert request.email == "test@example.com"
    assert request.subdomain == "acme"


def test_register_request_invalid_subdomain_uppercase():
    """Test subdomain must be lowercase."""
    data = {
        "email": "test@example.com",
        "password": "SecurePass123",
        "name": "John Doe",
        "company_name": "Acme Corp",
        "subdomain": "Acme"
    }
    with pytest.raises(ValidationError):
        RegisterRequest(**data)


def test_register_request_invalid_subdomain_too_short():
    """Test subdomain minimum length."""
    data = {
        "email": "test@example.com",
        "password": "SecurePass123",
        "name": "John Doe",
        "company_name": "Acme Corp",
        "subdomain": "ab"
    }
    with pytest.raises(ValidationError):
        RegisterRequest(**data)


def test_register_request_invalid_subdomain_special_chars():
    """Test subdomain alphanumeric only."""
    data = {
        "email": "test@example.com",
        "password": "SecurePass123",
        "name": "John Doe",
        "company_name": "Acme Corp",
        "subdomain": "acme_corp"
    }
    with pytest.raises(ValidationError):
        RegisterRequest(**data)


def test_check_subdomain_request():
    """Test subdomain check request."""
    request = CheckSubdomainRequest(subdomain="acme")
    assert request.subdomain == "acme"
