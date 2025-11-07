from sqlalchemy import Column, String, Enum as SQLEnum
from sqlalchemy.orm import relationship
import enum
from src.models.base import Base, UUIDMixin, TimestampMixin


class PlanTier(str, enum.Enum):
    """Subscription plan tiers."""
    STARTER = "starter"
    PRO = "pro"
    ENTERPRISE = "enterprise"


class Tenant(Base, UUIDMixin, TimestampMixin):
    """Tenant model - companies using the churn risk app."""
    __tablename__ = "tenants"

    name = Column(String(255), nullable=False)
    subdomain = Column(String(63), unique=True, nullable=False, index=True)
    plan_tier = Column(SQLEnum(PlanTier), default=PlanTier.STARTER, nullable=False)

    # Relationships
    users = relationship("User", back_populates="tenant", cascade="all, delete-orphan")
    integrations = relationship("Integration", back_populates="tenant", cascade="all, delete-orphan")
    companies = relationship("Company", back_populates="tenant", cascade="all, delete-orphan")
    tickets = relationship("Ticket", back_populates="tenant", cascade="all, delete-orphan")
    topics = relationship("TicketTopic", back_populates="tenant", cascade="all, delete-orphan")
    churn_risks = relationship("ChurnRiskCard", back_populates="tenant", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<Tenant {self.name} ({self.subdomain})>"
