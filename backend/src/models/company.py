from sqlalchemy import Column, String, ForeignKey, Numeric, Index
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.types import JSON
from sqlalchemy.orm import relationship
from src.models.base import Base, UUIDMixin, TimestampMixin


class Company(Base, UUIDMixin, TimestampMixin):
    """Company model - the tenant's customers."""
    __tablename__ = "companies"
    __table_args__ = (
        Index("ix_companies_tenant_external", "tenant_id", "external_id"),
    )

    tenant_id = Column(UUID(as_uuid=True), ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False, index=True)
    external_id = Column(String(255), nullable=False)  # HubSpot company ID
    name = Column(String(255), nullable=False)
    mrr = Column(Numeric(10, 2), nullable=True)  # Monthly recurring revenue
    crm_metadata = Column(JSON, default=dict)  # Custom fields from CRM, uses JSONB on PostgreSQL, TEXT on SQLite

    # Relationships
    tenant = relationship("Tenant", back_populates="companies")
    contacts = relationship("Contact", back_populates="company", cascade="all, delete-orphan")
    tickets = relationship("Ticket", back_populates="company")
    churn_risks = relationship("ChurnRiskCard", back_populates="company")

    def __repr__(self):
        return f"<Company {self.name} (MRR: ${self.mrr})>"
