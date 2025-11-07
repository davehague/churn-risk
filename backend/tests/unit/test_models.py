import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from src.models.base import Base
from src.models.tenant import Tenant, PlanTier
from src.models.user import User, UserRole
from src.models.company import Company
from src.models.integration import Integration
from src.models.contact import Contact
from src.models.ticket import Ticket
from src.models.topic import TicketTopic, TicketTopicAssignment
from src.models.churn_risk import ChurnRiskCard, ChurnRiskComment


@pytest.fixture
def db_session():
    """Create test database session using PostgreSQL."""
    # Use test database
    engine = create_engine("postgresql://postgres:password@localhost:5432/churn_risk_dev")
    Session = sessionmaker(bind=engine)
    session = Session()
    yield session
    # Rollback to clean up test data
    session.rollback()
    session.close()


def test_create_tenant(db_session):
    """Test creating a tenant."""
    import uuid
    unique_subdomain = f"flxpoint-{uuid.uuid4().hex[:8]}"

    tenant = Tenant(
        name="FlxPoint",
        subdomain=unique_subdomain,
        plan_tier=PlanTier.PRO
    )
    db_session.add(tenant)
    db_session.commit()

    assert tenant.id is not None
    assert tenant.name == "FlxPoint"
    assert tenant.subdomain == unique_subdomain
    assert tenant.plan_tier == PlanTier.PRO


def test_tenant_user_relationship(db_session):
    """Test tenant to user relationship."""
    import uuid
    unique_subdomain = f"testco-{uuid.uuid4().hex[:8]}"
    unique_firebase_uid = f"test-firebase-uid-{uuid.uuid4().hex[:8]}"

    tenant = Tenant(name="TestCo", subdomain=unique_subdomain)
    db_session.add(tenant)
    db_session.commit()

    user = User(
        tenant_id=tenant.id,
        firebase_uid=unique_firebase_uid,
        email="test@example.com",
        name="Test User",
        role=UserRole.ADMIN
    )
    db_session.add(user)
    db_session.commit()

    assert len(tenant.users) == 1
    assert tenant.users[0].email == "test@example.com"
    assert user.tenant.name == "TestCo"


def test_company_cascade_delete(db_session):
    """Test cascade delete when tenant is deleted."""
    import uuid
    unique_subdomain = f"testco-{uuid.uuid4().hex[:8]}"

    tenant = Tenant(name="TestCo", subdomain=unique_subdomain)
    db_session.add(tenant)
    db_session.commit()

    company = Company(
        tenant_id=tenant.id,
        external_id="hubspot-123",
        name="Acme Corp",
        mrr=1000.00
    )
    db_session.add(company)
    db_session.commit()

    tenant_id = tenant.id
    db_session.delete(tenant)
    db_session.commit()

    # Company should be deleted due to cascade
    assert db_session.query(Company).filter_by(tenant_id=tenant_id).count() == 0
