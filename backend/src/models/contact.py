from sqlalchemy import Column, String, ForeignKey, Index
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from src.models.base import Base, UUIDMixin, TimestampMixin


class Contact(Base, UUIDMixin, TimestampMixin):
    """Contact model - people at the companies."""
    __tablename__ = "contacts"
    __table_args__ = (
        Index("ix_contacts_tenant_external", "tenant_id", "external_id"),
    )

    tenant_id = Column(UUID(as_uuid=True), ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False, index=True)
    company_id = Column(UUID(as_uuid=True), ForeignKey("companies.id", ondelete="CASCADE"), nullable=True, index=True)
    external_id = Column(String(255), nullable=False)  # HubSpot contact ID
    email = Column(String(255), nullable=False)
    name = Column(String(255), nullable=False)

    # Relationships
    tenant = relationship("Tenant")
    company = relationship("Company", back_populates="contacts")
    tickets = relationship("Ticket", back_populates="contact")
    churn_risks = relationship("ChurnRiskCard", back_populates="contact")

    def __repr__(self):
        return f"<Contact {self.name} ({self.email})>"
