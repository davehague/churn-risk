from sqlalchemy import Column, String, ForeignKey, Enum as SQLEnum, DateTime, Text
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import relationship
import enum
from src.models.base import Base, UUIDMixin, TimestampMixin


class IntegrationType(str, enum.Enum):
    """Types of integrations."""
    HUBSPOT = "hubspot"
    ZENDESK = "zendesk"
    HELPSCOUT = "helpscout"


class IntegrationStatus(str, enum.Enum):
    """Integration connection status."""
    ACTIVE = "active"
    ERROR = "error"
    DISCONNECTED = "disconnected"


class Integration(Base, UUIDMixin, TimestampMixin):
    """Integration model - HubSpot/Zendesk connections."""
    __tablename__ = "integrations"

    tenant_id = Column(UUID(as_uuid=True), ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False, index=True)
    type = Column(SQLEnum(IntegrationType), nullable=False)
    status = Column(SQLEnum(IntegrationStatus), default=IntegrationStatus.ACTIVE, nullable=False)
    credentials = Column(JSONB, nullable=False)  # Encrypted in production
    settings = Column(JSONB, default=dict)
    last_synced_at = Column(DateTime, nullable=True)
    error_message = Column(Text, nullable=True)

    # Relationships
    tenant = relationship("Tenant", back_populates="integrations")

    def __repr__(self):
        return f"<Integration {self.type} for tenant {self.tenant_id}>"
