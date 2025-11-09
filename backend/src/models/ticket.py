from sqlalchemy import Column, String, ForeignKey, Text, Enum as SQLEnum, Float, DateTime, Index
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import relationship
import enum
from src.models.base import Base, UUIDMixin, TimestampMixin


class TicketStatus(str, enum.Enum):
    """Ticket status."""
    NEW = "new"
    OPEN = "open"
    WAITING = "waiting"
    CLOSED = "closed"


class SentimentScore(str, enum.Enum):
    """Sentiment analysis scores."""
    VERY_NEGATIVE = "very_negative"
    NEGATIVE = "negative"
    NEUTRAL = "neutral"
    POSITIVE = "positive"
    VERY_POSITIVE = "very_positive"


class Ticket(Base, UUIDMixin, TimestampMixin):
    """Support ticket model."""
    __tablename__ = "tickets"
    __table_args__ = (
        Index("ix_tickets_tenant_external", "tenant_id", "external_id", unique=True),
        Index("ix_tickets_tenant_sentiment", "tenant_id", "sentiment_score", "created_at"),
    )

    tenant_id = Column(UUID(as_uuid=True), ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False, index=True)
    external_id = Column(String(255), nullable=False)  # HubSpot ticket ID
    company_id = Column(UUID(as_uuid=True), ForeignKey("companies.id", ondelete="SET NULL"), nullable=True, index=True)
    contact_id = Column(UUID(as_uuid=True), ForeignKey("contacts.id", ondelete="SET NULL"), nullable=True, index=True)

    subject = Column(String(500), nullable=False)
    content = Column(Text, nullable=False)
    status = Column(SQLEnum(TicketStatus), default=TicketStatus.NEW, nullable=False)

    # HubSpot metadata
    hubspot_created_at = Column(DateTime, nullable=True)  # When ticket was created in HubSpot
    hubspot_updated_at = Column(DateTime, nullable=True)  # When ticket was last modified in HubSpot
    priority = Column(String(50), nullable=True)  # Ticket priority (e.g., HIGH, MEDIUM, LOW)

    # Sentiment analysis
    sentiment_score = Column(SQLEnum(SentimentScore), nullable=True, index=True)
    sentiment_confidence = Column(Float, nullable=True)
    sentiment_analyzed_at = Column(DateTime, nullable=True)

    external_url = Column(String(500), nullable=True)  # Deep link to HubSpot
    source_metadata = Column(JSONB, default=dict)  # Raw data from source

    # Relationships
    tenant = relationship("Tenant", back_populates="tickets")
    company = relationship("Company", back_populates="tickets")
    contact = relationship("Contact", back_populates="tickets")
    topic_assignments = relationship("TicketTopicAssignment", back_populates="ticket", cascade="all, delete-orphan")
    churn_risk = relationship("ChurnRiskCard", back_populates="ticket", uselist=False)

    def __repr__(self):
        return f"<Ticket {self.subject[:30]}... ({self.sentiment_score})>"
