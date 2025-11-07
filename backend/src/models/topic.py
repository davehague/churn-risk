from sqlalchemy import Column, String, ForeignKey, Text, Boolean, Float, DateTime, Enum as SQLEnum, UniqueConstraint, Index
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
import enum
from src.models.base import Base, UUIDMixin, TimestampMixin


class TicketTopic(Base, UUIDMixin, TimestampMixin):
    """Ticket topic model - AI-generated categories."""
    __tablename__ = "ticket_topics"
    __table_args__ = (
        UniqueConstraint("tenant_id", "name", name="uq_tenant_topic_name"),
    )

    tenant_id = Column(UUID(as_uuid=True), ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False, index=True)
    name = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    training_prompt = Column(Text, nullable=True)  # User feedback for AI
    is_active = Column(Boolean, default=True, nullable=False)

    # Relationships
    tenant = relationship("Tenant", back_populates="topics")
    ticket_assignments = relationship("TicketTopicAssignment", back_populates="topic", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<TicketTopic {self.name}>"


class AssignedBy(str, enum.Enum):
    """Who assigned the topic."""
    AI = "ai"
    USER = "user"


class TicketTopicAssignment(Base, UUIDMixin, TimestampMixin):
    """Many-to-many mapping between tickets and topics."""
    __tablename__ = "ticket_topic_assignments"
    __table_args__ = (
        UniqueConstraint("tenant_id", "ticket_id", "topic_id", name="uq_ticket_topic"),
        Index("ix_assignments_tenant_ticket", "tenant_id", "ticket_id"),
    )

    tenant_id = Column(UUID(as_uuid=True), ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False, index=True)
    ticket_id = Column(UUID(as_uuid=True), ForeignKey("tickets.id", ondelete="CASCADE"), nullable=False)
    topic_id = Column(UUID(as_uuid=True), ForeignKey("ticket_topics.id", ondelete="CASCADE"), nullable=False)
    confidence = Column(Float, nullable=True)  # AI confidence score
    assigned_by = Column(SQLEnum(AssignedBy), default=AssignedBy.AI, nullable=False)
    assigned_at = Column(DateTime, nullable=False)

    # Relationships
    tenant = relationship("Tenant")
    ticket = relationship("Ticket", back_populates="topic_assignments")
    topic = relationship("TicketTopic", back_populates="ticket_assignments")

    def __repr__(self):
        return f"<Assignment ticket={self.ticket_id} topic={self.topic_id} ({self.assigned_by})>"
