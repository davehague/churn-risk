import pytest
from unittest.mock import patch, MagicMock
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from src.models.base import Base
from src.models.tenant import Tenant
from src.models.user import User, UserRole
from src.core.database import get_db
from src.main import app
from fastapi.testclient import TestClient


@pytest.fixture
def test_db():
    """Create test database session using PostgreSQL."""
    # Use test database
    engine = create_engine("postgresql://postgres:password@localhost:5432/churn_risk_dev")
    Session = sessionmaker(bind=engine)
    session = Session()
    yield session
    # Rollback to clean up test data
    session.rollback()
    session.close()


@pytest.fixture
def client(test_db):
    """Create test client with overridden database."""
    def override_get_db():
        try:
            yield test_db
        finally:
            pass

    app.dependency_overrides[get_db] = override_get_db
    yield TestClient(app)
    app.dependency_overrides.clear()


def test_check_subdomain_available(client, test_db):
    """Test checking available subdomain."""
    import uuid
    unique_subdomain = f"acme-{uuid.uuid4().hex[:8]}"

    response = client.post(
        "/api/v1/auth/check-subdomain",
        json={"subdomain": unique_subdomain}
    )
    assert response.status_code == 200
    data = response.json()
    assert data["available"] is True
    assert data["subdomain"] == unique_subdomain


def test_check_subdomain_taken(client, test_db):
    """Test checking taken subdomain."""
    import uuid
    unique_subdomain = f"acme-{uuid.uuid4().hex[:8]}"

    # Create existing tenant
    tenant = Tenant(name="Acme Corp", subdomain=unique_subdomain)
    test_db.add(tenant)
    test_db.commit()

    response = client.post(
        "/api/v1/auth/check-subdomain",
        json={"subdomain": unique_subdomain}
    )
    assert response.status_code == 200
    data = response.json()
    assert data["available"] is False


@patch('src.api.routers.auth.auth.create_user')
def test_register_success(mock_create_user, client, test_db):
    """Test successful user registration."""
    import uuid
    unique_subdomain = f"acme-{uuid.uuid4().hex[:8]}"
    unique_firebase_uid = f"firebase-uid-{uuid.uuid4().hex[:8]}"

    # Mock Firebase user creation
    mock_create_user.return_value = MagicMock(uid=unique_firebase_uid)

    response = client.post(
        "/api/v1/auth/register",
        json={
            "email": "john@example.com",
            "password": "SecurePass123",
            "name": "John Doe",
            "company_name": "Acme Corp",
            "subdomain": unique_subdomain
        }
    )

    assert response.status_code == 201
    data = response.json()
    assert data["message"] == "Registration successful. Please log in."
    assert data["email"] == "john@example.com"

    # Verify tenant created
    tenant = test_db.query(Tenant).filter_by(subdomain=unique_subdomain).first()
    assert tenant is not None
    assert tenant.name == "Acme Corp"

    # Verify user created
    user = test_db.query(User).filter_by(firebase_uid=unique_firebase_uid).first()
    assert user is not None
    assert user.email == "john@example.com"
    assert user.name == "John Doe"
    assert user.role == UserRole.ADMIN
    assert user.tenant_id == tenant.id


@patch('src.api.routers.auth.auth.create_user')
def test_register_duplicate_subdomain(mock_create_user, client, test_db):
    """Test registration with duplicate subdomain."""
    import uuid
    unique_subdomain = f"acme-{uuid.uuid4().hex[:8]}"
    unique_firebase_uid = f"firebase-uid-{uuid.uuid4().hex[:8]}"

    # Create existing tenant
    tenant = Tenant(name="Existing Corp", subdomain=unique_subdomain)
    test_db.add(tenant)
    test_db.commit()

    mock_create_user.return_value = MagicMock(uid=unique_firebase_uid)

    response = client.post(
        "/api/v1/auth/register",
        json={
            "email": "john@example.com",
            "password": "SecurePass123",
            "name": "John Doe",
            "company_name": "Acme Corp",
            "subdomain": unique_subdomain
        }
    )

    assert response.status_code == 400
    assert "Subdomain already taken" in response.json()["detail"]


def test_register_invalid_subdomain_format(client, test_db):
    """Test registration with invalid subdomain format."""
    response = client.post(
        "/api/v1/auth/register",
        json={
            "email": "john@example.com",
            "password": "SecurePass123",
            "name": "John Doe",
            "company_name": "Acme Corp",
            "subdomain": "Acme_Corp"  # Invalid: uppercase and underscore
        }
    )

    assert response.status_code == 422  # Validation error
